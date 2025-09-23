# 開発環境セットアップ手順

## 前提条件

- Docker Desktop インストール済み
- Node.js 18+ インストール済み
- Python 3.11+ インストール済み
- Git インストール済み

## 環境変数設定

プロジェクトルートに `.env` ファイルを作成：

```bash
# GCPプロジェクト設定
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=asia-northeast1

# 開発環境用設定
USE_MOCK_LLM=true
NODE_ENV=development
```

## バックエンド開発環境起動

### 1. マルチエージェントシステム起動

```bash
# 全エージェント一括起動
docker-compose up

# 個別エージェント起動
docker-compose up detection-agent
docker-compose up orchestrator-agent
docker-compose up info-collector-agent
docker-compose up analyzer-agent
docker-compose up pr-agent
```

### 2. API Gateway起動

```bash
cd api_gateway
pip install -r requirements.txt
python main.py
```

## フロントエンド開発環境起動

```bash
cd web
npm install
npm run dev
```

アクセス: http://localhost:3000

## 開発用ポート番号

- **フロントエンド**: 3000
- **API Gateway**: 8082
- **災害検知Agent**: 8081
- **オーケストレータAgent**: 8082
- **情報収集Agent**: 8083
- **分析Agent**: 8084
- **広報Agent**: 8085

## 開発時の動作確認

### バックエンドAPI確認

```bash
# ヘルスチェック
curl http://localhost:8082/health

# 災害情報取得
curl http://localhost:8082/api/public/disasters

# FAQ機能テスト
curl -X POST "http://localhost:8082/api/public/faq/sample-disaster-1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "避難のタイミングは？"}'
```

### フロントエンド動作確認

1. http://localhost:3000 にアクセス
2. アラート一覧の表示確認
3. マップコンポーネントの動作確認
4. レスポンシブデザイン確認

## 開発時のコマンド

### フロントエンド

```bash
# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 本番モード起動
npm run start

# 型チェック
npx tsc --noEmit

# Linting
npx eslint src/
```

### バックエンド

```bash
# 全エージェント再ビルド
docker-compose build

# ログ確認
docker-compose logs -f detection-agent

# 特定コンテナ内でコマンド実行
docker-compose exec detection-agent bash
```

## ホットリロード

- **フロントエンド**: Next.jsの自動リロード有効
- **バックエンド**: volumes設定によりソースコード変更時に自動反映

## デバッグ方法

### フロントエンド

1. Chrome DevToolsを使用
2. Next.js DevToolsでコンポーネント状態確認
3. ネットワークタブでAPI呼び出し確認

### バックエンド

```bash
# ログレベル設定
export LOG_LEVEL=DEBUG

# 詳細ログ出力
docker-compose logs --tail=100 -f
```

## 開発時の注意事項

1. **環境変数**: 本番用の認証情報は使用しない
2. **モックデータ**: USE_MOCK_LLM=trueで開発
3. **ポート競合**: 既存サービスとのポート重複に注意
4. **リソース**: Dockerコンテナ起動時のメモリ使用量に注意

## トラブルシューティング

### よくある問題

1. **ポート使用中エラー**
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. **Docker起動失敗**
   ```bash
   docker-compose down
   docker system prune -a
   docker-compose up --build
   ```

3. **npm依存関係エラー**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```