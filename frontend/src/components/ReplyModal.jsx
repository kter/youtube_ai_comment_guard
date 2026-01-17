import { useState } from 'react'

/**
 * Reply modal for composing and sending replies to comments.
 * Shows mild_text of original comment for context.
 * Supports AI-generated reply suggestions.
 */
function ReplyModal({ comment, onClose, onSubmit }) {
  const [replyText, setReplyText] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggesting, setSuggesting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!replyText.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/comments/${comment.id}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          comment_id: comment.id,
          text: replyText,
        }),
      })

      if (!response.ok) {
        throw new Error('返信の投稿に失敗しました')
      }

      await onSubmit()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSuggest = async () => {
    setSuggesting(true)
    setError(null)

    try {
      const response = await fetch(`/api/comments/${comment.id}/suggest-reply`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('提案の取得に失敗しました')
      }

      const data = await response.json()
      if (data.suggestion) {
        setReplyText(data.suggestion)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSuggesting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">返信を作成</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {/* Show only the mild/transformed text, not original */}
          <div className="original-comment">
            <div className="original-label">コメント内容（要約）</div>
            <p className="original-text">{comment.mild_text}</p>
          </div>

          <textarea
            className="reply-textarea"
            placeholder="返信を入力..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            disabled={loading}
          />

          <button
            className="suggestion-button"
            onClick={handleSuggest}
            disabled={suggesting}
          >
            {suggesting ? '✨ 提案を生成中...' : '✨ AIに返信を提案してもらう'}
          </button>

          {error && (
            <div className="error-banner" style={{ marginTop: '1rem' }}>
              <span>⚠️ {error}</span>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="cancel-button" onClick={onClose}>
            キャンセル
          </button>
          <button
            className="submit-button"
            onClick={handleSubmit}
            disabled={loading || !replyText.trim()}
          >
            {loading ? '投稿中...' : '返信を投稿'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReplyModal
