import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  FolderOpen, 
  Upload, 
  Plus, 
  MoreVertical,
  Trash2,
  Download,
  Eye
} from 'lucide-react';
import { api, type DataSource } from '../lib/api';

interface DataFolder {
  id: string;
  name: string;
  size: string;
  videoCount: number;
  subfolderCount: number;
  lastModified: Date;
  path: string;
  totalSize: number;
  folderPath: string;
}

export function DataSourcesPage() {
  const [folders, setFolders] = useState<DataFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const dataSources = await api.dataSources.list();
      
      // Ensure dataSources is an array
      const dataSourcesArray = Array.isArray(dataSources) ? dataSources : [];
      
      // Convert API data sources to UI format
      const convertedFolders: DataFolder[] = dataSourcesArray.map((ds: DataSource) => ({
        id: ds.id,
        name: ds.name,
        size: formatBytes(ds.totalSize),
        videoCount: ds.videoCount,
        subfolderCount: 0, // API doesn't provide subfolder count
        lastModified: new Date(ds.updatedAt),
        path: `/data-sources/${ds.id}`,
        totalSize: ds.totalSize,
        folderPath: ds.folderPath
      }));
      
      setFolders(convertedFolders);
    } catch (error) {
      console.error('Failed to load data sources:', error);
      setError(error instanceof Error ? error.message : 'Failed to load data sources');
      setFolders([]);
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

  const handleCreateFolder = async (folderName: string) => {
    try {
      const newDataSource = await api.dataSources.create({
        name: folderName,
        description: 'New data source folder'
      });
      
      const newFolder: DataFolder = {
        id: newDataSource.id,
        name: newDataSource.name,
        size: formatBytes(newDataSource.totalSize),
        videoCount: newDataSource.videoCount,
        subfolderCount: 0,
        lastModified: new Date(newDataSource.updatedAt),
        path: `/data-sources/${newDataSource.id}`,
        totalSize: newDataSource.totalSize,
        folderPath: newDataSource.folderPath
      };
      
      setFolders(prev => [...prev, newFolder]);
      setShowCreateDialog(false);
      setNewFolderName('');
    } catch (error) {
      console.error('Failed to create folder:', error);
      setError(error instanceof Error ? error.message : 'Failed to create folder');
    }
  };

  const handleCreateFolderClick = () => {
    setShowCreateDialog(true);
  };

  const handleCreateFolderSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFolderName.trim()) {
      handleCreateFolder(newFolderName.trim());
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!confirm('Are you sure you want to delete this data source? This will permanently delete all files in this folder.')) {
      return;
    }

    try {
      await api.dataSources.delete(folderId);
      setFolders(prev => prev.filter(folder => folder.id !== folderId));
    } catch (error) {
      console.error('Failed to delete folder:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete folder');
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Create Button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-black">Data Sources</h1>
          <p className="text-gray-600 mt-1">Manage your video data sources and folders</p>
        </div>
        <Button
          onClick={handleCreateFolderClick}
          className="bg-black hover:bg-gray-800"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Data Source
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Folders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {folders.map((folder) => (
          <Card key={folder.id} className="p-4 hover:shadow-md transition-shadow border-l-4 border-l-blue-500">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <FolderOpen className="h-8 w-8 text-blue-600" />
                <div>
                  <h3 className="font-medium text-black">{folder.name}</h3>
                  <p className="text-sm text-gray-500">
                    Modified {formatDate(folder.lastModified)}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" className="p-1">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Size</span>
                <Badge variant="outline">{folder.size}</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Videos</span>
                <span className="font-medium">{folder.videoCount}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Subfolders</span>
                <span className="font-medium">{folder.subfolderCount}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <Link
                to={folder.path}
                className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center space-x-1"
              >
                <Eye className="h-3 w-3" />
                <span>View Files</span>
              </Link>
              <div className="flex items-center space-x-1">
                <Link to={folder.path}>
                  <Button variant="ghost" size="sm" className="p-1 text-green-600 hover:text-green-700" title="Upload Files">
                    <Upload className="h-3 w-3" />
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" className="p-1" title="Download Folder">
                  <Download className="h-3 w-3" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="p-1 text-red-600 hover:text-red-700"
                  onClick={() => handleDeleteFolder(folder.id)}
                  title="Delete Folder"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Create Folder Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-medium text-black mb-4">Create New Data Source</h3>
            <form onSubmit={handleCreateFolderSubmit}>
              <div className="mb-4">
                <label htmlFor="folderName" className="block text-sm font-medium text-gray-700 mb-2">
                  Data Source Name
                </label>
                <input
                  type="text"
                  id="folderName"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter data source name..."
                  autoFocus
                />
              </div>
              <div className="flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateDialog(false);
                    setNewFolderName('');
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-black hover:bg-gray-800"
                  disabled={!newFolderName.trim()}
                >
                  Create Data Source
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Empty State */}
      {folders.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-black mb-2">No data sources yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first data source to start uploading video data
          </p>
          <Button
            onClick={handleCreateFolderClick}
            className="bg-black hover:bg-gray-800"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create First Data Source
          </Button>
        </div>
      )}
    </div>
  );
}