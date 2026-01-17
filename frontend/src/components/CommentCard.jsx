/**
 * Comment card component displaying a single processed comment.
 * Only shows mild_text (transformed/neutralized version), never the original toxic content.
 */
function CommentCard({ comment, onReply, showReplyButton = false }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="comment-card">
      <div className="comment-header">
        <span className="comment-author">{comment.author_name}</span>
        {comment.needs_reply && (
          <span className="needs-reply-badge">📝 返信待ち</span>
        )}
        <span className="comment-date">{formatDate(comment.published_at)}</span>
      </div>
      {/* Always show mild_text, never original_text */}
      <p className="comment-text">{comment.mild_text}</p>
      {(showReplyButton || comment.needs_reply) && (
        <div className="comment-actions">
          <button className="reply-button" onClick={() => onReply(comment)}>
            ✉️ 返信する
          </button>
        </div>
      )}
    </div>
  )
}

export default CommentCard
