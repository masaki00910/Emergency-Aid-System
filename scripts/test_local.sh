#!/bin/bash

set -e

echo "=== ローカルテスト実行スクリプト ==="

# 環境変数チェック
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT環境変数が設定されていません"
    echo "export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

cd "$(dirname "$0")/.."

echo "1. エミュレータ起動確認..."

# Firestoreエミュレータ確認
if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "Firestoreエミュレータを起動してください:"
    echo "gcloud emulators firestore start --host-port=localhost:8080 &"
    exit 1
fi

# Pub/Subエミュレータ確認  
if ! curl -s http://localhost:8085 > /dev/null 2>&1; then
    echo "Pub/Subエミュレータを起動してください:"
    echo "gcloud emulators pubsub start --host-port=localhost:8085 &"
    exit 1
fi

echo "✅ エミュレータ起動確認完了"

echo "2. Docker Composeサービス起動..."
docker-compose up -d

# サービス起動待機
sleep 10

echo "3. ヘルスチェック実行..."

SERVICES=(
    "detection:8081"
    "orchestrator:8082" 
    "info-collector:8083"
    "analyzer:8084"
    "pr:8085"
)

for service in "${SERVICES[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    echo "Testing $name on port $port..."
    
    if curl -s http://localhost:$port/health | grep -q "healthy"; then
        echo "✅ $name: OK"
    else
        echo "❌ $name: Failed"
        docker-compose logs $name-agent
    fi
done

echo "4. 災害検知テスト..."
DETECTION_RESULT=$(curl -s -X POST http://localhost:8081/detect)
echo "Detection result: $DETECTION_RESULT"

echo "5. E2Eテスト実行..."

# テスト用災害イベント作成
TEST_EVENT='{
  "event_id": "test-local-001",
  "detected_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "source": ["test"],
  "type": "earthquake", 
  "location": {"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
  "severity": 0.7,
  "confidence": 0.9,
  "summary": "ローカルテスト用地震イベント",
  "evidence": []
}'

echo "Orchestrating test event..."
ORCHESTRATE_RESULT=$(curl -s -X POST http://localhost:8082/orchestrate \
  -H "Content-Type: application/json" \
  -d "$TEST_EVENT")

echo "Orchestration result: $ORCHESTRATE_RESULT"

# 処理完了待機
echo "6. 処理完了待機 (30秒)..."
sleep 30

# 結果確認
echo "7. 結果確認..."

echo "Task status:"
curl -s http://localhost:8082/events/test-local-001/tasks | jq '.'

echo "Generated bulletins:"
curl -s http://localhost:8085/events/test-local-001/bulletins | jq '.'

echo "Analysis results:"
curl -s http://localhost:8084/events/test-local-001/analysis | jq '.'

echo "=== ローカルテスト完了 ==="
echo "詳細ログ確認: docker-compose logs -f"