import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  ChevronLeft,
  FileVideo, 
  Upload, 
  Trash2,
  Download,
  Play,
  Calendar,
  HardDrive,
  MoreVertical
} from 'lucide-react';
import { api, type DataSource, type VideoFile } from '../lib/api';
import { DataSourceUpload } from '../components/datasources/DataSourceUpload';

interface FileDisplayData {
  id: string;
  name: string;
  size: string;
  duration: string;
  uploadDate: Date;
  thumbnail: string;
  path: string;
}

export function DataSourceFolderPage() {
  const { id } = useParams<{ id: string }>();
  const [dataSource, setDataSource] = useState<DataSource | null>(null);
  const [files, setFiles] = useState<FileDisplayData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const [activeUploads, setActiveUploads] = useState(0);

  useEffect(() => {
    if (id) {
      loadDataSource();
    }
  }, [id]);

  const loadDataSource = async () => {
    try {
      setLoading(true);
      setError(null);
      const ds = await api.dataSources.get(id!);
      setDataSource(ds);
      
      // Convert API files to display format
      const displayFiles: FileDisplayData[] = ds.files.map((file: VideoFile) => ({
        id: file.id || file.fileName, // Use file ID if available, fallback to fileName
        name: file.fileName,
        size: formatBytes(file.fileSize),
        duration: '0:00', // Duration not available from API yet
        uploadDate: new Date(file.uploadDate),
        thumbnail: '/thumbnails/default.jpg',
        path: file.s3Key
      }));
      
      setFiles(displayFiles);
    } catch (error) {
      console.error('Failed to load data source:', error);
      setError(error instanceof Error ? error.message : 'Failed to load data source');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUploadComplete = (uploadedFile: VideoFile) => {
    // Add the new file to the display
    const newDisplayFile: FileDisplayData = {
      id: uploadedFile.id || uploadedFile.fileName,
      name: uploadedFile.fileName,
      size: formatBytes(uploadedFile.fileSize),
      duration: '0:00',
      uploadDate: new Date(uploadedFile.uploadDate),
      thumbnail: '/thumbnails/default.jpg',
      path: uploadedFile.s3Key
    };
    setFiles(prev => [newDisplayFile, ...prev]);
    
    // Update data source stats
    if (dataSource) {
      setDataSource(prev => prev ? {
        ...prev,
        videoCount: prev.videoCount + 1,
        totalSize: prev.totalSize + uploadedFile.fileSize,
        files: [...prev.files, uploadedFile]
      } : null);
    }
  };

  const handleDelete = async (fileId: string) => {
    if (!dataSource || !confirm('Are you sure you want to delete this file?')) {
      return;
    }

    try {
      // Find the actual file data
      const fileToDelete = dataSource.files.find(f => f.fileName === fileId);
      if (!fileToDelete) {
        console.error('File not found in data source');
        return;
      }

      await api.dataSources.deleteFile(dataSource.id, fileToDelete.fileName);
      
      // Remove from local state
      setFiles(prev => prev.filter(file => file.id !== fileId));
      
      // Update data source stats
      setDataSource(prev => prev ? {
        ...prev,
        videoCount: prev.videoCount - 1,
        totalSize: prev.totalSize - fileToDelete.fileSize,
        files: prev.files.filter(f => f.fileName !== fileId)
      } : null);
    } catch (error) {
      console.error('Failed to delete file:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete file');
    }
  };
  
  const handleUploadStart = () => {
    setActiveUploads(prev => prev + 1);
  };
  
  const handleUploadEnd = () => {
    setActiveUploads(prev => Math.max(0, prev - 1));
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const totalSize = dataSource ? formatBytes(dataSource.totalSize) : '0 Bytes';

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-muted rounded animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-48 bg-muted rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/30 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400 dark:text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!dataSource) {
    return <div>Data source not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link 
            to="/data-sources"
            className="flex items-center space-x-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Back to Data Sources</span>
          </Link>
          <div className="h-6 w-px bg-border" />
          <div>
            <h1 className="text-2xl font-bold text-foreground">{dataSource.name}</h1>
            <p className="text-muted-foreground mt-1">
              {files.length} videos • {totalSize} total
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            onClick={() => setShowUploadArea(!showUploadArea)}
            className="flex items-center space-x-2 bg-primary hover:bg-primary/90"
          >
            <Upload className="h-4 w-4" />
            <span>Upload Files</span>
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <FileVideo className="h-5 w-5 text-green-600 dark:text-green-400" />
            <div>
              <div className="text-2xl font-bold text-foreground">{files.length}</div>
              <div className="text-sm text-muted-foreground">Video Files</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <HardDrive className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            <div>
              <div className="text-2xl font-bold text-foreground">{totalSize}</div>
              <div className="text-sm text-muted-foreground">Total Size</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <div>
              <div className="text-2xl font-bold text-foreground">
                {files.length > 0 ? formatDate(files[0].uploadDate) : 'N/A'}
              </div>
              <div className="text-sm text-muted-foreground">Last Upload</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Upload className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            <div>
              <div className="text-2xl font-bold text-foreground">{activeUploads}</div>
              <div className="text-sm text-muted-foreground">Active Uploads</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Upload Area */}
      {showUploadArea && (
        <DataSourceUpload 
          dataSourceId={dataSource.id} 
          onUploadComplete={handleUploadComplete}
          onUploadStart={handleUploadStart}
          onUploadEnd={handleUploadEnd}
        />
      )}

      {/* File Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {files.map((file) => (
          <Card key={file.id} className="overflow-hidden hover:shadow-md transition-shadow">
            {/* Thumbnail */}
            <div className="relative bg-muted aspect-video">
              <div className="absolute inset-0 flex items-center justify-center">
                <FileVideo className="h-12 w-12 text-muted-foreground" />
              </div>
              <div className="absolute bottom-2 right-2">
                <Badge variant="secondary" className="bg-foreground text-background text-xs">
                  {file.duration}
                </Badge>
              </div>
              <div className="absolute top-2 right-2">
                <Button variant="ghost" size="sm" className="p-1 bg-background/80">
                  <MoreVertical className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* File Info */}
            <div className="p-4">
              <h3 className="font-medium text-foreground truncate mb-2">{file.name}</h3>
              
              <div className="space-y-1 text-sm text-muted-foreground mb-3">
                <div className="flex justify-between">
                  <span>Size</span>
                  <span>{file.size}</span>
                </div>
                <div className="flex justify-between">
                  <span>Uploaded</span>
                  <span>{formatDate(file.uploadDate)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <Button variant="ghost" size="sm" className="p-1">
                  <Play className="h-3 w-3 mr-1" />
                  <span className="text-xs">Preview</span>
                </Button>
                <div className="flex items-center space-x-1">
                  <Button variant="ghost" size="sm" className="p-1">
                    <Download className="h-3 w-3" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="p-1 text-destructive hover:text-destructive/80"
                    onClick={() => handleDelete(file.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {files.length === 0 && (
        <div className="text-center py-12">
          <FileVideo className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No videos in this folder</h3>
          <p className="text-muted-foreground mb-4">
            Upload your first video file to get started
          </p>
          <Button
            onClick={() => setShowUploadArea(true)}
            className="bg-primary hover:bg-primary/90"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Videos
          </Button>
        </div>
      )}
    </div>
  );
}