// API types matching the Python models
export interface UnifiedDetection {
  bbox: number[];
  confidence: number;
  class_id: number;
  class_name: string;
  classifier_type: string;
  depth_mm?: number;
  position_3d?: {
    x: number;
    y: number;
    z: number;
  };
  attributes?: Record<string, any>;
  processing_time_ms?: number;
  model_version?: string;
}

export interface AnalysisRequest {
  classifiers: string[];
  options: {
    confidence_threshold?: number;
    include_depth?: boolean;
    include_3d_position?: boolean;
    include_annotated_frame?: boolean;
    max_detections?: number;
  };
  filters?: {
    min_confidence?: number;
    max_distance_mm?: number;
    classes?: string[];
  };
  frame_id?: number;
  client_id?: string;
}

export interface AnalysisResult {
  frame_id: number;
  timestamp: number;
  processing_time_ms: number;
  detections: Record<string, UnifiedDetection[]>;
  frame_resolution: number[];
  pipeline_info: Record<string, any>;
  cache_hit: boolean;
  detection_count: number;
}

export interface PipelineStatus {
  status: string;
  timestamp: number;
  pipeline_info: {
    is_running: boolean;
    config: {
      fps: number;
      confidence_threshold: number;
      max_detections: number;
      enabled_classifiers: string[];
      include_depth: boolean;
      include_3d_position: boolean;
    };
    frame_count: number;
    depth_camera_available: boolean;
    registry_stats: Record<string, any>;
    processing_stats: Record<string, any>;
    cache_stats: Record<string, any>;
  };
}

export interface ClassifierInfo {
  name: string;
  type: string;
  enabled: boolean;
  initialized: boolean;
  stats: {
    name: string;
    is_enabled: boolean;
    is_initialized: boolean;
    total_detections: number;
    last_detection_time: number;
    average_processing_time_ms: number;
    model_version?: string;
    config: {
      model_type: string;
      confidence_threshold: number;
      classes?: number[];
    };
  };
}

export interface WebSocketMessage {
  type: string;
  frame_id?: number;
  timestamp?: number;
  processing_time_ms?: number;
  detections?: Record<string, UnifiedDetection[]>;
  frame_resolution?: number[];
  pipeline_info?: Record<string, any>;
  cache_hit?: boolean;
  detection_count?: number;
  action?: string;
  subscription?: Record<string, any>;
  error?: string;
  message?: string;
}
