import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  AnalysisRequest, 
  AnalysisResult, 
  PipelineStatus, 
  ClassifierInfo 
} from '../types/api';

class JarvisApiClient {
  private api: AxiosInstance;

  constructor(baseURL: string = `http://${window.location.hostname}:3000/api/v1`) {
    this.api = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Analysis endpoints
  async analyze(request: AnalysisRequest): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await this.api.post('/analyze', request);
    return response.data;
  }

  async getAnalysisStatus(): Promise<PipelineStatus> {
    const response: AxiosResponse<PipelineStatus> = await this.api.get('/analyze/status');
    return response.data;
  }

  async testAnalysis(): Promise<AnalysisResult> {
    const response: AxiosResponse<{ result: AnalysisResult }> = await this.api.post('/analyze/test');
    return response.data.result;
  }

  // Pipeline control endpoints
  async getStatus(): Promise<PipelineStatus> {
    const response: AxiosResponse<PipelineStatus> = await this.api.get('/status');
    return response.data;
  }

  async startPipeline(): Promise<{ status: string; message: string }> {
    const response = await this.api.post('/pipeline/start');
    return response.data;
  }

  async stopPipeline(): Promise<{ status: string; message: string }> {
    const response = await this.api.post('/pipeline/stop');
    return response.data;
  }

  async resetPipeline(): Promise<{ status: string; message: string }> {
    const response = await this.api.post('/pipeline/reset');
    return response.data;
  }

  async getPipelineConfig(): Promise<{ config: any; timestamp: number }> {
    const response = await this.api.get('/pipeline/config');
    return response.data;
  }

  async updatePipelineConfig(config: any): Promise<{ status: string; message: string; config: any }> {
    const response = await this.api.post('/pipeline/config', config);
    return response.data;
  }

  async healthCheck(): Promise<{ status: string; pipeline_running: boolean; depth_camera_available: boolean; enabled_classifiers: number; timestamp: number }> {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Classifier management endpoints
  async listClassifiers(): Promise<{ classifiers: ClassifierInfo[]; total_count: number; enabled_count: number; timestamp: number }> {
    const response = await this.api.get('/classifiers');
    return response.data;
  }

  async getClassifier(name: string): Promise<{ name: string; stats: any; timestamp: number }> {
    const response = await this.api.get(`/classifiers/${name}`);
    return response.data;
  }

  async configureClassifier(name: string, config: { confidence_threshold: number; enabled: boolean; model_version?: string }): Promise<{ status: string; message: string; config: any; timestamp: number }> {
    const response = await this.api.post(`/classifiers/${name}/config`, config);
    return response.data;
  }

  async enableClassifier(name: string): Promise<{ status: string; message: string; timestamp: number }> {
    const response = await this.api.post(`/classifiers/${name}/enable`);
    return response.data;
  }

  async disableClassifier(name: string): Promise<{ status: string; message: string; timestamp: number }> {
    const response = await this.api.post(`/classifiers/${name}/disable`);
    return response.data;
  }

  async initializeClassifier(name: string): Promise<{ status: string; message: string; timestamp: number }> {
    const response = await this.api.post(`/classifiers/${name}/initialize`);
    return response.data;
  }

  async getClassifierStats(): Promise<{ registry_stats: any; timestamp: number }> {
    const response = await this.api.get('/classifiers/stats');
    return response.data;
  }

  async getClassifierTypes(): Promise<{ available_types: string[]; timestamp: number }> {
    const response = await this.api.get('/classifiers/types');
    return response.data;
  }

  // Frame access endpoints
  async getLatestResult(): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await this.api.get('/latest');
    return response.data;
  }

  async getAnnotatedFrame(): Promise<string> {
    const response = await this.api.get('/frame/annotated', { responseType: 'blob' });
    return URL.createObjectURL(response.data);
  }

  async getRawFrame(): Promise<string> {
    const response = await this.api.get('/frame/raw', { responseType: 'blob' });
    return URL.createObjectURL(response.data);
  }

  async getDepthMap(): Promise<string> {
    const response = await this.api.get('/depth/map', { responseType: 'blob' });
    return URL.createObjectURL(response.data);
  }

  async getDepthData(): Promise<{ frame_id: number; timestamp: number; resolution?: number[]; intrinsics: any; has_color_frame: boolean; has_depth_frame: boolean }> {
    const response = await this.api.get('/depth/data');
    return response.data;
  }

  async getFrameInfo(): Promise<{ frame_id: number; timestamp: number; resolution: number[]; processing_time_ms: number; pipeline_info: any; detection_count: number; cache_hit: boolean }> {
    const response = await this.api.get('/frame/info');
    return response.data;
  }
}

export default JarvisApiClient;
