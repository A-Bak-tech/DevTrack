
import { useEffect, useState } from 'react'
import { getBackendHealth } from './api/health'
import './App.css'

type ConnectionStatus = 'checking' | 'connected' | 'error'

function App() {
  const [status, setStatus] =
    useState<ConnectionStatus>('checking')
  const [service, setService] = useState('')

  useEffect(() => {
    let active = true

    async function checkBackend() {
      try {
        const data = await getBackendHealth()

        if (!active) return

        if (data.status !== 'healthy') {
          throw new Error('Backend reported an unhealthy status')
        }

        setService(data.service)
        setStatus('connected')
      } catch {
        if (active) {
          setStatus('error')
        }
      }
    }

    void checkBackend()

    return () => {
      active = false
    }
  }, [])

  return (
    <main className="container">
      <h1>DevTrack</h1>
      <p>Software Development Management Platform</p>

      <section className="status-card">
        <h2>Backend Connection</h2>

        {status === 'checking' && (
          <p role="status">Checking backend connection...</p>
        )}

        {status === 'connected' && (
          <p role="status">
            Connected successfully to {service}
          </p>
        )}

        {status === 'error' && (
          <p role="alert">
            Unable to connect to the backend.
          </p>
        )}
      </section>
    </main>
  )
}

export default App
