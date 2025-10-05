#!/usr/bin/env python3

import asyncio
import base64
import json
import logging
import os
import sys
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

try:
    import pyrealsense2 as rs  # type: ignore
    REALSENSE_AVAILABLE = True
except Exception as e:
    REALSENSE_AVAILABLE = False
    rs = None  # type: ignore
    print(f"Warning: pyrealsense2 import failed: {e}")

try:
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except Exception as e:
    CV2_AVAILABLE = False
    print(f"Warning: OpenCV import failed: {e}")


# Configuration
API_TOKEN = "valthera-dev-password"
HTTP_PORT = int(os.environ.get("CAMERA_HTTP_PORT", "8000"))
STREAM_W, STREAM_H = 640, 480
FPS = int(os.environ.get("CAMERA_FPS", "20"))  # Configurable FPS, default 20 for Jetson Nano

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/camera_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS for easy local testing from browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


pipeline: Optional["rs.pipeline"] = None  # type: ignore
intrinsics_cache: Optional[dict] = None
depth_scale_m: Optional[float] = None

# Thread pool for image encoding
executor = ThreadPoolExecutor(max_workers=2)


def compress_color_frame(color_np: np.ndarray, quality: int = 80) -> bytes:
    """Compress color frame to JPEG bytes"""
    if not CV2_AVAILABLE:
        # Fallback to raw data if OpenCV not available
        return color_np.tobytes(order="C")
    
    # Convert BGR to RGB for JPEG encoding
    rgb_frame = cv2.cvtColor(color_np, cv2.COLOR_BGR2RGB)
    
    # Encode as JPEG
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, encoded_img = cv2.imencode('.jpg', rgb_frame, encode_params)
    
    if success:
        return encoded_img.tobytes()
    else:
        # Fallback to raw data
        return color_np.tobytes(order="C")


def compress_depth_frame(depth_np: np.ndarray) -> bytes:
    """Compress depth frame - send raw 16-bit data for analysis"""
    # Send raw 16-bit depth data for client-side analysis
    # This allows the client to access actual depth values
    return depth_np.tobytes(order="C")


def start_camera_if_needed() -> tuple[int, int, int]:
    global pipeline, intrinsics_cache, depth_scale_m
    logger.info("Starting camera initialization...")
    
    if pipeline is not None:
        logger.info("Camera pipeline already initialized")
        # Check if pipeline is actually active
        try:
            if pipeline.get_active_profile():
                logger.info("Pipeline is active and ready")
                return STREAM_W, STREAM_H, FPS
            else:
                logger.warning("Pipeline exists but is not active, restarting...")
                pipeline = None
        except Exception as e:
            logger.warning(f"Pipeline state check failed: {e}, restarting...")
            pipeline = None
        
    if not REALSENSE_AVAILABLE:
        logger.error("pyrealsense2 not available in this environment")
        raise RuntimeError("pyrealsense2 not available in this environment")
    
    # Check if OpenCV is available for compression
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available - will use raw data instead of compression")
    else:
        logger.info("OpenCV available - will use JPEG/PNG compression")
    
    # Debug RealSense context
    if rs is None:
        logger.error("RealSense library not available - rs is None")
        raise RuntimeError("RealSense library not available - rs is None")
    
    try:
        ctx = rs.context()  # type: ignore
        devices = ctx.query_devices()
        logger.info(f"RealSense context created, found {len(devices)} devices")
        if len(devices) == 0:
            logger.error("No RealSense devices found!")
            raise RuntimeError("No RealSense devices found")
    except Exception as e:
        logger.error(f"Failed to create RealSense context: {e}")
        raise RuntimeError(f"Failed to create RealSense context: {e}")

    try:
        logger.info("Creating RealSense configuration...")
        
        # Try different configurations in order of preference
        # Based on your D435I capabilities: 640x480 @ 30fps is supported for depth
        configs_to_try = [
            # Try highest FPS first - your camera supports 640x480 @ 30fps
            (640, 480, 30),  # Your camera supports this!
            (640, 480, 25),
            (640, 480, 20),
            (640, 480, 15),
            # Try different resolutions with high FPS that your camera supports
            (480, 270, 60),  # Your camera supports this!
            (480, 270, 30),
            (480, 270, 15),
            (640, 360, 30),  # Your camera supports this!
            (640, 360, 15),
            # Fallback options
            (640, 480, 12),
            (640, 480, 10),
            (640, 480, 8),
            (640, 480, 6),
            (480, 270, 12),
            (480, 270, 10),
            (480, 270, 8),
            (480, 270, 6),
            # Last resort - very low FPS
            (640, 480, 5),
            (480, 270, 5),
        ]
        
        profile = None
        working_config = None
        for i, (width, height, fps) in enumerate(configs_to_try):
            try:
                logger.info(f"🔍 Attempt {i+1}/{len(configs_to_try)}: Trying {width}x{height} @ {fps}fps")
                
                # Create new config and pipeline for each attempt
                cfg = rs.config()  # type: ignore
                if cfg is None:
                    logger.error("Failed to create RealSense config object")
                    continue
                
                # Try to enable both color and depth streams
                try:
                    cfg.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
                    logger.info(f"✅ Color stream enabled: {width}x{height} @ {fps}fps")
                except Exception as e:
                    logger.warning(f"⚠️  Color stream failed: {e}")
                
                # Always try to enable depth stream
                cfg.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
                logger.info(f"✅ Depth stream enabled: {width}x{height} @ {fps}fps")
                
                logger.info("Creating pipeline...")
                # Create fresh pipeline for this attempt
                if pipeline:
                    try:
                        pipeline.stop()
                    except:
                        pass
                pipeline = rs.pipeline()  # type: ignore
                if pipeline is None:
                    logger.error("Failed to create RealSense pipeline object")
                    continue
                
                logger.info("Starting pipeline...")
                profile = pipeline.start(cfg)
                logger.info(f"✅ SUCCESS! Pipeline started with {width}x{height} @ {fps}fps")
                logger.info(f"🎯 USING CONFIGURATION: {width}x{height} @ {fps}fps")
                
                working_config = (width, height, fps)
                break
                
            except Exception as e:
                logger.warning(f"❌ Configuration {width}x{height} @ {fps}fps failed: {e}")
                if pipeline:
                    try:
                        pipeline.stop()
                    except:
                        pass
                pipeline = None
                continue
        
        if profile is None or working_config is None:
            raise RuntimeError("No compatible RealSense configuration found")
        
        # Log the final working configuration prominently
        logger.info(f"🎯 FINAL CONFIGURATION: {working_config[0]}x{working_config[1]} @ {working_config[2]}fps")
        if working_config[2] < 10:
            logger.warning(f"⚠️  WARNING: Using very low FPS ({working_config[2]}fps) - this will cause slow/stuttering video!")
            logger.warning(f"⚠️  This suggests your RealSense camera may not support higher frame rates at this resolution.")
            logger.warning(f"⚠️  Try visiting /stream-configs to see what your camera actually supports.")
        elif working_config[2] >= 30:
            logger.info(f"✅ EXCELLENT! Using high FPS ({working_config[2]}fps) - should provide smooth video!")
        elif working_config[2] >= 20:
            logger.info(f"✅ GOOD! Using decent FPS ({working_config[2]}fps) - should provide smooth video!")
        else:
            logger.info(f"⚠️  Using moderate FPS ({working_config[2]}fps) - may be slightly choppy but should work.")
        
        # Verify the pipeline is actually running
        try:
            active_profile = pipeline.get_active_profile()
            if not active_profile:
                raise RuntimeError("Pipeline started but is not active")
            logger.info("Pipeline is active and ready for frame capture")
        except Exception as e:
            logger.error(f"Pipeline verification failed: {e}")
            raise RuntimeError(f"Pipeline verification failed: {e}")

        logger.info("Getting depth sensor...")
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale_m = float(depth_sensor.get_depth_scale())
        logger.info(f"Depth scale: {depth_scale_m}")

        depth_stream = profile.get_stream(rs.stream.depth)
        color_stream = profile.get_stream(rs.stream.color)
        
        logger.info("Getting camera intrinsics...")
        intr = depth_stream.as_video_stream_profile().get_intrinsics()
        intrinsics_cache = {
            "width": int(intr.width),
            "height": int(intr.height),
            "fx": float(intr.fx),
            "fy": float(intr.fy),
            "cx": float(intr.ppx),
            "cy": float(intr.ppy),
            "depth_scale_m": depth_scale_m,
        }
        logger.info(f"Camera intrinsics cached: {intrinsics_cache}")
        logger.info("Camera initialization completed successfully")
        
        return working_config
        
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}", exc_info=True)
        # Reset pipeline on failure
        pipeline = None
        raise


@app.on_event("startup")
def on_startup() -> None:
    # Do not auto-start camera on startup to avoid blocking when no device is present.
    # Camera will be started lazily on first intrinsics request or websocket connect.
    logger.info("FastAPI application started - camera will be initialized on demand")
    return None


@app.get("/health")
def health() -> JSONResponse:
    logger.info("Health check requested")
    status = {
        "realsense_available": REALSENSE_AVAILABLE,
        "camera_started": pipeline is not None,
        "intrinsics_ready": intrinsics_cache is not None,
        "streams": {
            "depth": "z16_le",
            "left_rgb": "bgr8", 
            "right_rgb": "bgr8"
        } if pipeline is not None else None
    }
    logger.info(f"Health status: {status}")
    return JSONResponse(status)


@app.get("/v1/intrinsics")
def get_intrinsics(authorization: str = Header(default="")):
    logger.info("Intrinsics request received")
    if authorization != f"Bearer {API_TOKEN}":
        logger.warning(f"Unauthorized intrinsics request with auth: {authorization[:10]}...")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info("Authorization successful, checking intrinsics cache")
    if intrinsics_cache is None:
        logger.info("Intrinsics cache empty, starting camera on-demand")
        # Try starting camera on-demand
        start_camera_if_needed()
    
    if intrinsics_cache is None:
        logger.error("Camera not ready after initialization attempt")
        raise HTTPException(status_code=503, detail="Camera not ready")
    
    logger.info("Returning intrinsics data")
    return intrinsics_cache


@app.websocket("/v1/ws/depth")
async def ws_depth(ws: WebSocket):
    client_ip = ws.client.host if ws.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_ip}")
    
    # Check authorization
    auth_header = ws.headers.get("authorization", "")
    token_param = ws.query_params.get("token", "")
    token_ok = (
        auth_header == f"Bearer {API_TOKEN}" or
        token_param == API_TOKEN
    )
    
    logger.info(f"Auth check - Header: {auth_header[:20]}..., Token param: {token_param[:10]}..., Valid: {token_ok}")
    
    if not token_ok:
        logger.warning(f"WebSocket connection rejected - invalid token from {client_ip}")
        await ws.close(code=4401)
        return

    logger.info(f"WebSocket connection accepted from {client_ip}")
    await ws.accept()
    
    try:
        logger.info("Starting camera for WebSocket stream...")
        start_camera_if_needed()
        logger.info("Camera started successfully for WebSocket")
    except RuntimeError as e:
        error_msg = str(e)
        if "No device connected" in error_msg:
            logger.error("No RealSense camera device connected")
            await ws.close(code=1011, reason="No camera device connected")
        else:
            logger.error(f"Camera initialization failed: {error_msg}")
            await ws.close(code=1011, reason=f"Camera error: {error_msg}")
        return
    except Exception as e:
        logger.error(f"Unexpected error starting camera for WebSocket: {e}", exc_info=True)
        await ws.close(code=1011, reason="Unexpected camera error")
        return

    try:
        assert pipeline is not None
        logger.info("Starting frame streaming loop...")
        frame_count = 0
        
        # Give the pipeline a moment to stabilize before first frame
        logger.info("Waiting for pipeline to stabilize...")
        await asyncio.sleep(0.5)
        
        # Calculate target frame interval for smooth streaming
        target_fps = FPS
        frame_interval = 1.0 / target_fps
        last_frame_time = 0
        
        while True:
            try:
                # Add timeout to prevent hanging
                frames = pipeline.wait_for_frames(timeout_ms=5000)  # type: ignore
                frame_count += 1
                
                # Log frame rate periodically
                if frame_count % 30 == 0:  # Log every 30 frames
                    current_time = time.time()
                    if last_frame_time > 0:
                        actual_fps = 30 / (current_time - last_frame_time)
                        logger.info(f"📊 SERVER: Frame #{frame_count}, actual FPS: {actual_fps:.1f} (target: {target_fps})")
                        if actual_fps < 5:
                            logger.warning(f"⚠️  VERY LOW SERVER FPS: {actual_fps:.1f} - Camera may be using low FPS configuration!")
                        elif actual_fps >= 20:
                            logger.info(f"✅ SERVER: Good frame rate! {actual_fps:.1f} FPS")
                    last_frame_time = current_time
                
                # Get all three frames
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                
                # Check if we have the required frames
                if not depth_frame:
                    logger.warning(f"Missing depth frame at frame #{frame_count}")
                    await asyncio.sleep(0)
                    continue
                
                if not color_frame:
                    logger.warning(f"Missing color frame at frame #{frame_count} - using depth-only mode")
                    # In depth-only mode, we'll send depth data for both streams
                    # but the client will handle rendering appropriately
                    color_frame = None
                
                # Convert frames to numpy arrays
                if color_frame is not None:
                    color_np = np.asanyarray(color_frame.get_data())  # BGR8 format
                else:
                    # In depth-only mode, use depth data for color stream too
                    color_np = np.asanyarray(depth_frame.get_data()).astype(np.uint8)  # Convert depth to 8-bit
                
                depth_np = np.asanyarray(depth_frame.get_data()).astype(np.uint16)  # Z16 format
                
                # Debug: Log frame info
                if frame_count % 30 == 0:  # Log every 30 frames
                    logger.info(f"Frame #{frame_count} - Color: {color_np.shape}, Depth: {depth_np.shape}")
                    logger.info(f"Color data range: {color_np.min()}-{color_np.max()}, Depth data range: {depth_np.min()}-{depth_np.max()}")
                    logger.info(f"Color dtype: {color_np.dtype}, Depth dtype: {depth_np.dtype}")
                    logger.info(f"Color bytes per pixel: {color_np.nbytes // (color_np.shape[0] * color_np.shape[1])}")
                
                # Create comprehensive header with all stream info
                header = {
                    "type": "frame",
                    "timestamp": float(depth_frame.get_timestamp()),
                    "depth_only_mode": color_frame is None,
                    "compressed": True,  # Indicate compressed data
                    "depth": {
                        "width": int(depth_np.shape[1]),
                        "height": int(depth_np.shape[0]),
                        "format": "png" if CV2_AVAILABLE else "z16_le",
                        "scale_m": depth_scale_m if depth_scale_m is not None else 0.001
                    },
                    "left_rgb": {
                        "width": int(color_np.shape[1]),
                        "height": int(color_np.shape[0]),
                        "format": "jpeg" if CV2_AVAILABLE else ("bgr8" if color_frame is not None else "depth8")
                    },
                    "right_rgb": {
                        "width": int(color_np.shape[1]),
                        "height": int(color_np.shape[0]),
                        "format": "jpeg" if CV2_AVAILABLE else ("bgr8" if color_frame is not None else "depth8")
                    }
                }
                
                # Check if WebSocket is still open before sending
                try:
                    # Send header first
                    await ws.send_text(json.dumps(header))
                    
                    # Compress frames asynchronously to avoid blocking
                    loop = asyncio.get_running_loop()
                    
                    # Compress color frame (JPEG)
                    color_bytes = await loop.run_in_executor(
                        executor, compress_color_frame, color_np, 85
                    )
                    
                    # Compress depth frame (PNG)
                    depth_bytes = await loop.run_in_executor(
                        executor, compress_depth_frame, depth_np
                    )
                    
                    if frame_count % 30 == 0:  # Log every 30 frames
                        logger.info(f"📤 SENDING: Frame #{frame_count} - Color: {len(color_bytes)} bytes, Depth: {len(depth_bytes)} bytes")
                        logger.info(f"📤 SENDING: Compression ratio - Color: {len(color_bytes)/(color_np.shape[0]*color_np.shape[1]*3):.2%}, Depth: {len(depth_bytes)/(depth_np.shape[0]*depth_np.shape[1]*2):.2%}")
                    
                    # Send compressed data
                    await ws.send_bytes(color_bytes)  # Left RGB (same as right for now)
                    await ws.send_bytes(color_bytes)  # Right RGB (same as left for now)
                    await ws.send_bytes(depth_bytes)  # Depth
                except Exception as e:
                    logger.warning(f"WebSocket connection closed or error at frame #{frame_count}: {e}")
                    break
                
                # Let the camera control the frame rate naturally
                # Remove artificial limiting to allow maximum FPS
                await asyncio.sleep(0)  # Just yield control, don't limit frame rate
                
            except Exception as e:
                logger.error(f"Error processing frame #{frame_count}: {e}", exc_info=True)
                # Continue trying to process frames
                await asyncio.sleep(0.1)
                
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected from {client_ip} after {frame_count} frames - code: {e.code}, reason: {e.reason}")
        return
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket stream from {client_ip}: {e}", exc_info=True)
        try:
            await ws.close(code=1011)
        except:
            pass
        return


VIEWER_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Valthera Depth Viewer</title>
    <style>
      body { font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\"; margin: 0; padding: 0; background: #0b0d12; color: #e5e7eb; }
      header { padding: 12px 16px; background: #111827; border-bottom: 1px solid #1f2937; display:flex; justify-content:space-between; align-items:center }
      .muted { color: #9ca3af; font-size: 12px }
      main { padding: 16px; display:flex; gap:16px; flex-wrap: wrap; }
      canvas { background: #000; image-rendering: pixelated; border: 1px solid #1f2937 }
      .panel { padding: 12px; background: #111827; border: 1px solid #1f2937; border-radius: 8px; }
      input { background:#0b0d12; color:#e5e7eb; border:1px solid #374151; border-radius:6px; padding:6px 8px }
      button { background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 10px; cursor:pointer }
      .view-btn { background:#374151; color:#e5e7eb; border:1px solid #4b5563; }
      .view-btn.active { background:#2563eb; color:white; border:1px solid #3b82f6; }
    </style>
  </head>
  <body>
    <header>
      <div>
        <strong>Valthera Depth Viewer</strong>
        <div class=\"muted\">WebSocket depth stream</div>
      </div>
      <div class=\"muted\" id=\"status\">disconnected</div>
    </header>
    <main>
      <div class=\"panel\">
        <div style=\"display:flex; gap:8px; align-items:center; flex-wrap:wrap\">
          <label>Token</label>
          <input id=\"token\" value=\"valthera-dev-password\" style=\"min-width:240px\" />
          <button id=\"connect\">Connect</button>
        </div>
        <div style=\"display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:8px\">
          <label>View:</label>
          <button id=\"viewColor\" class=\"view-btn active\">Color</button>
          <button id=\"viewDepth\" class=\"view-btn\">Depth</button>
        </div>
      </div>
      <div class=\"panel\">
        <canvas id=\"c\" width=640 height=480></canvas>
        <div id=\"depthLegend\" style=\"display:none; margin-top:8px; font-size:12px; color:#9ca3af\">
          <div>Depth Legend: <span style=\"color:#00f\">Blue</span> (close) → <span style=\"color:#0f0\">Green</span> → <span style=\"color:#ff0\">Yellow</span> → <span style=\"color:#f00\">Red</span> (far)</div>
        </div>
      </div>
    </main>
    <script>
      const statusEl = document.getElementById('status');
      const canvas = document.getElementById('c');
      const ctx = canvas.getContext('2d');
      const tokenInput = document.getElementById('token');
      const connectBtn = document.getElementById('connect');
      const viewColorBtn = document.getElementById('viewColor');
      const viewDepthBtn = document.getElementById('viewDepth');
      const depthLegend = document.getElementById('depthLegend');

      let expectingBinary = false;
      let header = null;
      let ws = null;
      let binaryDataCount = 0;
      let currentView = 'color'; // 'color' or 'depth'
      let frameCount = 0;
      let lastFrameTime = 0;
      let lastRenderTime = 0;
      let renderFPS = 0;
      let framesDropped = 0;

      function setStatus(text) { statusEl.textContent = text; }

      function renderColor(buffer, width, height, format = 'bgr8') {
        if (format === 'jpeg') {
          // Use ImageBitmap for synchronous JPEG rendering to prevent black frames
          const blob = new Blob([buffer], { type: 'image/jpeg' });
          createImageBitmap(blob).then(bitmap => {
            // Clear canvas first to prevent black frames
            ctx.clearRect(0, 0, width, height);
            ctx.drawImage(bitmap, 0, 0, width, height);
            bitmap.close();
          }).catch(err => {
            console.error('JPEG rendering failed:', err);
            // Fallback to raw data
            renderColorRaw(buffer, width, height);
          });
        } else {
          console.log('🖼️  Using raw BGR8 rendering path');
          // Handle raw BGR8 data - no requestAnimationFrame to avoid flickering
          const bgr = new Uint8Array(buffer);
          const expectedSize = width * height * 3; // BGR8 = 3 bytes per pixel
          
          if (bgr.length !== expectedSize) {
            console.error(`Buffer size mismatch! Expected ${expectedSize}, got ${bgr.length}`);
            return;
          }
          
          const img = ctx.createImageData(width, height);
          for (let i = 0, j = 0; i < bgr.length; i += 3, j += 4) {
            img.data[j] = bgr[i + 2];     // R (BGR -> RGB)
            img.data[j+1] = bgr[i + 1];   // G
            img.data[j+2] = bgr[i];       // B
            img.data[j+3] = 255;          // A
          }
          ctx.putImageData(img, 0, 0);
        }
      }

      function renderDepth(buffer, width, height, format = 'z16_le') {
        if (format === 'png') {
          // Use ImageBitmap for synchronous PNG rendering to prevent black frames
          const blob = new Blob([buffer], { type: 'image/png' });
          createImageBitmap(blob).then(bitmap => {
            // Clear canvas first to prevent black frames
            ctx.clearRect(0, 0, width, height);
            ctx.drawImage(bitmap, 0, 0, width, height);
            bitmap.close();
          }).catch(err => {
            console.error('PNG rendering failed:', err);
            // Fallback to raw data
            renderDepthRaw(buffer, width, height);
          });
        } else {
          // Handle raw depth data - no requestAnimationFrame to avoid flickering
          const depth = new Uint16Array(buffer);
          const img = ctx.createImageData(width, height);
        
        // Enhanced depth visualization for room-scale distances (matching client)
        const maxDepth = 4000; // 4 meters in mm (covers 10ft+ room)
        const minDepth = 50;   // 5cm minimum depth (very close range)
        
        let minVal = 65535;
        let maxVal = 0;
        
        // Find actual min/max values for better contrast
        for (let i = 0; i < depth.length; i++) {
          if (depth[i] > 0 && depth[i] < 65535) {
            minVal = Math.min(minVal, depth[i]);
            maxVal = Math.max(maxVal, depth[i]);
          }
        }
        
        // Use actual range with aggressive contrast enhancement
        let actualMin = Math.max(minDepth, minVal);
        let actualMax = Math.min(maxDepth, maxVal);
        
        // Force a reasonable range for better contrast
        let range = actualMax - actualMin;
        if (range < 2000) {
          // If range is too small, force a wider range for better visibility
          const mid = (actualMin + actualMax) / 2;
          actualMin = Math.max(50, mid - 1500);
          actualMax = Math.min(4000, mid + 1500);
          range = actualMax - actualMin;
          console.log(`Forced depth range for better contrast: ${actualMin}mm - ${actualMax}mm`);
        }
        
        // Additional contrast boost - use only the middle 80% of the range for better visibility
        const contrastBoost = 0.2; // Use 20% padding on each end
        const adjustedMin = actualMin + (range * contrastBoost);
        const adjustedMax = actualMax - (range * contrastBoost);
        const adjustedRange = adjustedMax - adjustedMin;
        
        console.log(`🔄 Final depth range: ${adjustedMin}mm - ${adjustedMax}mm (${Math.round(adjustedMin/10)}cm - ${Math.round(adjustedMax/10)}cm)`);
        
        for (let i = 0, j = 0; i < depth.length; i++, j += 4) {
          const v16 = depth[i];
          
          if (v16 === 0 || v16 >= 65535) {
            // Invalid depth - show as black
            img.data[j] = 0;
            img.data[j+1] = 0;
            img.data[j+2] = 0;
            img.data[j+3] = 255;
          } else {
            // Map depth to grayscale: closer = white, farther = black
            // Closer objects have smaller depth values, farther objects have larger depth values
            const normalized = Math.max(0, Math.min(1, (v16 - adjustedMin) / adjustedRange));
            
            // Apply strong contrast curve for better visibility
            const gamma = 0.4; // Lower gamma = much brighter mid-tones
            const contrastNormalized = Math.pow(normalized, gamma);
            
            // INVERT: closer objects (small depth values) should be white (high grayscale)
            // farther objects (large depth values) should be black (low grayscale)
            const grayscale = Math.floor((1 - contrastNormalized) * 255);
            
            // Apply additional contrast boost
            const boostedGrayscale = Math.min(255, Math.max(0, grayscale * 1.5));
            
            // Set all RGB channels to the same grayscale value
            img.data[j] = boostedGrayscale;     // R
            img.data[j+1] = boostedGrayscale;   // G
            img.data[j+2] = boostedGrayscale;   // B
            img.data[j+3] = 255;                // A
          }
        }
        
          ctx.putImageData(img, 0, 0);
          
          // Log depth info occasionally
          if (frameCount % 60 === 0) {
            console.log(`🔄 Depth range: ${actualMin}mm - ${actualMax}mm (${Math.round(actualMin/10)}cm - ${Math.round(actualMax/10)}cm)`);
          }
        }
      }

      function renderDepthAsGrayscale(buffer, width, height) {
        // No requestAnimationFrame to avoid flickering
        const depth = new Uint16Array(buffer);
        const img = ctx.createImageData(width, height);
        
        // Simple grayscale depth visualization
        const maxDepth = 5000; // 5 meters in mm
        const minDepth = 200;  // 20cm minimum depth
        
        let minVal = 65535;
        let maxVal = 0;
        
        // Find actual min/max values for better contrast
        for (let i = 0; i < depth.length; i++) {
          if (depth[i] > 0 && depth[i] < 65535) {
            minVal = Math.min(minVal, depth[i]);
            maxVal = Math.max(maxVal, depth[i]);
          }
        }
        
        // Use actual range or fallback to reasonable values
        const actualMin = Math.max(minDepth, minVal);
        const actualMax = Math.min(maxDepth, maxVal);
        const range = actualMax - actualMin;
        
        for (let i = 0, j = 0; i < depth.length; i++, j += 4) {
          const v16 = depth[i];
          
          if (v16 === 0 || v16 >= 65535) {
            // Invalid depth - show as black
            img.data[j] = 0;
            img.data[j+1] = 0;
            img.data[j+2] = 0;
            img.data[j+3] = 255;
          } else {
            // Map depth to grayscale
            const normalized = Math.max(0, Math.min(1, (v16 - actualMin) / range));
            const intensity = Math.floor(normalized * 255);
            
            // Grayscale: white (close) -> black (far)
            img.data[j] = 255 - intensity;     // R
            img.data[j+1] = 255 - intensity;   // G
            img.data[j+2] = 255 - intensity;   // B
            img.data[j+3] = 255;               // A
          }
        }
        
        ctx.putImageData(img, 0, 0);
      }

      function connect() {
        if (ws) { try { ws.close(); } catch(e){} }
        const token = tokenInput.value.trim();
        const url = `ws://${location.host}/v1/ws/depth?token=${encodeURIComponent(token)}`;
        ws = new WebSocket(url);
        ws.binaryType = 'arraybuffer';
        ws.onopen = () => setStatus('connected');
        ws.onclose = () => setStatus('disconnected');
        ws.onerror = () => setStatus('error');
        ws.onmessage = (ev) => {
          if (typeof ev.data === 'string') {
            header = JSON.parse(ev.data);
            console.log('📥 Received header:', header);
            expectingBinary = true;
            binaryDataCount = 0;
            // Use color dimensions from the header
            canvas.width = header.left_rgb.width;
            canvas.height = header.left_rgb.height;
            console.log(`🖼️  Canvas resized to: ${canvas.width}x${canvas.height}`);
          } else if (expectingBinary) {
            binaryDataCount++;
            console.log(`Received binary data #${binaryDataCount}, size: ${ev.data.byteLength}`);
            
            // Server sends: left RGB, right RGB, depth (in that order)
            if (binaryDataCount === 1) {
              // Render color image (left RGB) or depth if in depth-only mode
              frameCount++;
              const now = performance.now();
              if (lastFrameTime > 0) {
                const fps = 1000 / (now - lastFrameTime);
                if (frameCount % 30 === 0) {
                  console.log(`🖥️  CLIENT: Frame #${frameCount}, FPS: ${fps.toFixed(1)}, Dropped: ${framesDropped}`);
                  if (fps < 10) {
                    console.warn(`⚠️  CLIENT: Very low FPS detected: ${fps.toFixed(1)} - Check server logs!`);
                  } else if (fps >= 20) {
                    console.log(`✅ CLIENT: Good frame rate! ${fps.toFixed(1)} FPS`);
                  }
                }
              }
              lastFrameTime = now;
              
              // Check if we're in depth-only mode
              if (header.depth_only_mode) {
                if (frameCount % 30 === 0) {
                  console.log(`🔍 Depth-only mode: currentView=${currentView}, rendering depth data`);
                }
                // In depth-only mode, render based on current view
                if (currentView === 'depth') {
                  renderDepth(ev.data, header.depth.width, header.depth.height, header.depth.format);
                } else {
                  // Color view in depth-only mode - render depth as grayscale
                  renderDepthAsGrayscale(ev.data, header.depth.width, header.depth.height);
                }
              } else {
                if (frameCount % 30 === 0) {
                  console.log(`🔍 Normal mode: currentView=${currentView}, rendering color data`);
                }
                // Normal mode - render based on current view
                if (currentView === 'color') {
                  console.log(`🎨 Rendering color: format=${header.left_rgb.format}, compressed=${header.compressed}`);
                  renderColor(ev.data, header.left_rgb.width, header.left_rgb.height, header.left_rgb.format);
                } else {
                  // In depth view but not depth-only mode, we'll get depth data in the 3rd message
                  // For now, show a placeholder or wait for depth data
                  if (frameCount % 30 === 0) {
                    console.log('⏳ Waiting for depth data in normal mode...');
                  }
                }
              }
            } else if (binaryDataCount === 3) {
              // Optionally render depth data (3rd binary message) - only in normal mode
              if (frameCount % 30 === 0) {
                console.log(`🔍 Processing depth data: currentView=${currentView}, depth_only_mode=${header.depth_only_mode}`);
              }
              if (currentView === 'depth' && !header.depth_only_mode) {
                if (frameCount % 30 === 0) {
                  console.log('📏 Rendering depth data in normal mode');
                }
                renderDepth(ev.data, header.depth.width, header.depth.height, header.depth.format);
              } else {
                if (frameCount % 30 === 0) {
                  console.log('⏭️  Skipping depth data - not in depth view or in depth-only mode');
                }
              }
              expectingBinary = false;
              binaryDataCount = 0;
            }
          }
        };
      }

      connectBtn.addEventListener('click', connect);
      
      viewColorBtn.addEventListener('click', () => {
        currentView = 'color';
        viewColorBtn.classList.add('active');
        viewDepthBtn.classList.remove('active');
        depthLegend.style.display = 'none';
        console.log('🖼️  Switched to Color view');
        
        // In depth-only mode, show a message
        if (header && header.depth_only_mode) {
          console.log('ℹ️  Note: Camera is in depth-only mode - Color view will show depth data');
        }
      });
      
      viewDepthBtn.addEventListener('click', () => {
        currentView = 'depth';
        viewDepthBtn.classList.add('active');
        viewColorBtn.classList.remove('active');
        depthLegend.style.display = 'block';
        console.log('📏 Switched to Depth view');
        
        // In depth-only mode, show a message
        if (header && header.depth_only_mode) {
          console.log('ℹ️  Note: Camera is in depth-only mode - Depth view will show enhanced depth visualization');
        }
      });
    </script>
  </body>
</html>
"""


@app.get("/viewer")
def viewer() -> HTMLResponse:
    return HTMLResponse(content=VIEWER_HTML)


@app.get("/logs")
def get_logs() -> JSONResponse:
    """Get recent log entries for debugging"""
    try:
        with open('/tmp/camera_server.log', 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            return JSONResponse({
                "log_entries": recent_lines,
                "total_lines": len(lines),
                "showing_last": len(recent_lines)
            })
    except FileNotFoundError:
        return JSONResponse({"error": "Log file not found", "log_entries": []})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return JSONResponse({"error": str(e), "log_entries": []})


@app.get("/devices")
def get_devices() -> JSONResponse:
    """Check for available RealSense devices"""
    if not REALSENSE_AVAILABLE:
        return JSONResponse({
            "error": "RealSense SDK not available",
            "devices": [],
            "count": 0
        })
    
    try:
        ctx = rs.context()  # type: ignore
        devices = ctx.query_devices()
        device_list = []
        
        for i, device in enumerate(devices):
            device_info = {
                "index": i,
                "name": device.get_info(rs.camera_info.name) if hasattr(rs, 'camera_info') else f"Device {i}",
                "serial": device.get_info(rs.camera_info.serial_number) if hasattr(rs, 'camera_info') else "Unknown",
                "firmware": device.get_info(rs.camera_info.firmware_version) if hasattr(rs, 'camera_info') else "Unknown"
            }
            device_list.append(device_info)
        
        return JSONResponse({
            "devices": device_list,
            "count": len(device_list),
            "realsense_available": True
        })
        
    except Exception as e:
        logger.error(f"Error detecting devices: {e}")
        return JSONResponse({
            "error": str(e),
            "devices": [],
            "count": 0,
            "realsense_available": True
        })


@app.get("/stream-configs")
def get_stream_configs() -> JSONResponse:
    """Get available RealSense stream configurations"""
    if not REALSENSE_AVAILABLE:
        return JSONResponse({
            "error": "RealSense SDK not available",
            "configs": []
        })
    
    try:
        ctx = rs.context()  # type: ignore
        devices = ctx.query_devices()
        
        if not devices:
            return JSONResponse({
                "error": "No RealSense devices found",
                "configs": []
            })
        
        device = devices[0]
        
        # Get device info
        device_info = {}
        try:
            device_info = {
                "name": device.get_info(rs.camera_info.name) if hasattr(rs, 'camera_info') else "Unknown",
                "serial": device.get_info(rs.camera_info.serial_number) if hasattr(rs, 'camera_info') else "Unknown",
                "firmware": device.get_info(rs.camera_info.firmware_version) if hasattr(rs, 'camera_info') else "Unknown",
                "usb_type": device.get_info(rs.camera_info.usb_type_descriptor) if hasattr(rs, 'camera_info') else "Unknown"
            }
        except:
            pass
        
        # Get color stream profiles
        color_profiles = []
        for profile in device.sensors[0].get_stream_profiles():
            if profile.stream_type() == rs.stream.color:
                color_profiles.append({
                    "width": profile.as_video_stream_profile().width(),
                    "height": profile.as_video_stream_profile().height(),
                    "fps": profile.as_video_stream_profile().fps(),
                    "format": str(profile.format())
                })
        
        # Get depth stream profiles
        depth_profiles = []
        for profile in device.sensors[0].get_stream_profiles():
            if profile.stream_type() == rs.stream.depth:
                depth_profiles.append({
                    "width": profile.as_video_stream_profile().width(),
                    "height": profile.as_video_stream_profile().height(),
                    "fps": profile.as_video_stream_profile().fps(),
                    "format": str(profile.format())
                })
        
        # Sort by FPS descending to see highest rates first
        color_profiles.sort(key=lambda x: x['fps'], reverse=True)
        depth_profiles.sort(key=lambda x: x['fps'], reverse=True)
        
        # Find the highest FPS for 640x480 (check both color and depth streams)
        max_640x480_fps = 0
        for profile in color_profiles + depth_profiles:
            if profile['width'] == 640 and profile['height'] == 480:
                max_640x480_fps = max(max_640x480_fps, profile['fps'])
        
        return JSONResponse({
            "device_info": device_info,
            "color_streams": color_profiles,
            "depth_streams": depth_profiles,
            "max_640x480_fps": max_640x480_fps,
            "current_config": {
                "width": STREAM_W,
                "height": STREAM_H,
                "fps": FPS
            },
            "jetson_optimization": {
                "recommended_fps": min(30, max_640x480_fps) if max_640x480_fps > 0 else 15,
                "note": "Jetson Nano may have USB bandwidth limitations"
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stream configs: {e}")
        return JSONResponse({
            "error": str(e),
            "configs": []
        })


def main() -> None:
    # Optional local run: uvicorn camera.server:app --host 0.0.0.0 --port 8000
    import uvicorn  # type: ignore
    logger.info(f"Starting camera server on port {HTTP_PORT}")
    logger.info(f"RealSense available: {REALSENSE_AVAILABLE}")
    uvicorn.run("camera.server:app", host="0.0.0.0", port=HTTP_PORT, reload=False)


if __name__ == "__main__":
    main()

