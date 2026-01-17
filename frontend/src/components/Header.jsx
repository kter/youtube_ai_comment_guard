/**
 * Header component with logo and sync button
 */
function Header({ onSync, syncing }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <span className="logo-icon">🛡️</span>
          <h1>YouTube AI Comment Guard</h1>
        </div>
        <button
          className={`sync-button ${syncing ? 'syncing' : ''}`}
          onClick={onSync}
          disabled={syncing}
        >
          <span className="sync-icon">🔄</span>
          <span>{syncing ? '同期中...' : 'コメントを同期'}</span>
        </button>
      </div>
    </header>
  )
}

export default Header
