import { useState } from 'react'
import CommentCard from './CommentCard'
import ReplyModal from './ReplyModal'

/**
 * Dashboard component displaying categorized comments and statistics.
 * Mental protection: Only shows mild/transformed text, never raw toxic content.
 */
function Dashboard({ data, onRefresh }) {
  const [selectedComment, setSelectedComment] = useState(null)
  const { comments, stats } = data

  const handleReply = (comment) => {
    setSelectedComment(comment)
  }

  const handleCloseModal = () => {
    setSelectedComment(null)
  }

  const handleReplySubmit = async () => {
    setSelectedComment(null)
    await onRefresh()
  }

  return (
    <div className="dashboard">
      {/* Statistics */}
      <div className="stats-grid">
        <div className="stat-card positive">
          <span className="stat-label">💚 応援・感謝</span>
          <span className="stat-value">{stats.positive_count}</span>
          <span className="stat-sublabel">ポジティブなコメント</span>
        </div>
        <div className="stat-card question">
          <span className="stat-label">❓ 質問</span>
          <span className="stat-value">{stats.question_count}</span>
          <span className="stat-sublabel">返信をお待ちのコメント</span>
        </div>
        <div className="stat-card constructive">
          <span className="stat-label">💡 改善提案</span>
          <span className="stat-value">{stats.constructive_count}</span>
          <span className="stat-sublabel">建設的なフィードバック</span>
        </div>
        <div className="stat-card blocked">
          <span className="stat-label">🚫 ブロック済み</span>
          <span className="stat-value">{stats.blocked_count}</span>
          <span className="stat-sublabel">確認不要（自動処理済み）</span>
        </div>
      </div>

      {/* Comment Sections */}
      <div className="comment-sections">
        {/* Positive Comments */}
        <section className="comment-section">
          <div className="section-header positive">
            <span className="section-icon">💚</span>
            <span className="section-title">応援・感謝のコメント</span>
            <span className="section-count">{comments.positive?.length || 0}</span>
          </div>
          <div className="section-content">
            {comments.positive?.length > 0 ? (
              comments.positive.map((comment) => (
                <CommentCard
                  key={comment.id}
                  comment={comment}
                  onReply={handleReply}
                />
              ))
            ) : (
              <div className="empty-state">まだコメントがありません</div>
            )}
          </div>
        </section>

        {/* Questions */}
        <section className="comment-section">
          <div className="section-header question">
            <span className="section-icon">❓</span>
            <span className="section-title">質問</span>
            <span className="section-count">{comments.questions?.length || 0}</span>
          </div>
          <div className="section-content">
            {comments.questions?.length > 0 ? (
              comments.questions.map((comment) => (
                <CommentCard
                  key={comment.id}
                  comment={comment}
                  onReply={handleReply}
                  showReplyButton
                />
              ))
            ) : (
              <div className="empty-state">質問はありません</div>
            )}
          </div>
        </section>

        {/* Constructive Feedback */}
        <section className="comment-section">
          <div className="section-header constructive">
            <span className="section-icon">💡</span>
            <span className="section-title">改善提案</span>
            <span className="section-count">{comments.constructive?.length || 0}</span>
          </div>
          <div className="section-content">
            {comments.constructive?.length > 0 ? (
              comments.constructive.map((comment) => (
                <CommentCard
                  key={comment.id}
                  comment={comment}
                  onReply={handleReply}
                  showReplyButton
                />
              ))
            ) : (
              <div className="empty-state">改善提案はありません</div>
            )}
          </div>
        </section>
      </div>

      {/* Blocked Notice - Count only, no content shown */}
      {stats.blocked_count > 0 && (
        <div className="blocked-notice">
          <div className="blocked-count">{stats.blocked_count}</div>
          <div className="blocked-label">件の不適切なコメントを自動ブロックしました</div>
          <div className="blocked-message">
            🛡️ これらのコメントは自動的に非表示にされました。内容を確認する必要はありません。
          </div>
        </div>
      )}

      {/* Reply Modal */}
      {selectedComment && (
        <ReplyModal
          comment={selectedComment}
          onClose={handleCloseModal}
          onSubmit={handleReplySubmit}
        />
      )}
    </div>
  )
}

export default Dashboard
