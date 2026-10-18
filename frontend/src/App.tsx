
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import {
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from './api/auth'

import type { User } from './api/auth'

import { getBackendHealth } from './api/health'

import './App.css'

type AuthMode = 'login' | 'register'

type ConnectionStatus = 'checking' | 'connected' | 'error'

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [connection, setConnection] =
    useState<ConnectionStatus>('checking')

  useEffect(() => {
    let active = true

    async function initialize() {
      try {
        const health = await getBackendHealth()

        if (!active) return

        setConnection(
          health.status === 'healthy' ? 'connected' : 'error',
        )
      } catch {
        if (active) setConnection('error')
      }

      try {
        const currentUser = await getCurrentUser()

        if (active) setUser(currentUser)
      } catch {
        if (active) {
          setError('Unable to check your login session.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void initialize()

    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setError('')
    setMessage('')
    setSubmitting(true)

    try {
      if (mode === 'register') {
        await registerUser({ email, password })

        setMessage('Account created. Please sign in.')
        setMode('login')
        setPassword('')
      } else {
        await loginUser({ email, password })

        const currentUser = await getCurrentUser()

        if (!currentUser) {
          throw new Error('Login succeeded, but the session was not found.')
        }

        setUser(currentUser)
        setPassword('')
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to complete your request.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleLogout() {
    setSubmitting(true)
    setError('')
    setMessage('')

    try {
      await logoutUser()
      setUser(null)
      setPassword('')
      setMessage('You have been logged out.')
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Logout failed.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <main className="container">
        <h1>DevTrack</h1>
        <p role="status">Loading your session...</p>
      </main>
    )
  }

  return (
    <main className="container">
      <header className="app-header">
        <h1>DevTrack</h1>
        <p>Software Development Management Platform</p>
      </header>

      <section className="status-card">
        <h2>Backend Connection</h2>
        <p role="status">
          {connection === 'connected'
            ? 'Backend connected'
            : connection === 'checking'
              ? 'Checking connection...'
              : 'Backend connection unavailable'}
        </p>
      </section>

      {error && <p className="error-message" role="alert">{error}</p>}
      {message && <p className="success-message" role="status">{message}</p>}

      {user ? (
        <section className="auth-card">
          <h2>Welcome to DevTrack</h2>

          <p>You are signed in as:</p>
          <p><strong>{user.email}</strong></p>

          <div className="dashboard-preview">
            <h3>Your Dashboard</h3>
            <p>
              Project management and bug tracking are coming next.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void handleLogout()}
            disabled={submitting}
          >
            {submitting ? 'Logging out...' : 'Log Out'}
          </button>
        </section>
      ) : (
        <section className="auth-card">
          <h2>
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </h2>

          <form onSubmit={(event) => void handleSubmit(event)}>
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete={
                mode === 'register'
                  ? 'new-password'
                  : 'current-password'
              }
              minLength={mode === 'register' ? 12 : undefined}
              maxLength={mode === 'register' ? 128 : undefined}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />

            <button type="submit" disabled={submitting}>
              {submitting
                ? 'Please wait...'
                : mode === 'login'
                  ? 'Sign In'
                  : 'Create Account'}
            </button>
          </form>

          <p>
            {mode === 'login'
              ? "Don't have an account?"
              : 'Already have an account?'}
          </p>

          <button
            type="button"
            className="secondary-button"
            disabled={submitting}
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError('')
              setMessage('')
              setPassword('')
            }}
          >
            {mode === 'login' ? 'Register' : 'Back to Login'}
          </button>
        </section>
      )}
    </main>
  )
}

export default App
