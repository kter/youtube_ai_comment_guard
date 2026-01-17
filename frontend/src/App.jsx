import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import Header from './components/Header'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/comments/summary`)
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
      await fetch(`${API_BASE_URL}/api/comments/sync`, { method: 'POST' })
      await fetchData()
    } catch (err) {
      setError(err.message)
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <Header onSync={handleSync} syncing={syncing} />
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

export default App
