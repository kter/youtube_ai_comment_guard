import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import LandingPage from './components/LandingPage'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

function AppContent() {
  const { user, loading: authLoading, isAuthenticated } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)

  const fetchData = async () => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }
    
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/comments/summary`, {
        credentials: 'include',
      })
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    try {
      setSyncing(true)
      await fetch(`${API_BASE_URL}/api/comments/sync`, { 
        method: 'POST',
        credentials: 'include',
      })
      await fetchData()
    } catch (err) {
      setError(err.message)
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchData()
      // Refresh every 5 minutes
      const interval = setInterval(fetchData, 5 * 60 * 1000)
      return () => clearInterval(interval)
    }
  }, [isAuthenticated])

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>認証確認中...</p>
        </div>
      </div>
    )
  }

  // Show landing page for unauthenticated users
  if (!isAuthenticated) {
    return <LandingPage />
  }

  // Show dashboard for authenticated users
  return (
    <div className="app">
      <Header onSync={handleSync} syncing={syncing} user={user} />
      <main className="main-content">
        {loading && !data && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>読み込み中...</p>
          </div>
        )}
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
            <button onClick={fetchData} className="retry-button">再試行</button>
          </div>
        )}
        {data && <Dashboard data={data} onRefresh={fetchData} />}
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
