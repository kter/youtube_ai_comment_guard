# YouTube AI Comment Guard - Makefile
# 開発・デプロイ用コマンド集

.PHONY: help dev-backend dev-frontend dev install-backend install-frontend install \
        build-backend build-frontend build push-backend push deploy-frontend-dev deploy-frontend-prd \
        terraform-setup terraform-init terraform-workspace-new terraform-workspace terraform-plan terraform-apply terraform-destroy \
        invalidate-cache-dev invalidate-cache-prd test lint clean

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
	@echo "  make build            - バックエンド Docker イメージをビルド"
	@echo "  make build-backend    - バックエンドのみビルド"
	@echo "  make build-frontend   - フロントエンドをビルド (Vite)"
	@echo ""
	@echo "デプロイ (Terraform):"
	@echo "  make terraform-setup          - tfenv で Terraform をセットアップ"
	@echo "  make terraform-init           - Terraform 初期化"
	@echo "  make terraform-workspace-new  - ワークスペース作成 (ENV=dev|prd)"
	@echo "  make terraform-plan ENV=dev   - デプロイ計画を確認"
	@echo "  make terraform-apply ENV=prd  - インフラをデプロイ"
	@echo ""
	@echo "フロントエンドデプロイ (AWS S3 + CloudFront):"
	@echo "  make deploy-frontend-dev      - Dev環境へフロントエンドをデプロイ"
	@echo "  make deploy-frontend-prd      - Prd環境へフロントエンドをデプロイ"
	@echo "  make invalidate-cache-dev     - DevのCloudFrontキャッシュを無効化"
	@echo "  make invalidate-cache-prd     - PrdのCloudFrontキャッシュを無効化"
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
# Docker ビルド (Backend only - Frontend is hosted on S3)
# ========================================

PROJECT_ID ?= your-project-id
REGION ?= asia-northeast1
BACKEND_IMAGE = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/youtube-guard/backend

build-backend:
	docker build --platform linux/amd64 -t $(BACKEND_IMAGE):latest backend/

build: build-backend
	@echo "✅ Docker イメージをビルドしました"

push-backend:
	docker push $(BACKEND_IMAGE):latest

push: push-backend
	@echo "✅ Docker イメージをプッシュしました"

# ========================================
# Terraform
# ========================================

ENV ?= dev

# tfenv でバージョンをインストール・切り替え
terraform-setup:
	@command -v tfenv >/dev/null 2>&1 || (echo "❌ tfenv がインストールされていません: brew install tfenv" && exit 1)
	cd terraform && tfenv install && tfenv use
	@echo "✅ Terraform $(shell cat terraform/.terraform-version) をセットアップしました"

terraform-init:
	cd terraform && terraform init

# ワークスペース作成（存在しない場合のみ）
terraform-workspace-new:
	cd terraform && terraform workspace new $(ENV) 2>/dev/null || true

# ワークスペース切り替え
terraform-workspace:
	cd terraform && terraform workspace select $(ENV)
	@echo "✅ ワークスペース $(ENV) に切り替えました"

terraform-plan: terraform-workspace
	cd terraform && terraform plan

terraform-apply: terraform-workspace
	cd terraform && terraform apply

terraform-destroy: terraform-workspace
	cd terraform && terraform destroy

# ========================================
# AWS Frontend Deployment
# ========================================

# S3 バケット名とCloudFront Distribution ID を取得
S3_BUCKET_DEV = youtube-guard-frontend-dev
S3_BUCKET_PRD = youtube-guard-frontend-prd
CF_DISTRIBUTION_DEV = $(shell cd terraform && terraform workspace select dev >/dev/null 2>&1 && terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
CF_DISTRIBUTION_PRD = $(shell cd terraform && terraform workspace select prd >/dev/null 2>&1 && terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")

# フロントエンドビルド
BACKEND_URL_DEV = $(shell cd terraform && terraform workspace select dev >/dev/null 2>&1 && terraform output -raw backend_url 2>/dev/null || echo "")
BACKEND_URL_PRD = $(shell cd terraform && terraform workspace select prd >/dev/null 2>&1 && terraform output -raw backend_url 2>/dev/null || echo "")

build-frontend:
	@if [ -z "$(VITE_API_URL)" ]; then \
		echo "⚠️ VITE_API_URL is not set. Trying to fetch from Terraform..."; \
		if [ "$(ENV)" = "prd" ]; then \
			export VITE_API_URL=$(BACKEND_URL_PRD); \
		else \
			export VITE_API_URL=$(BACKEND_URL_DEV); \
		fi; \
	fi
	@echo "ℹ️ Using API URL: $$VITE_API_URL"
	@echo "ℹ️ Building for $(ENV) environment"
	@if [ "$(ENV)" = "prd" ]; then \
		cd frontend && VITE_API_URL=$$VITE_API_URL npm run build:prd; \
	else \
		cd frontend && VITE_API_URL=$$VITE_API_URL npm run build:dev; \
	fi
	@echo "✅ フロントエンドをビルドしました ($(ENV))"

# Dev環境へデプロイ
deploy-frontend-dev: build-frontend
	@echo "📤 Dev環境へフロントエンドをデプロイ中..."
	aws s3 sync frontend/dist/ s3://$(S3_BUCKET_DEV)/ --delete --profile dev
	@if [ -n "$(CF_DISTRIBUTION_DEV)" ]; then \
		echo "🔄 CloudFrontキャッシュを無効化中..."; \
		aws cloudfront create-invalidation --distribution-id $(CF_DISTRIBUTION_DEV) --paths "/*" --profile dev; \
	fi
	@echo "✅ Dev環境へデプロイ完了: https://youtube-comment-guard.dev.devtools.site"

# Prd環境へデプロイ
deploy-frontend-prd: build-frontend
	@echo "📤 Prd環境へフロントエンドをデプロイ中..."
	aws s3 sync frontend/dist/ s3://$(S3_BUCKET_PRD)/ --delete --profile prd
	@if [ -n "$(CF_DISTRIBUTION_PRD)" ]; then \
		echo "🔄 CloudFrontキャッシュを無効化中..."; \
		aws cloudfront create-invalidation --distribution-id $(CF_DISTRIBUTION_PRD) --paths "/*" --profile prd; \
	fi
	@echo "✅ Prd環境へデプロイ完了: https://youtube-comment-guard.devtools.site"

# CloudFrontキャッシュ無効化のみ
invalidate-cache-dev:
	aws cloudfront create-invalidation --distribution-id $(CF_DISTRIBUTION_DEV) --paths "/*" --profile dev
	@echo "✅ Devキャッシュを無効化しました"

invalidate-cache-prd:
	aws cloudfront create-invalidation --distribution-id $(CF_DISTRIBUTION_PRD) --paths "/*" --profile prd
	@echo "✅ Prdキャッシュを無効化しました"

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

