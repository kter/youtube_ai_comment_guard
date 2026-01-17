# YouTube AI Comment Guard

YouTubeクリエイターのメンタルヘルスを守るための、コメント自動管理・要約システム。

## 機能

- 🛡️ **フィルタリング**: 攻撃的なコメントを自動で非表示/保留
- 🔄 **解毒変換**: 批判的コメントを事務的な報告形式に変換
- 📊 **ダッシュボード**: ポジティブな意見と改善提案のみを表示

## 技術スタック

- **Backend**: Python (FastAPI) + uv
- **Frontend**: React (Vite)
- **AI**: Vertex AI (Gemini 1.5 Flash)
- **Database**: Firestore
- **Infrastructure**: Terraform, Cloud Run, Cloud Scheduler

## セットアップ

### 開発環境

1. VSCode + Dev Containersを使用してコンテナを起動
2. バックエンド起動:
   ```bash
   cd backend
   uv run uvicorn src.youtube_guard.main:app --reload
   ```
3. フロントエンド起動:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### デプロイ

```bash
cd terraform
terraform init
terraform apply
```

## 環境変数

- `GOOGLE_CLOUD_PROJECT`: GCPプロジェクトID
- `YOUTUBE_CLIENT_ID`: YouTube OAuth Client ID
- `YOUTUBE_CLIENT_SECRET`: YouTube OAuth Client Secret
# youtube_ai_comment_guard
