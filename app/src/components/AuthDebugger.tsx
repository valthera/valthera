import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { debugAuthState, testApiConnection } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export function AuthDebugger() {
  const [authState, setAuthState] = useState<any>(null);
  const [apiTestResult, setApiTestResult] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const { user, session } = useAuth();

  const handleDebugAuth = async () => {
    setLoading(true);
    try {
      const auth = await debugAuthState();
      setAuthState(auth);
    } catch (error) {
      console.error('Debug auth error:', error);
      setAuthState({ error: error instanceof Error ? error.message : 'Unknown error' });
    } finally {
      setLoading(false);
    }
  };

  const handleTestApi = async () => {
    setLoading(true);
    try {
      const result = await testApiConnection();
      setApiTestResult(result ? '✅ API connection successful' : '❌ API connection failed');
    } catch (error) {
      setApiTestResult(`❌ API test error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Authentication Debugger</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <h3 className="font-semibold">Current Auth State:</h3>
          <div className="text-sm bg-gray-100 p-2 rounded">
            <div>User: {user ? '✅ Logged in' : '❌ Not logged in'}</div>
            <div>Session: {session ? '✅ Active' : '❌ No session'}</div>
            {user && (
              <div>User ID: {user.id}</div>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Button 
            onClick={handleDebugAuth} 
            disabled={loading}
            variant="outline"
          >
            Debug Auth State
          </Button>
          {authState && (
            <div className="text-sm bg-gray-100 p-2 rounded">
              <pre>{JSON.stringify(authState, null, 2)}</pre>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Button 
            onClick={handleTestApi} 
            disabled={loading}
            variant="outline"
          >
            Test API Connection
          </Button>
          {apiTestResult && (
            <div className="text-sm bg-gray-100 p-2 rounded">
              {apiTestResult}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 