# 災害情報システム API Gateway

フロントエンド向けの公開APIとWebSocketによるリアルタイム通信を提供します。

## 🚀 ローカル起動方法

### 1. 環境設定

```bash
# Google Cloud プロジェクトID設定
export GOOGLE_CLOUD_PROJECT=your-project-id

# 認証設定（どちらか一つ）
# 方法A: Application Default Credentials
gcloud auth application-default login

# 方法B: サービスアカウントキー（本番用）
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 2. 依存関係インストール

```bash
cd api_gateway
pip install -r requirements.txt
```

### 3. サーバー起動

```bash
# 方法A: 起動スクリプト使用（推奨）
python start_local.py

# 方法B: 直接uvicorn起動
uvicorn main:app --reload --port 8081
```

## 📡 API エンドポイント

### REST API
- **Base URL**: `http://localhost:8081`
- **API Documentation**: `http://localhost:8081/docs`
- **災害一覧**: `GET /api/public/disasters`
- **災害詳細**: `GET /api/public/disasters/{id}`
- **マップデータ**: `GET /api/public/disasters/map-data`
- **統計情報**: `GET /api/public/disasters/stats`

### WebSocket
- **URL**: `ws://localhost:8081/ws/connect`

#### WebSocketメッセージ例

**接続後の設定**:
```json
{
  "type": "subscribe",
  "subscriptions": {
    "prefectures": ["東京都", "神奈川県"],
    "min_severity": "medium",
    "disaster_types": ["earthquake", "flood"]
  }
}
```

**ハートビート**:
```json
{
  "type": "ping"
}
```

**ステータス確認**:
```json
{
  "type": "get_status"
}
```

## 🎯 使用例

### フロントエンドからのAPI呼び出し

```javascript
// 災害一覧取得
const response = await fetch('http://localhost:8081/api/public/disasters?page=1&limit=20');
const data = await response.json();

// WebSocket接続
const ws = new WebSocket('ws://localhost:8081/ws/connect');

ws.onopen = () => {
  // サブスクリプション設定
  ws.send(JSON.stringify({
    type: 'subscribe',
    subscriptions: {
      prefectures: ['東京都'],
      min_severity: 'high'
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'disaster_update') {
    console.log('新しい災害情報:', message.data);
  }
};
```

## 🔧 開発・デバッグ

### ログレベル設定
```bash
export LOG_LEVEL=DEBUG
python start_local.py
```

### WebSocket接続テスト
```bash
# wscat を使用してWebSocket接続テスト
npm install -g wscat
wscat -c ws://localhost:8081/ws/connect
```

## 📁 ファイル構造

```
api_gateway/
├── main.py                 # メインアプリケーション
├── start_local.py          # ローカル起動スクリプト
├── requirements.txt        # Python依存関係
├── routers/
│   ├── disasters.py        # 災害情報API
│   └── websocket.py        # WebSocket通信
├── models/
│   └── public_api.py       # データモデル定義
├── services/
│   └── disaster_service.py # データ処理サービス
└── utils/
    └── __init__.py
```

## 🌐 フロントエンドとの連携

このAPI Gatewayは以下のフロントエンド機能をサポートします：

1. **災害一覧表示** - ページネーション、フィルタリング対応
2. **マップ表示** - 軽量化されたマーカーデータ
3. **リアルタイム更新** - WebSocketによる即座な通知
4. **詳細情報** - 個別災害の詳細データ
5. **統計ダッシュボード** - 集計データ提供

## 🐛 トラブルシューティング

### よくある問題

1. **Firestore接続エラー**
   ```
   解決方法: gcloud auth application-default login
   ```

2. **ポート競合**
   ```
   解決方法: 別のポートを指定
   uvicorn main:app --port 8082
   ```

3. **WebSocket接続失敗**
   ```
   解決方法: CORS設定確認、ブラウザコンソールでエラー確認
   ```