# GCPデプロイ手順

## 前提条件

### 1. GCPプロジェクト準備
```bash
# 新規プロジェクト作成
gcloud projects create your-disaster-response-project

# プロジェクト設定
gcloud config set project your-disaster-response-project

# 課金アカウント設定
gcloud billing projects link your-disaster-response-project \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 2. 必要なAPIを有効化
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  bigquery.googleapis.com
```

### 3. 認証設定
```bash
# ADC設定
gcloud auth application-default login

# Docker認証
gcloud auth configure-docker
```

## デプロイ方法

### Option 1: 自動デプロイスクリプト (推奨)

```bash
# 環境変数設定
export GOOGLE_CLOUD_PROJECT=your-disaster-response-project
export GOOGLE_CLOUD_REGION=asia-northeast1

# デプロイ実行
./scripts/deploy.sh
```

### Option 2: 手動デプロイ

#### Step 1: Terraformでインフラ構築
```bash
cd infrastructure/environments/dev

# Terraform初期化
terraform init

# プラン確認
terraform plan \
  -var="project_id=$GOOGLE_CLOUD_PROJECT" \
  -var="region=$GOOGLE_CLOUD_REGION"

# インフラ作成
terraform apply \
  -var="project_id=$GOOGLE_CLOUD_PROJECT" \
  -var="region=$GOOGLE_CLOUD_REGION" \
  -auto-approve
```

#### Step 2: コンテナイメージビルド・プッシュ
```bash
cd ../../..

# 各エージェントのビルド
AGENTS=("detection" "orchestrator" "info_collector" "analyzer" "pr")

for agent in "${AGENTS[@]}"; do
  echo "Building $agent agent..."
  
  docker build -t "gcr.io/$GOOGLE_CLOUD_PROJECT/$agent-agent:latest" \
    "agents/$agent/"
  
  docker push "gcr.io/$GOOGLE_CLOUD_PROJECT/$agent-agent:latest"
done
```

#### Step 3: Cloud Runサービス更新
```bash
# サービス一覧確認
gcloud run services list --region=$GOOGLE_CLOUD_REGION

# イメージ更新 (Terraformで自動実行済みの場合は不要)
gcloud run services update orchestrator-agent \
  --image=gcr.io/$GOOGLE_CLOUD_PROJECT/orchestrator-agent:latest \
  --region=$GOOGLE_CLOUD_REGION
```

## デプロイ後の確認

### 1. サービス状態確認
```bash
# Cloud Runサービス一覧
gcloud run services list --region=$GOOGLE_CLOUD_REGION

# Pub/Subトピック確認
gcloud pubsub topics list

# Firestoreコレクション確認 (Web Console)
```

### 2. エンドポイントテスト
```bash
# サービスURL取得
ORCHESTRATOR_URL=$(gcloud run services describe orchestrator-agent \
  --region=$GOOGLE_CLOUD_REGION \
  --format="value(status.url)")

# ヘルスチェック
curl $ORCHESTRATOR_URL/health

# 手動災害イベント発生
curl -X POST $ORCHESTRATOR_URL/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -d '{
    "event_id": "test-deploy-001",
    "detected_at": "2025-01-15T10:00:00Z",
    "source": ["manual"],
    "type": "earthquake",
    "location": {"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
    "severity": 0.6,
    "confidence": 0.8,
    "summary": "デプロイテスト用地震イベント",
    "evidence": []
  }'
```

### 3. ログ・監視確認
```bash
# Cloud Runログ確認
gcloud logs read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"

# Pub/Subメッセージ確認
gcloud pubsub subscriptions pull disaster-detected-subscription \
  --limit=5 \
  --auto-ack
```

## トラブルシューティング

### 権限エラー
```bash
# IAM権限確認
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# サービスアカウント確認
gcloud iam service-accounts list
```

### イメージビルドエラー
```bash
# Cloud Build履歴確認
gcloud builds list --limit=5

# ローカルビルドテスト
docker build -t test-image agents/detection/
```

### 接続エラー
```bash
# VPCコネクタ確認
gcloud compute networks vpc-access connectors list

# セキュリティ設定確認
gcloud run services get-iam-policy SERVICE_NAME --region=$REGION
```

## 本番環境への展開

### 1. 本番環境用設定
```bash
# 本番環境Terraform
cd infrastructure/environments/prod

# 環境変数設定
export GOOGLE_CLOUD_PROJECT=your-prod-project
export TF_VAR_environment=prod
```

### 2. CI/CDパイプライン (Cloud Build)
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/orchestrator-agent:$BUILD_ID', 'agents/orchestrator/']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/orchestrator-agent:$BUILD_ID']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'orchestrator-agent', 
         '--image', 'gcr.io/$PROJECT_ID/orchestrator-agent:$BUILD_ID',
         '--region', 'asia-northeast1']
```

### 3. 本番監視設定
```bash
# アラート設定
gcloud alpha monitoring policies create --policy-from-file=monitoring/alerts.yaml

# ダッシュボード作成
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json
```

## 定期メンテナンス

### 1. ログ監視
```bash
# エラーログ確認
gcloud logging read "severity>=ERROR" --limit=20

# パフォーマンス確認  
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com"
```

### 2. コスト監視
```bash
# 課金状況確認
gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT

# リソース使用量確認
gcloud monitoring timeseries list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"'
```