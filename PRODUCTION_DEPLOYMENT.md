# 本番環境デプロイ手順

## 前提条件

- GCPプロジェクト作成済み
- gcloud CLI認証済み (`gcloud auth login`)
- 必要なGCP API有効化済み
  - Cloud Run API
  - Cloud Build API  
  - Firestore API
  - Vertex AI API
  - Pub/Sub API

## 環境変数設定

```bash
export GOOGLE_CLOUD_PROJECT="sharelabai-hackathon2"
export GOOGLE_CLOUD_REGION="asia-northeast1"
```

## デプロイ方法

### オプション1: Cloud Build自動デプロイ（推奨）

1. **Cloud Build トリガー設定**
   ```bash
   # Google Cloud Consoleでトリガー作成
   # URL: https://console.cloud.google.com/cloud-build/triggers
   ```

2. **トリガー設定内容**
   - 名前: `deploy-disaster-api-production`
   - イベント: プッシュ時にブランチ
   - ソース: `github_masaki00910_emergency-aid-system`
   - ブランチ: `main`
   - 構成ファイル: `/cloudbuild.yaml`

3. **自動デプロイ実行**
   ```bash
   git push origin main
   ```

### オプション2: 手動デプロイ

1. **各エージェントのデプロイ**
   ```bash
   # API Gateway
   gcloud run deploy disaster-api \
     --source ./api_gateway \
     --region $GOOGLE_CLOUD_REGION \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,USE_MOCK_LLM=false

   # 災害検知Agent
   gcloud run deploy detection-agent \
     --source ./agents/detection \
     --region $GOOGLE_CLOUD_REGION \
     --platform managed \
     --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT

   # オーケストレータAgent
   gcloud run deploy orchestrator-agent \
     --source ./agents/orchestrator \
     --region $GOOGLE_CLOUD_REGION \
     --platform managed \
     --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT
   ```

2. **フロントエンドデプロイ**
   ```bash
   cd web
   npm run build
   
   # Firebase Hostingにデプロイ
   npm install -g firebase-tools
   firebase login
   firebase deploy --only hosting
   ```

## 本番環境設定

### 1. 環境変数設定

本番環境では以下の環境変数を設定：

```bash
GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2
GOOGLE_CLOUD_REGION=asia-northeast1
USE_MOCK_LLM=false
NODE_ENV=production
```

### 2. IAM権限設定

各Cloud Runサービスに必要な権限を付与：

```bash
# Cloud Runサービスアカウントに権限付与
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/firestore.user"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"
```

### 3. Firestore設定

```bash
# Firestoreネイティブモードを有効化（未設定の場合）
gcloud firestore databases create --region=$GOOGLE_CLOUD_REGION
```

## デプロイ後の確認

### 1. ヘルスチェック

```bash
# API Gateway
curl https://disaster-api-670435464520.asia-northeast1.run.app/health

# 各エージェント
curl https://detection-agent-670435464520.asia-northeast1.run.app/health
curl https://orchestrator-agent-670435464520.asia-northeast1.run.app/health
```

### 2. 機能確認

```bash
# 災害情報取得
curl https://disaster-api-670435464520.asia-northeast1.run.app/api/public/disasters

# FAQ機能
curl -X POST "https://disaster-api-670435464520.asia-northeast1.run.app/api/public/faq/sample-disaster-1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "避難のタイミングは？"}'
```

### 3. フロントエンド確認

1. Firebase Hosting URLにアクセス
2. APIとの接続確認
3. 全機能の動作確認

## 監視・運用

### 1. ログ監視

```bash
# Cloud Runのログ確認
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# 特定サービスのログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=disaster-api" --limit=50
```

### 2. メトリクス監視

Google Cloud Monitoringで以下を監視：
- CPU使用率
- メモリ使用率
- リクエスト数
- エラー率
- レスポンス時間

### 3. アラート設定

```bash
# エラー率アラート設定例
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring-policy.yaml
```

## セキュリティ設定

### 1. IAM最小権限

各サービスに必要最小限の権限のみ付与

### 2. VPC設定（オプション）

```bash
# Private Google Accessを有効化してインターネットアクセス制限
gcloud compute networks subnets update SUBNET_NAME \
  --region=$GOOGLE_CLOUD_REGION \
  --enable-private-ip-google-access
```

### 3. Secret Manager

機密情報はSecret Managerで管理：

```bash
# シークレット作成
gcloud secrets create api-key --data-file=api-key.txt

# Cloud Runからアクセス権限付与
gcloud secrets add-iam-policy-binding api-key \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

## バックアップ・復旧

### 1. Firestoreバックアップ

```bash
# 定期バックアップ設定
gcloud firestore operations list
```

### 2. ソースコードバックアップ

GitHubリポジトリが主要なバックアップ

## トラブルシューティング

### 1. デプロイエラー

```bash
# Cloud Buildログ確認
gcloud builds list --limit=10
gcloud builds log BUILD_ID
```

### 2. サービス接続エラー

```bash
# Cloud Runサービス確認
gcloud run services list
gcloud run services describe SERVICE_NAME --region=$GOOGLE_CLOUD_REGION
```

### 3. パフォーマンス問題

```bash
# インスタンス数調整
gcloud run services update SERVICE_NAME \
  --region=$GOOGLE_CLOUD_REGION \
  --max-instances=10 \
  --concurrency=100
```

## コスト最適化

1. **自動スケーリング**: 負荷に応じたインスタンス数調整
2. **リソース制限**: CPU・メモリの適切な設定
3. **リージョン選択**: 最も近いリージョンを使用
4. **不要サービス停止**: 使用していないサービスの削除