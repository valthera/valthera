import React, { useState } from 'react';
import { UnifiedDetection } from '../types/api';

interface DetectionViewProps {
  detections: UnifiedDetection[];
  frameWidth?: number;
  frameHeight?: number;
}

const DetectionView: React.FC<DetectionViewProps> = ({ 
  detections, 
  frameWidth = 640, 
  frameHeight = 480 
}) => {
  const [selectedDetection, setSelectedDetection] = useState<UnifiedDetection | null>(null);

  const getDetectionColor = (classifierType: string) => {
    switch (classifierType) {
      case 'person':
        return 'border-green-400 bg-green-400';
      case 'object':
        return 'border-blue-400 bg-blue-400';
      case 'face':
        return 'border-purple-400 bg-purple-400';
      default:
        return 'border-gray-400 bg-gray-400';
    }
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  const formatPosition3D = (position?: { x: number; y: number; z: number }) => {
    if (!position) return 'N/A';
    return `(${position.x.toFixed(2)}, ${position.y.toFixed(2)}, ${position.z.toFixed(2)})`;
  };

  return (
    <div className="space-y-4">
      {/* Detection Overlay */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden" style={{ width: frameWidth, height: frameHeight }}>
        {detections.map((detection, index) => {
          const [x1, y1, x2, y2] = detection.bbox;
          const width = x2 - x1;
          const height = y2 - y1;
          
          return (
            <div
              key={index}
              className={`absolute border-2 ${getDetectionColor(detection.classifier_type)} bg-opacity-20 cursor-pointer hover:bg-opacity-30 transition-all`}
              style={{
                left: x1,
                top: y1,
                width: width,
                height: height,
              }}
              onClick={() => setSelectedDetection(detection)}
            >
              <div className={`absolute -top-6 left-0 ${getDetectionColor(detection.classifier_type)} text-xs px-2 py-1 rounded`}>
                {detection.class_name}: {formatConfidence(detection.confidence)}
              </div>
            </div>
          );
        })}
        
        {detections.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            No detections
          </div>
        )}
      </div>

      {/* Detection Details */}
      {selectedDetection && (
        <div className="detection-card">
          <h3 className="text-lg font-semibold mb-2">Detection Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Class:</span> {selectedDetection.class_name}
            </div>
            <div>
              <span className="font-medium">Confidence:</span> {formatConfidence(selectedDetection.confidence)}
            </div>
            <div>
              <span className="font-medium">Classifier:</span> {selectedDetection.classifier_type}
            </div>
            <div>
              <span className="font-medium">Depth:</span> {selectedDetection.depth_mm ? `${selectedDetection.depth_mm.toFixed(1)}mm` : 'N/A'}
            </div>
            <div className="col-span-2">
              <span className="font-medium">3D Position:</span> {formatPosition3D(selectedDetection.position_3d)}
            </div>
            {selectedDetection.attributes && Object.keys(selectedDetection.attributes).length > 0 && (
              <div className="col-span-2">
                <span className="font-medium">Attributes:</span>
                <pre className="mt-1 text-xs bg-gray-100 p-2 rounded">
                  {JSON.stringify(selectedDetection.attributes, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Detection Summary */}
      <div className="detection-card">
        <h3 className="text-lg font-semibold mb-2">Detection Summary</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{detections.length}</div>
            <div className="text-gray-600">Total</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {detections.filter(d => d.classifier_type === 'person').length}
            </div>
            <div className="text-gray-600">People</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {detections.filter(d => d.classifier_type === 'object').length}
            </div>
            <div className="text-gray-600">Objects</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetectionView;
