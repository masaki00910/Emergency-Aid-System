# ローカルテスト手順

## 前提条件

### 必要なツール
```bash
# Python 3.11+
python3 --version

# gcloud CLI
gcloud version

# Docker & Docker Compose (推奨)
docker --version
docker-compose --version
```

### GCP認証設定
```bash
# Application Default Credentials設定
gcloud auth application-default login

# プロジェクト設定
gcloud config set project YOUR_PROJECT_ID
```

## 方法1: GCPエミュレータ使用 (Docker不要)

### 1. エミュレータ起動
```bash
# Firestoreエミュレータ
gcloud emulators firestore start --host-port=localhost:8080 &

# Pub/Subエミュレータ
gcloud emulators pubsub start --host-port=localhost:8085 &
```

### 2. 環境変数設定
```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
export PUBSUB_EMULATOR_HOST=localhost:8085
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_REGION=asia-northeast1
```

### 3. 依存関係インストール
```bash
cd disaster-response-system
pip install -r requirements.txt
```

### 4. 個別Agentテスト
```bash
# 災害検知Agent
cd agents/detection
python main.py &
# ポート8080で起動

# オーケストレータAgent  
cd ../orchestrator
python main.py &
# ポート8080で起動（ポート重複回避）
```

### 5. テスト実行
```bash
# 災害検知テスト
curl -X POST http://localhost:8080/detect

# ヘルスチェック
curl http://localhost:8080/health
```

## 方法2: Docker Compose使用 (推奨)

### 1. 環境変数ファイル作成
```bash
# .env ファイル作成
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=asia-northeast1
EOF
```

### 2. サービス起動
```bash
# 全エージェント起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

### 3. エージェントテスト
```bash
# 災害検知Agent (ポート8081)
curl -X POST http://localhost:8081/detect

# オーケストレータAgent (ポート8082)
curl http://localhost:8082/health

# 情報収集Agent (ポート8083)
curl http://localhost:8083/health

# 対策検討Agent (ポート8084) 
curl http://localhost:8084/health

# 広報Agent (ポート8085)
curl http://localhost:8085/health
```

### 4. E2Eテスト
```bash
# 災害イベント手動発生
curl -X POST http://localhost:8082/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-001",
    "detected_at": "2025-01-15T10:00:00Z",
    "source": ["test"],
    "type": "earthquake",
    "location": {"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
    "severity": 0.7,
    "confidence": 0.9,
    "summary": "テスト用地震イベント",
    "evidence": []
  }'
```

### 5. ステータス確認
```bash
# オーケストレーション状況確認
curl http://localhost:8082/events/test-001/tasks

# 生成されたコンテンツ確認
curl http://localhost:8085/events/test-001/bulletins
```

## トラブルシューティング

### ポート競合
```bash
# ポート使用状況確認
lsof -i :8080-8085

# Docker Compose停止
docker-compose down
```

### ログ確認
```bash
# エミュレータログ
gcloud emulators firestore logs

# Dockerログ
docker-compose logs [service-name]
```

### 認証エラー
```bash
# ADC再設定
gcloud auth application-default revoke
gcloud auth application-default login
```

## テストデータ

### サンプル災害イベント
```json
{
  "event_id": "test-earthquake-001",
  "type": "earthquake",
  "location": {"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
  "severity": 0.8,
  "confidence": 0.9,
  "summary": "震度5強の地震が発生"
}
```

### 期待される動作
1. 災害検知 → Pub/Sub発行
2. オーケストレータ → 各Agentにタスク配信
3. 情報収集 → RAG構築
4. 分析 → 影響評価
5. 広報 → コンテンツ生成・配信