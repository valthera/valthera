// Project types
export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'training' | 'completed';
  createdAt: string;
  updatedAt: string;
  videoCount: number;
  hasDroidDataset: boolean;
  linkedDataSources: string[];
  metadata: {
    lastTrainingAt?: string;
    totalBehaviors: number;
    totalEndpoints: number;
  };
}

// Behavior types
export interface Behavior {
  id: string;
  projectId: string;
  name: string;
  sampleCount: number;
  uploadedAt: string;
  updatedAt: string;
  linkedVideos: string[];
  trainingResults: {
    accuracy?: number;
    modelPath?: string;
    trainingJobId?: string;
    lastTrainedAt?: string;
  };
  apiEndpoints: APIEndpoint[];
}

// Data Source types
export interface DataSource {
  id: string;
  name: string;
  description?: string;
  folderPath: string;
  videoCount: number;
  totalSize: number;
  createdAt: string;
  updatedAt: string;
  files: VideoFile[];
}

// Training Job types
export interface TrainingJob {
  id: string;
  projectId: string;
  status: 'preprocessing' | 'training' | 'validating' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  logs: string[];
  config: {
    modelType: string;
    hyperparameters: object;
    dataSources: string[];
  };
}

// API Endpoint types
export interface APIEndpoint {
  id: string;
  projectId: string;
  behaviorId: string;
  classifierName: string;
  accuracy: number;
  url: string;
  status: 'ready' | 'training' | 'failed';
  createdAt: string;
  usageMetrics: {
    totalCalls: number;
    lastUsed?: string;
    errorRate?: number;
  };
}

// Video File types
export interface VideoFile {
  fileName: string;
  fileSize: number;
  uploadDate: string;
  s3Key: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  metadata: {
    width?: number;
    height?: number;
    fps?: number;
    format?: string;
  };
}

// DynamoDB Schema Types
export interface DynamoDBItem {
  PK: string;
  SK: string;
  [key: string]: any;
}

// Project DynamoDB Item
export interface ProjectDynamoItem extends DynamoDBItem {
  PK: string; // USER#{user_id}
  SK: string; // PROJECT#{project_id}
  name: string;
  description: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  videoCount: number;
  hasDroidDataset: boolean;
  linkedDataSources: string[];
  metadata: object;
}

// Behavior DynamoDB Item
export interface BehaviorDynamoItem extends DynamoDBItem {
  PK: string; // PROJECT#{project_id}
  SK: string; // BEHAVIOR#{behavior_id}
  name: string;
  sampleCount: number;
  uploadedAt: string;
  updatedAt: string;
  linkedVideos: string[];
  trainingResults: object;
}

// Data Source DynamoDB Item
export interface DataSourceDynamoItem extends DynamoDBItem {
  PK: string; // USER#{user_id}
  SK: string; // DATASOURCE#{datasource_id}
  name: string;
  description?: string;
  folderPath: string;
  videoCount: number;
  totalSize: number;
  createdAt: string;
  updatedAt: string;
}

// Training Job DynamoDB Item
export interface TrainingJobDynamoItem extends DynamoDBItem {
  PK: string; // PROJECT#{project_id}
  SK: string; // TRAINING#{training_id}
  status: string;
  progress: number;
  startedAt: string;
  completedAt?: string;
  logs: string[];
  config: object;
}

// API Endpoint DynamoDB Item
export interface APIEndpointDynamoItem extends DynamoDBItem {
  PK: string; // PROJECT#{project_id}
  SK: string; // ENDPOINT#{endpoint_id}
  behaviorId: string;
  classifierName: string;
  accuracy: number;
  url: string;
  status: string;
  createdAt: string;
  usageMetrics: object;
} 