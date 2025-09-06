#!/bin/bash

set -e

echo "=== GCPエミュレータセットアップ ==="

# 環境変数チェック
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT環境変数が設定されていません"
    echo "export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

echo "1. Firestoreエミュレータ起動..."
gcloud emulators firestore start --host-port=localhost:8080 &
FIRESTORE_PID=$!

echo "2. Pub/Subエミュレータ起動..."
gcloud emulators pubsub start --host-port=localhost:8085 &
PUBSUB_PID=$!

# 起動待機
sleep 5

echo "3. 環境変数設定..."
export FIRESTORE_EMULATOR_HOST=localhost:8080
export PUBSUB_EMULATOR_HOST=localhost:8085

echo "4. Pub/Subトピック・サブスクリプション作成..."

# トピック作成
gcloud pubsub topics create disaster-poll
gcloud pubsub topics create disaster-detected
gcloud pubsub topics create agent-task-info-collector
gcloud pubsub topics create agent-task-analyzer
gcloud pubsub topics create agent-task-pr
gcloud pubsub topics create agent-task-support

# サブスクリプション作成
gcloud pubsub subscriptions create disaster-poll-subscription --topic=disaster-poll
gcloud pubsub subscriptions create disaster-detected-subscription --topic=disaster-detected
gcloud pubsub subscriptions create agent-task-info-collector-subscription --topic=agent-task-info-collector
gcloud pubsub subscriptions create agent-task-analyzer-subscription --topic=agent-task-analyzer
gcloud pubsub subscriptions create agent-task-pr-subscription --topic=agent-task-pr
gcloud pubsub subscriptions create agent-task-support-subscription --topic=agent-task-support

echo "5. 環境変数出力..."
echo ""
echo "以下の環境変数を設定してください:"
echo "export FIRESTORE_EMULATOR_HOST=localhost:8080"
echo "export PUBSUB_EMULATOR_HOST=localhost:8085"
echo "export GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
echo "export GOOGLE_CLOUD_REGION=asia-northeast1"
echo ""

echo "✅ エミュレータセットアップ完了"
echo ""
echo "エミュレータ停止方法:"
echo "kill $FIRESTORE_PID $PUBSUB_PID"

# PIDファイル保存
echo "$FIRESTORE_PID" > .firestore_emulator.pid
echo "$PUBSUB_PID" > .pubsub_emulator.pid

echo "または: ./scripts/stop_emulators.sh"