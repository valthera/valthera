import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Eye, EyeOff, AlertCircle, X } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const { theme } = useTheme()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const { error } = await signIn(email, password)
    if (error) {
      setError(error.message)
    } else {
      navigate('/dashboard')
    }
    setLoading(false)
  }

  return (
    <div className={`
      min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8
      ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}
    `}>
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <img
            className="mx-auto h-12 w-auto logo-invert"
            src="/logo.svg"
            alt="Valthera"
          />
          <h2 className={`
            mt-6 text-3xl font-bold
            ${theme === 'dark' ? 'text-white' : 'text-black'}
          `}>
            Welcome back
          </h2>
          <p className={`
            mt-2
            ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}
          `}>
            Sign in to your account to continue
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className={`
                block text-sm font-medium
                ${theme === 'dark' ? 'text-white' : 'text-black'}
              `}>
                Email address
              </label>
              <div className="mt-1 relative">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`
                    appearance-none relative block w-full px-3 py-2 border rounded-md 
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    placeholder:text-sm transition-colors duration-200
                    ${theme === 'dark' 
                      ? 'border-gray-600 bg-gray-800 text-white placeholder:text-gray-400' 
                      : 'border-gray-300 bg-white text-black placeholder:text-gray-500'
                    }
                  `}
                  placeholder="Enter your email"
                />
                {email && (
                  <button
                    type="button"
                    onClick={() => setEmail('')}
                    className={`
                      absolute right-3 top-1/2 -translate-y-1/2 hover:scale-110 transition-all
                      ${theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-black'}
                    `}
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="password" className={`
                block text-sm font-medium
                ${theme === 'dark' ? 'text-white' : 'text-black'}
              `}>
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`
                    appearance-none relative block w-full px-3 py-2 border rounded-md 
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    placeholder:text-sm transition-colors duration-200
                    ${theme === 'dark' 
                      ? 'border-gray-600 bg-gray-800 text-white placeholder:text-gray-400' 
                      : 'border-gray-300 bg-white text-black placeholder:text-gray-500'
                    }
                  `}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`
                    absolute right-3 top-1/2 -translate-y-1/2 hover:scale-110 transition-all
                    ${theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-black'}
                  `}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <Alert className={`
              ${theme === 'dark' ? 'bg-red-900/20 border-red-800' : 'bg-red-50 border-red-200'}
            `}>
              <AlertCircle className={`
                h-4 w-4 ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}
              `} />
              <AlertDescription className={`
                ${theme === 'dark' ? 'text-red-300' : 'text-red-700'}
              `}>
                {error}
              </AlertDescription>
            </Alert>
          )}

          <div>
            <Button
              type="submit"
              disabled={loading}
              className={`
                w-full flex justify-center py-2 px-4 border border-transparent rounded-md 
                text-sm font-medium transition-all duration-200
                ${loading 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'hover:scale-105'
                }
                ${theme === 'dark' 
                  ? 'bg-white text-black hover:bg-gray-200' 
                  : 'bg-black text-white hover:bg-gray-800'
                }
              `}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </div>

          <div className="text-center">
            <Link
              to="/forgot-password"
              className={`
                text-sm hover:underline transition-colors duration-200
                ${theme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'}
              `}
            >
              Forgot your password?
            </Link>
          </div>

          <div className="text-center">
            <span className={`
              text-sm
              ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}
            `}>
              Don't have an account?{' '}
            </span>
            <Link
              to="/signup"
              className={`
                text-sm font-medium hover:underline transition-colors duration-200
                ${theme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'}
              `}
            >
              Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
} 