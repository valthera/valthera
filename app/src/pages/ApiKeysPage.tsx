import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { Plus, Copy, Trash2, Key, Eye, EyeOff } from 'lucide-react';
import { api, type ApiKey } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';

export function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const { theme } = useTheme();

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const data = await api.getApiKeys();
      setApiKeys(data);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const createApiKey = async () => {
    if (!newKeyName.trim()) return;

    try {
      setCreateLoading(true);
      // Provide default scopes for the API key
      const defaultScopes = ['read', 'write'];
      const newKey = await api.createApiKey(newKeyName, defaultScopes);
      setApiKeys([newKey, ...apiKeys]);
      setNewKeyName('');
      setIsCreateModalOpen(false);
      // Show the newly created key
      setVisibleKeys(new Set([newKey.key_id]));
    } catch (error) {
      console.error('Failed to create API key:', error);
    } finally {
      setCreateLoading(false);
    }
  };

  const deleteApiKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await api.deleteApiKey(keyId);
      setApiKeys(apiKeys.filter(key => key.key_id !== keyId));
      setVisibleKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(keyId);
        return newSet;
      });
    } catch (error) {
      console.error('Failed to delete API key:', error);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const maskKey = (key: string) => {
    const parts = key.split('_');
    if (parts.length >= 3) {
      return `${parts[0]}_${parts[1]}_${'*'.repeat(8)}...`;
    }
    return key.substring(0, 8) + '*'.repeat(key.length - 8);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading API keys...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">API Keys</h1>
          <p className="text-muted-foreground mt-1">
            Manage your API keys for accessing the Valthera Perception API
          </p>
        </div>
        
        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="mr-2 h-4 w-4" />
              Generate Key
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Generate New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key to authenticate your requests to the Valthera API.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="keyName">Key Name</Label>
                <Input
                  id="keyName"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production API Key"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setIsCreateModalOpen(false)}
                disabled={createLoading}
              >
                Cancel
              </Button>
              <Button
                onClick={createApiKey}
                disabled={!newKeyName.trim() || createLoading}
                className="bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {createLoading ? 'Generating...' : 'Generate Key'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys Table */}
      {apiKeys.length === 0 ? (
        <Card className="border">
          <CardContent className="text-center py-12">
            <Key className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No API keys</h3>
            <p className="text-muted-foreground mb-4">
              Generate your first API key to start using the Valthera API
            </p>
            <Button
              onClick={() => setIsCreateModalOpen(true)}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              Generate Key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="border">
          <CardHeader>
            <CardTitle>Your API Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((apiKey) => {
                  const isVisible = visibleKeys.has(apiKey.key_id);
                  
                  return (
                    <TableRow key={apiKey.key_id}>
                      <TableCell className="font-medium">
                        {apiKey.name}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <code className="text-xs bg-muted px-2 py-1 rounded font-mono">
                            {isVisible ? apiKey.key_id : maskKey(apiKey.key_id)}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleKeyVisibility(apiKey.key_id)}
                          >
                            {isVisible ? (
                              <EyeOff className="h-3 w-3" />
                            ) : (
                              <Eye className="h-3 w-3" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(apiKey.key_id)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {apiKey.scopes.join(', ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {apiKey.is_expired ? 'Expired' : 'Active'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(apiKey.created_at * 1000).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteApiKey(apiKey.key_id)}
                          className="text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Usage Examples */}
      {apiKeys.length > 0 && (
        <Card className="border">
          <CardHeader>
            <CardTitle>Usage Examples</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium text-foreground mb-2">Authentication Header</h4>
              <div className={`
                p-4 rounded-lg font-mono text-sm overflow-x-auto
                ${theme === 'dark' 
                  ? 'bg-gray-800 text-green-400 border border-gray-600' 
                  : 'bg-black text-green-400'
                }
              `}>
                <pre>Authorization: Bearer YOUR_API_KEY</pre>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-foreground mb-2">cURL Example</h4>
              <div className={`
                p-4 rounded-lg font-mono text-sm overflow-x-auto
                ${theme === 'dark' 
                  ? 'bg-gray-800 text-green-400 border border-gray-600' 
                  : 'bg-black text-green-400'
                }
              `}>
                <pre>{`curl -X POST "https://api.valthera.com/v1/classify/YOUR_ENDPOINT" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@path/to/video.mp4"`}</pre>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-foreground mb-2">Python Example</h4>
              <div className={`
                p-4 rounded-lg font-mono text-sm overflow-x-auto
                ${theme === 'dark' 
                  ? 'bg-gray-800 text-green-400 border border-gray-600' 
                  : 'bg-black text-green-400'
                }
              `}>
                <pre>{`import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

with open("video.mp4", "rb") as video_file:
    files = {"video": video_file}
    response = requests.post(
        "https://api.valthera.com/v1/classify/YOUR_ENDPOINT",
        headers=headers,
        files=files
    )
    result = response.json()
    print(result)`}</pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}