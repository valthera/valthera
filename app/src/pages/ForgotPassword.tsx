import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Eye, EyeOff, AlertCircle, CheckCircle2, Mail, Key, X } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [confirmationCode, setConfirmationCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmNewPassword, setConfirmNewPassword] = useState('')
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [showResetForm, setShowResetForm] = useState(false)
  const [resetSent, setResetSent] = useState(false)
  const { resetPassword, confirmResetPassword } = useAuth()
  const { theme } = useTheme()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    const { error } = await resetPassword(email)
    
    if (error) {
      setError(error.message || 'Failed to send reset code')
    } else {
      setMessage('Check your email for a password reset code!')
      setShowResetForm(true)
      setResetSent(true)
    }
    
    setLoading(false)
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    if (newPassword !== confirmNewPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long')
      setLoading(false)
      return
    }

    const { error } = await confirmResetPassword(email, confirmationCode, newPassword)
    
    if (error) {
      setError(error.message || 'Failed to reset password')
    } else {
      setMessage('Password reset successfully! You can now sign in with your new password.')
      setShowResetForm(false)
      setEmail('')
      setConfirmationCode('')
      setNewPassword('')
      setConfirmNewPassword('')
    }
    
    setLoading(false)
  }

  if (showResetForm) {
    return (
      <AuthShell>
        <div className={`
          rounded-lg border p-8 shadow-sm transition-colors duration-200
          ${theme === 'dark' 
            ? 'bg-gray-800 border-gray-600' 
            : 'bg-white border-gray-200'
          }
        `}>
          <div className="text-center mb-8">
            <div className={`
              mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4
              ${theme === 'dark' 
                ? 'bg-white text-black' 
                : 'bg-black text-white'
              }
            `}>
              <Key className="h-6 w-6" />
            </div>
            <h1 className={`
              text-2xl font-bold mb-2
              ${theme === 'dark' ? 'text-white' : 'text-black'}
            `}>
              Create new password
            </h1>
            <p className={`
              ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}
            `}>
              Enter the code from your email and create a new password
            </p>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {message && (
            <Alert className="mb-6">
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleResetPassword} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                disabled
                className="w-full bg-gray-50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmationCode">Confirmation Code</Label>
              <Input
                id="confirmationCode"
                type="text"
                placeholder="Enter the 6-digit code"
                value={confirmationCode}
                onChange={(e) => setConfirmationCode(e.target.value)}
                required
                className="w-full text-center text-lg tracking-widest"
                maxLength={6}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">New Password</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Create a strong password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-500">Must be at least 8 characters long</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmNewPassword">Confirm New Password</Label>
              <div className="relative">
                <Input
                  id="confirmNewPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your new password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  required
                  className="w-full pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
              size="lg"
            >
              {loading ? 'Resetting Password...' : 'Reset Password'}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowResetForm(false)}
              className="w-full"
            >
              Back to Email Step
            </Button>
          </form>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell>
      <div className={`
        rounded-lg border p-8 shadow-sm transition-colors duration-200
        ${theme === 'dark' 
          ? 'bg-gray-800 border-gray-600' 
          : 'bg-white border-gray-200'
        }
      `}>
        <div className="text-center mb-8">
          <div className={`
            mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4
            ${theme === 'dark' 
              ? 'bg-white text-black' 
              : 'bg-black text-white'
            }
          `}>
            <Mail className="h-6 w-6" />
          </div>
          <h1 className={`
            text-2xl font-bold mb-2
            ${theme === 'dark' ? 'text-white' : 'text-black'}
          `}>
            Reset your password
          </h1>
          <p className={`
            ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}
          `}>
            Enter your email address and we'll send you a code to reset your password
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {message && (
          <Alert className={`
            mb-6 ${theme === 'dark' ? 'bg-green-900/20 border-green-800' : 'bg-green-50 border-green-200'}
          `}>
            <CheckCircle2 className={`
              h-4 w-4 ${theme === 'dark' ? 'text-green-400' : 'text-green-600'}
            `} />
            <AlertDescription className={`
              ${theme === 'dark' ? 'text-green-300' : 'text-green-700'}
            `}>
              {message}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className={`
              ${theme === 'dark' ? 'text-white' : 'text-black'}
            `}>
              Email address
            </Label>
            <div className="mt-1 relative">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none relative block w-full px-3 py-2 border border-input bg-background text-foreground placeholder-muted-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                placeholder="Enter your email"
              />
              {email && (
                <button
                  type="button"
                  onClick={() => setEmail('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <p className="text-xs text-muted-foreground">Must be at least 8 characters long</p>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2"></div>
                  Sending...
                </div>
              ) : (
                'Send reset link'
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-muted-foreground">
              Remember your password?{' '}
              <Link to="/signin" className="text-foreground font-medium hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </AuthShell>
  );
} 