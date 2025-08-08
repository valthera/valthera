import { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { Upload, FileVideo, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { api, type VideoFile } from '../../lib/api';
import { handleApiError } from '../../lib/errors';

interface DataSourceUploadProps {
  dataSourceId: string;
  onUploadComplete?: (file: VideoFile) => void;
  onUploadStart?: () => void;
  onUploadEnd?: () => void;
}

interface UploadingFile {
  name: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

export function DataSourceUpload({ dataSourceId, onUploadComplete, onUploadStart, onUploadEnd }: DataSourceUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<VideoFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  };

  const handleFiles = async (files: File[]) => {
    const videoFiles = files.filter(file => 
      file.type.startsWith('video/') || 
      file.name.toLowerCase().endsWith('.mp4') ||
      file.name.toLowerCase().endsWith('.avi') ||
      file.name.toLowerCase().endsWith('.mov') ||
      file.name.toLowerCase().endsWith('.mkv')
    );

    if (videoFiles.length === 0) {
      setUploadError('Please select valid video files (MP4, AVI, MOV, MKV)');
      return;
    }

    setUploadError(null);
    setUploading(true);
    
    // Initialize uploading files state
    const initialUploadingFiles = videoFiles.map(file => ({
      name: file.name,
      progress: 0,
      status: 'uploading' as const
    }));
    setUploadingFiles(initialUploadingFiles);
    
    if (onUploadStart) {
      onUploadStart();
    }

    try {
      const uploadPromises = videoFiles.map(async (file, index) => {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadingFiles(prev => {
            const updated = [...prev];
            if (updated[index] && updated[index].progress < 90) {
              updated[index].progress += Math.random() * 10;
            }
            return updated;
          });
        }, 200);

        try {
          // Upload directly to Lambda function (not to S3)
          const formData = new FormData();
          formData.append('file', file);
          
          // Convert file to base64 for JSON transmission
          const arrayBuffer = await file.arrayBuffer();
          const base64Content = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
          
          // Upload to Lambda function
          const uploadedFile = await api.dataSources.uploadFile(dataSourceId, {
            filename: file.name,
            content: base64Content
          });

          clearInterval(progressInterval);
          
          // Mark as completed
          setUploadingFiles(prev => {
            const updated = [...prev];
            if (updated[index]) {
              updated[index].progress = 100;
              updated[index].status = 'completed';
            }
            return updated;
          });

          setUploadedFiles(prev => [...prev, uploadedFile]);
          
          if (onUploadComplete) {
            onUploadComplete(uploadedFile);
          }

          return uploadedFile;

        } catch (error) {
          clearInterval(progressInterval);
          const apiError = handleApiError(error);
          const errorMessage = `Failed to upload ${file.name}: ${apiError.message}`;
          
          // Mark file as error
          setUploadingFiles(prev => {
            const updated = [...prev];
            if (updated[index]) {
              updated[index].status = 'error';
              updated[index].error = errorMessage;
            }
            return updated;
          });
          
          console.error('Upload error:', error);
          throw error;
        }
      });
      
      // Wait for all uploads to complete or fail
      const results = await Promise.allSettled(uploadPromises);
      
      // Check if any uploads failed
      const failures = results.filter(result => result.status === 'rejected');
      if (failures.length > 0) {
        setUploadError(`${failures.length} file(s) failed to upload`);
      }
      
    } finally {
      setUploading(false);
      if (onUploadEnd) {
        onUploadEnd();
      }
      
      // Clear uploading files after a delay
      setTimeout(() => {
        setUploadingFiles([]);
      }, 3000);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <Card className={`border-2 border-dashed transition-colors ${
        isDragOver 
          ? 'border-blue-400 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400'
      }`}>
        <CardContent className="p-6">
          <div
            className="text-center"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="flex flex-col items-center space-y-4">
              <div className="flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full">
                {uploading ? (
                  <Loader2 className="h-8 w-8 text-gray-400 animate-spin" />
                ) : (
                  <Upload className="h-8 w-8 text-gray-400" />
                )}
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {uploading ? `Uploading ${uploadingFiles.length} file(s)...` : 'Upload Video Files'}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Drag and drop video files here, or click to browse
                </p>
                
                {!uploading && (
                  <Button
                    onClick={openFileDialog}
                    variant="outline"
                    className="bg-white"
                  >
                    <FileVideo className="mr-2 h-4 w-4" />
                    Select Video Files
                  </Button>
                )}
              </div>

              {/* Progress Bars for Multiple Files */}
              {uploading && uploadingFiles.length > 0 && (
                <div className="w-full max-w-md space-y-3">
                  {uploadingFiles.map((file, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-700 truncate max-w-48">{file.name}</span>
                        <span className={`font-medium ${
                          file.status === 'completed' ? 'text-green-600' :
                          file.status === 'error' ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {file.status === 'completed' ? 'Complete' :
                           file.status === 'error' ? 'Failed' :
                           `${Math.round(file.progress)}%`}
                        </span>
                      </div>
                      <Progress 
                        value={file.progress} 
                        className={`h-2 ${
                          file.status === 'error' ? 'bg-red-100' : ''
                        }`}
                      />
                      {file.error && (
                        <p className="text-xs text-red-600">{file.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Supported Formats */}
              <div className="text-xs text-gray-500">
                Supported formats: MP4, AVI, MOV, MKV
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="video/*,.mp4,.avi,.mov,.mkv"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Error Display */}
      {uploadError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{uploadError}</AlertDescription>
        </Alert>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recently Uploaded</CardTitle>
            <CardDescription>
              Files uploaded to this data source
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {file.fileName}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.fileSize)} • {file.processingStatus}
                      </p>
                    </div>
                  </div>
                  
                  <Badge 
                    variant={file.processingStatus === 'completed' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {file.processingStatus}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 