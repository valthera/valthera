#!/usr/bin/env python3

"""
WebSocket streaming endpoint for Jarvis smart CV pipeline.

This module provides real-time streaming of analysis results via WebSocket.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ...models.base import AnalysisRequest, AnalysisResult
from ...core.smart_pipeline import SmartCVPipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])

# Global pipeline instance (will be set by main server)
smart_pipeline: Optional[SmartCVPipeline] = None

# WebSocket connection management
active_connections: Set[WebSocket] = set()
connection_subscriptions: Dict[WebSocket, Dict[str, Any]] = {}


def set_pipeline(pipeline: SmartCVPipeline):
    """Set the global pipeline instance"""
    global smart_pipeline
    smart_pipeline = pipeline


class WebSocketManager:
    """Manage WebSocket connections and subscriptions"""
    
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
        self.broadcast_queue = asyncio.Queue()
        self.is_running = False
    
    async def start(self):
        """Start the WebSocket manager"""
        if self.is_running:
            return
        
        self.is_running = True
        # Start background task for broadcasting
        asyncio.create_task(self._broadcast_loop())
        logger.info("[WEBSOCKET_MANAGER] Started")
    
    async def stop(self):
        """Stop the WebSocket manager"""
        self.is_running = False
        # Close all connections
        for websocket in list(self.connections):
            await self.disconnect(websocket)
        logger.info("[WEBSOCKET_MANAGER] Stopped")
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.connections.add(websocket)
        self.subscriptions[websocket] = {
            "classifiers": ["person"],
            "options": {},
            "filters": {},
            "connected_at": time.time()
        }
        logger.info(f"[WEBSOCKET_MANAGER] Client connected. Total: {len(self.connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.connections:
            self.connections.remove(websocket)
        
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        
        logger.info(f"[WEBSOCKET_MANAGER] Client disconnected. Total: {len(self.connections)}")
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                await self._handle_subscribe(websocket, data)
            elif action == "unsubscribe":
                await self._handle_unsubscribe(websocket, data)
            elif action == "ping":
                await websocket.send_text(json.dumps({"action": "pong", "timestamp": time.time()}))
            elif action == "get_latest":
                await self._handle_get_latest(websocket)
            else:
                await websocket.send_text(json.dumps({
                    "error": f"Unknown action: {action}",
                    "timestamp": time.time()
                }))
        
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "error": "Invalid JSON",
                "timestamp": time.time()
            }))
        except Exception as e:
            logger.error(f"[WEBSOCKET_MANAGER] Error handling message: {e}")
            await websocket.send_text(json.dumps({
                "error": str(e),
                "timestamp": time.time()
            }))
    
    async def _handle_subscribe(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle subscription request"""
        if websocket not in self.subscriptions:
            await websocket.send_text(json.dumps({
                "error": "Not connected",
                "timestamp": time.time()
            }))
            return
        
        # Update subscription
        self.subscriptions[websocket].update({
            "classifiers": data.get("classifiers", ["person"]),
            "options": data.get("options", {}),
            "filters": data.get("filters", {}),
            "subscribed_at": time.time()
        })
        
        await websocket.send_text(json.dumps({
            "action": "subscribed",
            "subscription": self.subscriptions[websocket],
            "timestamp": time.time()
        }))
        
        logger.info(f"[WEBSOCKET_MANAGER] Client subscribed to: {self.subscriptions[websocket]['classifiers']}")
    
    async def _handle_unsubscribe(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle unsubscription request"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] = {
                "classifiers": [],
                "options": {},
                "filters": {},
                "unsubscribed_at": time.time()
            }
        
        await websocket.send_text(json.dumps({
            "action": "unsubscribed",
            "timestamp": time.time()
        }))
        
        logger.info("[WEBSOCKET_MANAGER] Client unsubscribed")
    
    async def _handle_get_latest(self, websocket: WebSocket):
        """Handle get latest data request"""
        if not smart_pipeline:
            await websocket.send_text(json.dumps({
                "error": "Pipeline not available",
                "timestamp": time.time()
            }))
            return
        
        try:
            latest_result = smart_pipeline.get_latest_result()
            if latest_result:
                await self._send_result(websocket, latest_result)
            else:
                await websocket.send_text(json.dumps({
                    "message": "No data available",
                    "timestamp": time.time()
                }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "error": f"Failed to get latest data: {str(e)}",
                "timestamp": time.time()
            }))
    
    async def broadcast_result(self, result: AnalysisResult):
        """Broadcast analysis result to all subscribed clients"""
        if not self.connections:
            return
        
        await self.broadcast_queue.put(result)
    
    async def _broadcast_loop(self):
        """Background loop for broadcasting results"""
        while self.is_running:
            try:
                # Wait for result with timeout
                result = await asyncio.wait_for(self.broadcast_queue.get(), timeout=1.0)
                
                # Send to all connected clients
                disconnected = set()
                for websocket in list(self.connections):
                    try:
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await self._send_result(websocket, result)
                        else:
                            disconnected.add(websocket)
                    except Exception as e:
                        logger.error(f"[WEBSOCKET_MANAGER] Error sending to client: {e}")
                        disconnected.add(websocket)
                
                # Remove disconnected clients
                for websocket in disconnected:
                    await self.disconnect(websocket)
                
            except asyncio.TimeoutError:
                # No data available, continue
                continue
            except Exception as e:
                logger.error(f"[WEBSOCKET_MANAGER] Error in broadcast loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_result(self, websocket: WebSocket, result: AnalysisResult):
        """Send analysis result to a specific client"""
        if websocket not in self.subscriptions:
            return
        
        subscription = self.subscriptions[websocket]
        
        # Check if client is subscribed to any classifiers
        if not subscription.get("classifiers"):
            return
        
        # Filter detections based on subscription
        filtered_detections = {}
        for classifier_type, detections in result.detections.items():
            if classifier_type in subscription["classifiers"]:
                filtered_detections[classifier_type] = detections
        
        # Convert to JSON-serializable format
        detections_data = {}
        for classifier_type, detections in filtered_detections.items():
            detections_data[classifier_type] = []
            for detection in detections:
                detection_data = {
                    "bbox": detection.bbox,
                    "confidence": detection.confidence,
                    "class_id": detection.class_id,
                    "class_name": detection.class_name,
                    "classifier_type": detection.classifier_type,
                    "depth_mm": detection.depth_mm,
                    "position_3d": detection.position_3d,
                    "attributes": detection.attributes,
                    "processing_time_ms": detection.processing_time_ms,
                    "model_version": detection.model_version
                }
                detections_data[classifier_type].append(detection_data)
        
        # Create message
        message = {
            "type": "analysis_result",
            "frame_id": result.frame_id,
            "timestamp": result.timestamp,
            "processing_time_ms": result.processing_time_ms,
            "detections": detections_data,
            "frame_resolution": list(result.frame_resolution),
            "pipeline_info": result.pipeline_info,
            "cache_hit": result.cache_hit,
            "detection_count": sum(len(detections) for detections in detections_data.values())
        }
        
        await websocket.send_text(json.dumps(message))


# Global WebSocket manager
ws_manager = WebSocketManager()


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming analysis results"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            try:
                # Wait for client messages
                data = await websocket.receive_text()
                await ws_manager.handle_message(websocket, data)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"[WEBSOCKET] Error in WebSocket loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"[WEBSOCKET] WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


async def start_websocket_manager():
    """Start the WebSocket manager"""
    await ws_manager.start()


async def stop_websocket_manager():
    """Stop the WebSocket manager"""
    await ws_manager.stop()


async def broadcast_analysis_result(result: AnalysisResult):
    """Broadcast analysis result to all WebSocket clients"""
    await ws_manager.broadcast_result(result)


def get_connection_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics"""
    return {
        "total_connections": len(ws_manager.connections),
        "active_subscriptions": len([s for s in ws_manager.subscriptions.values() if s.get("classifiers")]),
        "subscriptions": {
            str(id(ws)): {
                "classifiers": sub.get("classifiers", []),
                "connected_at": sub.get("connected_at", 0),
                "subscribed_at": sub.get("subscribed_at", 0)
            }
            for ws, sub in ws_manager.subscriptions.items()
        }
    }
