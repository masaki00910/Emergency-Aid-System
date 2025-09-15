# API統合完了ガイド

## 完了したタスク

### 1. APIサービスモジュール作成
- `src/lib/api.ts`: Firebase/REST API統合サービス
- Firebase優先、REST APIフォールバック対応
- 環境変数でAPI方式を選択可能

### 2. ページ別API接続
- ✅ **ダッシュボード (`/dashboard`)**: mock → API接続完了
- ✅ **アラート一覧 (`/alerts`)**: mock → API接続完了
- ✅ **アラート詳細 (`/alerts/[id]`)**: mock → API接続完了

## 環境設定

### 1. 環境変数設定
`.env.local`ファイルを作成し、以下の値を設定:

```bash
# Firebase使用時（推奨）
NEXT_PUBLIC_USE_FIREBASE=true
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_key

# REST API使用時
NEXT_PUBLIC_USE_FIREBASE=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

### 2. Firestoreデータ構造
バックエンドで以下のコレクションが準備されている必要があります：

```
firestore/
├── incidents/          # インシデントデータ
├── alerts/            # アラートデータ
└── feeds/             # フィードデータ
```

### 3. APIエンドポイント（REST使用時）
```
GET /api/incidents?since=<ms>
GET /api/incidents/:id
GET /api/alerts?active=true
GET /api/alerts/:id
GET /api/feeds?limit=50
GET /api/feeds?incidentId=<id>&limit=50
```

## 使用方法

### Firebase方式（推奨）
```typescript
import { API } from '@/lib/api'

// インシデント取得
const incidents = await API.getIncidents()

// アクティブなアラートのみ取得
const activeAlerts = await API.getAlerts(true)

// 特定インシデント関連フィード
const feeds = await API.getFeedsByIncident('incident_id')
```

### REST API方式
環境変数を変更するだけで自動的にREST APIを使用：
```bash
NEXT_PUBLIC_USE_FIREBASE=false
NEXT_PUBLIC_API_BASE_URL=https://your-api-server.com
```

## 主な変更点

### 1. ダッシュボードページ
- Mockデータ削除
- API呼び出しでリアルタイムデータ読み込み
- ローディング状態追加
- エラー処理追加

### 2. アラートページ
- Mockデータ削除
- アラート + インシデント統合表示
- ローディング状態および空状態処理

### 3. アラート詳細ページ
- Mockデータ削除
- 関連フィード動的読み込み
- タイムラインAPI基盤生成

## テスト方法

### 1. Mockデータでテスト
バックエンドが準備されていない場合、一時的にmockデータを使用：

```typescript
// src/lib/api.tsで一時修正
export const API = {
  getIncidents: () => Promise.resolve(mockIncidents),
  getAlerts: () => Promise.resolve(mockAlerts),
  getFeeds: () => Promise.resolve(mockFeeds),
  // ...
}
```

### 2. 開発サーバー実行
```bash
cd web/
npm run dev
```

ブラウザで`http://localhost:3000`にアクセスして確認

## 次のステップ

1. **バックエンド接続**: Firebaseプロジェクト設定またはREST APIサーバー準備
2. **環境変数設定**: 実際のAPIキーで`.env.local`設定
3. **データ確認**: APIレスポンスがスキーマと一致することを確認
4. **エラー処理**: ネットワークエラー、空データなどの追加処理

## トラブルシューティング

### Firebase接続エラー
- Firebaseプロジェクト設定確認
- APIキーおよびプロジェクトID確認
- Firestoreルール設定確認

### REST API接続エラー
- APIサーバーが稼働中か確認
- CORS設定確認
- エンドポイントURL確認

### データタイプエラー
- `FE_APIschema.md`と実際のレスポンスデータを比較
- TypeScript型定義確認