# YouTube AI Comment Guard - Makefile
# 開発・デプロイ用コマンド集

.PHONY: help dev-backend dev-frontend dev install-backend install-frontend install \
        build-backend build-frontend build deploy terraform-init terraform-plan terraform-apply \
        test lint clean

# デフォルト: ヘルプ表示
help:
	@echo "YouTube AI Comment Guard - 利用可能なコマンド"
	@echo ""
	@echo "開発:"
	@echo "  make install          - 全ての依存関係をインストール"
	@echo "  make dev              - バックエンド・フロントエンドを同時起動"
	@echo "  make dev-backend      - バックエンドのみ起動"
	@echo "  make dev-frontend     - フロントエンドのみ起動"
	@echo ""
	@echo "ビルド:"
	@echo "  make build            - Docker イメージをビルド"
	@echo "  make build-backend    - バックエンドのみビルド"
	@echo "  make build-frontend   - フロントエンドのみビルド"
	@echo ""
	@echo "デプロイ (Terraform):"
	@echo "  make terraform-init   - Terraform 初期化"
	@echo "  make terraform-plan   - デプロイ計画を確認"
	@echo "  make terraform-apply  - GCP にデプロイ"
	@echo ""
	@echo "テスト・品質:"
	@echo "  make test             - テスト実行"
	@echo "  make lint             - リント実行"
	@echo "  make clean            - キャッシュ・一時ファイル削除"

# ========================================
# 依存関係インストール
# ========================================

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend
	@echo "✅ 全ての依存関係をインストールしました"

# ========================================
# 開発サーバー
# ========================================

dev-backend:
	cd backend && uv run uvicorn youtube_guard.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# バックエンド・フロントエンド同時起動 (要: tmux or 別ターミナル推奨)
dev:
	@echo "📝 別ターミナルで以下を実行してください:"
	@echo "  Terminal 1: make dev-backend"
	@echo "  Terminal 2: make dev-frontend"
	@echo ""
	@echo "または tmux を使用:"
	@tmux new-session -d -s youtube-guard 'make dev-backend' \; split-window -h 'make dev-frontend' \; attach 2>/dev/null || \
		(echo "tmux がインストールされていません。別ターミナルで起動してください。")

# ========================================
# Docker ビルド
# ========================================

PROJECT_ID ?= your-project-id
REGION ?= asia-northeast1
BACKEND_IMAGE = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/youtube-guard/backend
FRONTEND_IMAGE = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/youtube-guard/frontend

build-backend:
	docker build -t $(BACKEND_IMAGE):latest backend/

build-frontend:
	docker build -t $(FRONTEND_IMAGE):latest frontend/

build: build-backend build-frontend
	@echo "✅ Docker イメージをビルドしました"

push-backend:
	docker push $(BACKEND_IMAGE):latest

push-frontend:
	docker push $(FRONTEND_IMAGE):latest

push: push-backend push-frontend
	@echo "✅ Docker イメージをプッシュしました"

# ========================================
# Terraform
# ========================================

terraform-init:
	cd terraform && terraform init

terraform-plan:
	cd terraform && terraform plan

terraform-apply:
	cd terraform && terraform apply

terraform-destroy:
	cd terraform && terraform destroy

# ========================================
# テスト・品質
# ========================================

test:
	cd backend && uv run pytest tests/ -v

lint:
	cd backend && uv run ruff check src/
	cd frontend && npm run lint

format:
	cd backend && uv run ruff format src/

# ========================================
# クリーンアップ
# ========================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.venv 2>/dev/null || true
	rm -rf frontend/node_modules 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	@echo "✅ キャッシュ・一時ファイルを削除しました"
