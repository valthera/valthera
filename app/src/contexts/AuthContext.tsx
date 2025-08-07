import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { signIn, signUp, signOut, getCurrentUser, confirmSignUp, resetPassword, confirmResetPassword } from 'aws-amplify/auth'
import { fetchUserAttributes } from 'aws-amplify/auth'

interface User {
  id: string
  email: string
  created_at: string
  api_key?: string
  stripe_customer_id?: string
  subscription_status?: 'active' | 'inactive' | 'past_due'
  plan_type?: 'basic' | 'pro' | 'enterprise'
}

interface AuthContextType {
  user: User | null
  session: any
  loading: boolean
  signUp: (email: string, password: string) => Promise<{ error?: any }>
  signIn: (email: string, password: string) => Promise<{ error?: any }>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<{ error?: any }>
  confirmResetPassword: (email: string, code: string, newPassword: string) => Promise<{ error?: any }>
  confirmSignUp: (email: string, code: string) => Promise<{ error?: any }>
  generateApiKey: () => Promise<string>
  getUserProfile: () => Promise<User | null>
  refreshUserData: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const getUserProfile = async (): Promise<User | null> => {
    try {
      const currentUser = await getCurrentUser()
      const attributes = await fetchUserAttributes()
      
      // Create user object from Cognito attributes
      const userObj: User = {
        id: currentUser.userId,
        email: attributes.email || '',
        created_at: attributes.created_at || new Date().toISOString(),
        api_key: attributes['custom:api_key'] || undefined,
        stripe_customer_id: attributes['custom:stripe_customer_id'] || undefined,
        subscription_status: (attributes['custom:subscription_status'] as any) || 'inactive',
        plan_type: (attributes['custom:plan_type'] as any) || 'free',
      }
      
      setUser(userObj)
      return userObj
    } catch (error) {
      console.error('Error fetching user profile:', error)
      return null
    }
  }

  useEffect(() => {
    const checkAuthState = async () => {
      try {
        const currentUser = await getCurrentUser()
        setSession({ user: currentUser })
        await getUserProfile()
      } catch (error) {
        console.log('No authenticated user')
        setSession(null)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    checkAuthState()
  }, [])

  const signUpHandler = async (email: string, password: string) => {
    try {
      // Check if there's already an authenticated user and sign out first
      try {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          console.log('Found existing authenticated user, signing out first...')
          await signOut()
          setUser(null)
          setSession(null)
        }
      } catch (error) {
        // No authenticated user, continue with sign up
        console.log('No existing authenticated user found')
      }

      await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
          },
        },
      })
      return {}
    } catch (error) {
      console.error('Sign up error:', error)
      return { error }
    }
  }

  const signInHandler = async (email: string, password: string) => {
    try {
      // Check if there's already an authenticated user and sign out first
      try {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          console.log('Found existing authenticated user, signing out first...')
          await signOut()
          setUser(null)
          setSession(null)
        }
      } catch (error) {
        // No authenticated user, continue with sign in
        console.log('No existing authenticated user found')
      }

      // For local development, use USER_PASSWORD_AUTH flow
      const isLocal = import.meta.env.VITE_ENVIRONMENT === 'local' || import.meta.env.NODE_ENV === 'development'
      
      if (isLocal) {
        // Use USER_PASSWORD_AUTH for local development
        await signIn({ 
          username: email, 
          password,
          options: {
            authFlowType: 'USER_PASSWORD_AUTH'
          }
        })
      } else {
        // Use default flow for production
        await signIn({ username: email, password })
      }
      
      const userProfile = await getUserProfile()
      if (userProfile) {
        setSession({ user: await getCurrentUser() })
      }
      return {}
    } catch (error) {
      console.error('Sign in error:', error)
      return { error }
    }
  }

  const signOutHandler = async () => {
    try {
      await signOut()
      setUser(null)
      setSession(null)
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  const resetPasswordHandler = async (email: string) => {
    try {
      await resetPassword({ username: email })
      return {}
    } catch (error) {
      console.error('Reset password error:', error)
      return { error }
    }
  }

  const confirmResetPasswordHandler = async (email: string, code: string, newPassword: string) => {
    try {
      await confirmResetPassword({ username: email, confirmationCode: code, newPassword })
      return {}
    } catch (error) {
      console.error('Confirm reset password error:', error)
      return { error }
    }
  }

  const confirmSignUpHandler = async (email: string, code: string) => {
    try {
      await confirmSignUp({ username: email, confirmationCode: code })
      
      // After successful confirmation, sign in the user
      try {
        const isLocal = import.meta.env.VITE_ENVIRONMENT === 'local' || import.meta.env.NODE_ENV === 'development'
        
        if (isLocal) {
          // Use USER_PASSWORD_AUTH for local development
          await signIn({ 
            username: email, 
            password: '', // User will need to enter password
            options: {
              authFlowType: 'USER_PASSWORD_AUTH'
            }
          })
        } else {
          await signIn({ username: email, password: '' })
        }
        
        const userProfile = await getUserProfile()
        if (userProfile) {
          setSession({ user: await getCurrentUser() })
        }
      } catch (signInError) {
        console.log('User needs to sign in manually after confirmation')
      }
      
      return {}
    } catch (error) {
      console.error('Confirm sign up error:', error)
      return { error }
    }
  }

  const generateApiKey = async (): Promise<string> => {
    if (!session?.user) {
      throw new Error('User not authenticated')
    }

    const apiKey = `blink_${Math.random().toString(36).substring(2)}_${Date.now()}`
    
    // For now, we'll just return the API key
    // In a real implementation, you'd update the user's custom attributes
    // or store this in a separate database
    
    // Update local user state
    setUser(prev => prev ? { ...prev, api_key: apiKey } : null)

    return apiKey
  }

  const refreshUserData = async (): Promise<void> => {
    try {
      await getUserProfile()
    } catch (error) {
      console.error('Error refreshing user data:', error)
    }
  }

  const value = {
    user,
    session,
    loading,
    signUp: signUpHandler,
    signIn: signInHandler,
    signOut: signOutHandler,
    resetPassword: resetPasswordHandler,
    confirmResetPassword: confirmResetPasswordHandler,
    confirmSignUp: confirmSignUpHandler,
    generateApiKey,
    getUserProfile,
    refreshUserData,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 