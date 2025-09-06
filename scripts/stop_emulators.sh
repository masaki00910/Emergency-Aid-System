#!/bin/bash

echo "=== GCPエミュレータ停止 ==="

cd "$(dirname "$0")/.."

# PIDファイルから停止
if [ -f .firestore_emulator.pid ]; then
    FIRESTORE_PID=$(cat .firestore_emulator.pid)
    kill $FIRESTORE_PID 2>/dev/null || echo "Firestore emulator already stopped"
    rm .firestore_emulator.pid
fi

if [ -f .pubsub_emulator.pid ]; then
    PUBSUB_PID=$(cat .pubsub_emulator.pid)
    kill $PUBSUB_PID 2>/dev/null || echo "Pub/Sub emulator already stopped"
    rm .pubsub_emulator.pid
fi

# プロセス確認で強制終了
pkill -f "gcloud emulators firestore" 2>/dev/null || true
pkill -f "gcloud emulators pubsub" 2>/dev/null || true

echo "✅ エミュレータ停止完了"