import { useAuth } from '../contexts/AuthContext'

/**
 * Landing page component displayed to unauthenticated users
 */
function LandingPage() {
  const { login } = useAuth()

  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="hero-content">
          <div className="hero-badge">🛡️ YouTubeクリエイター向け</div>
          <h1 className="hero-title">
            AI Comment Guard
            <span className="hero-subtitle">あなたのメンタルを守る、賢いコメント管理</span>
          </h1>
          <p className="hero-description">
            AIが有害なコメントを自動でフィルタリング。
            批判的なコメントも、建設的なフィードバックに変換。
            あなたが見るのは、ポジティブな意見と改善提案だけ。
          </p>
          <button className="login-button" onClick={login}>
            <svg className="google-icon" viewBox="0 0 24 24" width="24" height="24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Googleでログイン</span>
          </button>
        </div>
        <div className="hero-visual">
          <div className="hero-card">
            <div className="card-header">
              <span className="card-icon">📊</span>
              <span>ダッシュボード</span>
            </div>
            <div className="card-stats">
              <div className="stat">
                <span className="stat-value">156</span>
                <span className="stat-label">安全なコメント</span>
              </div>
              <div className="stat">
                <span className="stat-value">23</span>
                <span className="stat-label">フィルター済み</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="features-section">
        <h2 className="features-title">主な機能</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>AI分析</h3>
            <p>Gemini AIがコメントの有害度を自動判定。微妙なニュアンスも見逃しません。</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔄</div>
            <h3>解毒変換</h3>
            <p>攻撃的なコメントを事務的な報告形式に変換。感情的ダメージを軽減します。</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>ダッシュボード</h3>
            <p>ポジティブな意見と建設的なフィードバックだけを見やすく表示します。</p>
          </div>
        </div>
      </div>

      <footer className="landing-footer">
        <p>© 2026 YouTube AI Comment Guard</p>
      </footer>
    </div>
  )
}

export default LandingPage
