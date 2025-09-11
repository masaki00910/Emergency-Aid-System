# Quick Build & Deploy Guide

## 修正されたビルド手順

### 1. 各エージェントの正しいDockerfileでビルド

```bash
# Orchestrator Agent (プロジェクトルートのDockerfile使用)
gcloud builds submit --tag gcr.io/sharelabai-hackathon2/orchestrator-agent:latest .

# Info Collector Agent (専用config使用)
gcloud builds submit --config cloudbuild-info-collector.yaml

# Analyzer Agent (専用config使用)  
gcloud builds submit --config cloudbuild-analyzer.yaml

# PR Agent (専用config使用)
gcloud builds submit --config cloudbuild-pr.yaml
```

### 2. デプロイ（Real Vertex AI環境変数付き）

```bash
# 全エージェント統一デプロイ
gcloud run deploy orchestrator-agent \
    --image gcr.io/sharelabai-hackathon2/orchestrator-agent:latest \
    --region asia-northeast1 \
    --set-env-vars="USE_MOCK_LLM=false,GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2,GOOGLE_CLOUD_REGION=asia-northeast1"

gcloud run deploy info-collector-agent \
    --image gcr.io/sharelabai-hackathon2/info-collector-agent:latest \
    --region asia-northeast1 \
    --set-env-vars="USE_MOCK_LLM=false,GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2,GOOGLE_CLOUD_REGION=asia-northeast1"

gcloud run deploy analyzer-agent \
    --image gcr.io/sharelabai-hackathon2/analyzer-agent:latest \
    --region asia-northeast1 \
    --set-env-vars="USE_MOCK_LLM=false,GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2,GOOGLE_CLOUD_REGION=asia-northeast1"

gcloud run deploy pr-agent \
    --image gcr.io/sharelabai-hackathon2/pr-agent:latest \
    --region asia-northeast1 \
    --set-env-vars="USE_MOCK_LLM=false,GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2,GOOGLE_CLOUD_REGION=asia-northeast1"
```

## スケジューラー実行後の確認方法

### 1. スケジューラー手動実行
```bash
# 定期実行スケジューラーを手動で起動
gcloud scheduler jobs run disaster-detection-scheduler --location=asia-northeast1
```

### 2. 実行状況の確認

#### A) 各エージェントの動作確認
```bash
# 全体の流れを時系列で確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name:(detection-agent OR orchestrator-agent OR info-collector-agent OR analyzer-agent OR pr-agent) AND timestamp>=\"$(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%SZ)\"" --format="value(timestamp,resource.labels.service_name,textPayload)" --limit=50

# Detection Agentの災害検知結果確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=detection-agent AND (textPayload:\"disaster detected\" OR textPayload:\"Detection task completed\")" --limit=5

# Orchestrator Agentのタスク分散確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-agent AND textPayload:\"Published task\"" --limit=10
```

#### B) Real Vertex AI使用確認
```bash
# Mock LLMが使用されていないことを確認
gcloud logging read "textPayload:\"[MOCK] LLM invoked\"" --limit=5

# Vertex AI APIコール確認
gcloud logging read "resource.type=cloud_run_revision AND (textPayload:\"Vertex AI\" OR textPayload:\"ainvoke\")" --limit=10
```

#### C) PR Agentの正常動作確認
```bash
# PR Agentの正しいエンドポイント確認
curl "https://pr-agent-670435464520.asia-northeast1.run.app/docs"

# 最新の災害情報取得
curl "https://pr-agent-670435464520.asia-northeast1.run.app/latest?limit=3"

# PR Agentログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pr-agent" --limit=5
```

### 3. 成功指標

#### ✅ 正常動作の確認項目
1. **Detection Agent**: RSS取得成功 + 災害判定実行
2. **Orchestrator**: 各エージェントへのタスク分散成功  
3. **Info Collector**: ニュース収集 + Real Vertex AI関連性判定
4. **Analyzer**: 影響評価 + Real Vertex AI分析
5. **PR Agent**: 災害情報生成 + `/latest`エンドポイントで結果確認可能

#### 📊 期待される結果
```bash
# 成功時のPR Agent API応答例
{
  "bulletins": [
    {
      "content": {
        "web": {...実際のニュース内容...},
        "mobile": {...},
        "emergency": {...}
      },
      "event_id": "実際のevent_id",
      "published_at": "2025-09-09T...",
      "status": "published"
    }
  ]
}
```

### 4. エラー対応
```bash
# エラーログ確認
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR AND timestamp>=\"$(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%SZ)\"" --limit=20

# 429エラー（レート制限）の場合は正常 - リトライで解決
# 404エラーの場合はDockerイメージ問題 - 再ビルド必要
```

これで正しい動作確認ができます！