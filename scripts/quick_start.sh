#!/bin/bash

set -e

echo "=== 災害対応システム クイックスタート ==="

cd "$(dirname "$0")/.."

echo "選択してください:"
echo "1) ローカルテスト (エミュレータ + Docker)"
echo "2) ローカルテスト (エミュレータのみ)"
echo "3) GCPデプロイ"
echo "4) 環境設定のみ"

read -p "選択 (1-4): " choice

case $choice in
    1)
        echo "=== Docker Compose ローカルテスト ==="
        
        # 環境変数確認
        if [ ! -f .env ]; then
            echo "環境設定ファイルをコピーしています..."
            cp .env.example .env
            echo "❗ .env ファイルを編集してプロジェクトIDを設定してください"
            exit 1
        fi
        
        # エミュレータ起動
        echo "エミュレータ起動..."
        ./scripts/setup_emulators.sh
        
        # Docker起動
        echo "Docker Compose起動..."
        docker-compose up -d
        
        # テスト実行
        echo "テスト実行..."
        sleep 15
        ./scripts/test_local.sh
        ;;
        
    2)
        echo "=== エミュレータのみ ローカルテスト ==="
        
        # 依存関係インストール
        echo "依存関係インストール..."
        pip install -r requirements.txt
        
        # エミュレータ起動
        ./scripts/setup_emulators.sh
        
        echo "個別Agentを起動してテストを実行してください:"
        echo "cd agents/detection && python main.py"
        ;;
        
    3)
        echo "=== GCPデプロイ ==="
        
        # 前提条件確認
        if ! command -v gcloud &> /dev/null; then
            echo "gcloud CLIがインストールされていません"
            exit 1
        fi
        
        if ! command -v terraform &> /dev/null; then
            echo "Terraformがインストールされていません"
            exit 1
        fi
        
        echo "GCPデプロイを開始します..."
        ./scripts/deploy.sh
        ;;
        
    4)
        echo "=== 環境設定 ==="
        
        if [ ! -f .env ]; then
            cp .env.example .env
            echo "✅ .env ファイルを作成しました"
        fi
        
        echo "以下を設定してください:"
        echo "1. .env ファイルでプロジェクトID設定"
        echo "2. gcloud auth application-default login"
        echo "3. gcloud config set project YOUR_PROJECT_ID"
        ;;
        
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac

echo "=== 完了 ==="