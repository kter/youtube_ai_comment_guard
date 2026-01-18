import { useAuth } from '../contexts/AuthContext'

/**
 * Header component with logo, sync button, and user menu
 */
function Header({ onSync, syncing, user }) {
  const { logout } = useAuth()

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <span className="logo-icon">🛡️</span>
          <h1>YouTube AI Comment Guard</h1>
        </div>
        <div className="header-actions">
          <button
            className={`sync-button ${syncing ? 'syncing' : ''}`}
            onClick={onSync}
            disabled={syncing}
          >
            <span className="sync-icon">🔄</span>
            <span>{syncing ? '同期中...' : 'コメントを同期'}</span>
          </button>
          {user && (
            <div className="user-menu">
              {user.picture && (
                <img 
                  src={user.picture} 
                  alt={user.name} 
                  className="user-avatar"
                />
              )}
              <span className="user-name">{user.name}</span>
              <button className="logout-button" onClick={logout}>
                ログアウト
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default Header
