import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ReplyModal from '../ReplyModal';

describe('ReplyModal', () => {
  const mockComment = {
    id: 'c1',
    mild_text: 'Hello world',
  };
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders correctly with mild text', () => {
    render(
      <ReplyModal
        comment={mockComment}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('返信を作成')).toBeInTheDocument();
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('handles manual input and submission', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    render(
      <ReplyModal
        comment={mockComment}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const textarea = screen.getByPlaceholderText('返信を入力...');
    fireEvent.change(textarea, { target: { value: 'My reply' } });
    
    // Submit button should be enabled
    const submitBtn = screen.getByText('返信を投稿');
    expect(submitBtn).toBeEnabled();
    
    fireEvent.click(submitBtn);

    expect(screen.getByText('投稿中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/comments/c1/reply',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ comment_id: 'c1', text: 'My reply' }),
        })
      );
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });

  it('handles AI suggestion', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: 'AI Suggested Reply' }),
    });

    render(
      <ReplyModal
        comment={mockComment}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const suggestBtn = screen.getByText('✨ AIに返信を提案してもらう');
    fireEvent.click(suggestBtn);

    expect(screen.getByText('✨ 提案を生成中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/comments/c1/suggest-reply',
        expect.objectContaining({ method: 'POST' })
      );
    });
    
    const textarea = screen.getByDisplayValue('AI Suggested Reply');
    expect(textarea).toBeInTheDocument();
  });
});
