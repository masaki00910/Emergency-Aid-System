# Firebase本番環境デプロイ手順書

## 📋 事前準備

### 1. 環境変数設定
```bash
export GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2
export GOOGLE_CLOUD_REGION=asia-northeast1
```

### 2. 必要なAPI有効化確認
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

### 3. 認証設定
```bash
gcloud auth application-default login
gcloud auth configure-docker
```

---

## 🚀 デプロイ手順

### A. フロントエンド (Next.js) デプロイ

#### 1. Vercelデプロイ (推奨)
```bash
cd /Users/hiroki/Emergency-Aid-System/web

# Vercel CLIインストール (未インストールの場合)
npm install -g vercel

# デプロイ実行
vercel

# 本番デプロイ
vercel --prod
```

#### 2. Firebase Hostingデプロイ (代替案)
```bash
cd /Users/hiroki/Emergency-Aid-System/web

# Firebase CLIインストール
npm install -g firebase-tools

# Firebase初期化 (初回のみ)
firebase init hosting

# ビルド
npm run build

# デプロイ
firebase deploy --only hosting
```

#### 3. Cloud Run デプロイ (コンテナ化)
```bash
cd /Users/hiroki/Emergency-Aid-System/web

# Dockerfileがない場合は作成
cat > Dockerfile << 'EOF'
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
EOF

# ビルド・プッシュ
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-frontend:latest .
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-frontend:latest

# デプロイ
gcloud run deploy disaster-frontend \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-frontend:latest \
  --platform managed \
  --region $GOOGLE_CLOUD_REGION \
  --allow-unauthenticated
```

### B. バックエンド (API Gateway) デプロイ

#### 1. minimal_faq_server.py をCloud Runにデプロイ
```bash
cd /Users/hiroki/Emergency-Aid-System/api_gateway

# Dockerfileを作成
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# 共有モジュールのパスを設定
ENV PYTHONPATH=/app:/app/..

# ポート設定
EXPOSE 8082

# エントリーポイント
CMD ["python3", "minimal_faq_server.py"]
EOF

# ビルド・プッシュ
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-api:latest .
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-api:latest

# デプロイ
gcloud run deploy disaster-api \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/disaster-api:latest \
  --platform managed \
  --region $GOOGLE_CLOUD_REGION \
  --allow-unauthenticated \
  --port 8082 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,USE_MOCK_LLM=false"
```

#### 2. 既存のマルチエージェントシステムデプロイ
```bash
cd /Users/hiroki/Emergency-Aid-System

# 自動デプロイスクリプト実行
./scripts/deploy.sh
```

---

## 🔧 本番環境設定

### 1. API URLの更新 (フロントエンド)
```bash
cd /Users/hiroki/Emergency-Aid-System/web/src/lib

# api.tsのbaseURLを本番URLに更新
# ローカル: http://localhost:8082
# 本番: https://disaster-api-[hash]-an.a.run.app
```

### 2. CORS設定の更新 (バックエンド)
```bash
# minimal_faq_server.pyまたは該当APIサーバーで
# フロントエンドの本番URLをCORS設定に追加
```

### 3. 環境変数・シークレット設定
```bash
# Service Account Key をSecret Managerに保存
gcloud secrets create service-account-key \
  --data-file=/Users/hiroki/Emergency-Aid-System/keys/service-account-key.json

# Cloud Run サービスに環境変数設定
gcloud run services update disaster-api \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
  --region $GOOGLE_CLOUD_REGION
```

---

## 🧪 デプロイ後の動作確認手順

### 1. バックエンドAPI確認
```bash
# デプロイされたAPIのURL取得
API_URL=$(gcloud run services describe disaster-api \
  --region=$GOOGLE_CLOUD_REGION \
  --format="value(status.url)")

echo "API URL: $API_URL"

# ヘルスチェック
curl $API_URL/

# 災害データ確認
curl $API_URL/api/public/disasters | jq

# アラート確認
curl $API_URL/api/alerts | jq

# FAQ機能テスト
curl -X POST $API_URL/api/public/faq/test-disaster/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "災害時の基本的な対応を教えてください"}' | jq
```

### 2. フロントエンド確認
```bash
# デプロイされたフロントエンドURL取得
FRONTEND_URL=$(gcloud run services describe disaster-frontend \
  --region=$GOOGLE_CLOUD_REGION \
  --format="value(status.url)")

echo "Frontend URL: $FRONTEND_URL"

# ブラウザで確認するポイント:
echo "1. $FRONTEND_URL でダッシュボードが表示されること"
echo "2. $FRONTEND_URL/alerts でアラート一覧が表示されること" 
echo "3. $FRONTEND_URL/alerts/alert-1 でFAQ機能が動作すること"
```

### 3. 画面上での確認手順

#### ダッシュボードページ
1. **URL**: `https://your-frontend-url.com/dashboard`
2. **確認項目**:
   - 災害データが表示されている
   - マップにマーカーが表示されている
   - アラート件数が正しく表示されている

#### アラート一覧ページ
1. **URL**: `https://your-frontend-url.com/alerts`
2. **確認項目**:
   - アラート一覧が表示されている
   - 各アラートの詳細リンクが機能している

#### FAQ機能確認
1. **URL**: `https://your-frontend-url.com/alerts/alert-1`
2. **確認項目**:
   - FAQチャット画面が表示されている
   - 質問を入力して送信できる
   - **重要**: レスポンスが実際のVertex AI（Gemini 2.5）から返されている
   - `model_used: "gemini-2.5-flash"` がレスポンスに含まれている

#### Vertex AI機能確認
```bash
# ブラウザのデベロッパーツールのNetworkタブで確認
# FAQ質問送信時のレスポンスで以下を確認:
{
  "question": "災害時の対応は？",
  "answer": "[実際のAI生成回答]",
  "model_used": "gemini-2.5-flash",
  "timestamp": "..."
}
```

---

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. CORS エラー
```bash
# バックエンドのCORS設定確認
# Access-Control-Allow-Origin ヘッダーがフロントエンドURLを含んでいるか確認
```

#### 2. API接続エラー
```bash
# フロントエンドのapi.tsでbaseURLが正しいか確認
# ネットワークタブでAPIコールのレスポンスを確認
```

#### 3. Vertex AI認証エラー
```bash
# Cloud Run の環境変数確認
gcloud run services describe disaster-api \
  --region=$GOOGLE_CLOUD_REGION \
  --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"

# ログ確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=disaster-api" \
  --limit=50
```

#### 4. ビルドエラー
```bash
# Next.js ビルドエラーの場合
cd /Users/hiroki/Emergency-Aid-System/web
npm run build  # ローカルでビルド確認

# Docker ビルドエラーの場合
docker build --no-cache -t test-image .
```

---

## 📊 監視・運用

### デプロイ後の継続監視
```bash
# リアルタイムログ監視
gcloud logs tail "resource.type=cloud_run_revision"

# エラーログ抽出
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20

# パフォーマンス監視
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com"
```

---

## 📝 重要な注意事項

### セキュリティ
- Service Account Key は Secret Manager を使用して管理
- Cloud Run サービスには必要最小限の権限のみ付与
- 本番環境では認証付きエンドポイントの使用を検討

### パフォーマンス
- Vertex AI のレート制限に注意
- Cloud Run のコールドスタート時間を考慮
- 必要に応じてCloud CDNの使用を検討

### コスト最適化
- Cloud Run のコンカレンシー設定を調整
- 不要なサービスのスケールダウン
- リソース使用量の定期監視

この手順書に従って本番環境デプロイを実行し、特にFAQ機能でのVertex AI（Gemini 2.5）統合が正常に動作することを確認してください。