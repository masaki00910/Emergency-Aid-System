# Disaster Response System - フロントエンド向け API 仕様（ドラフト）

## 0. 概要
- **目的**: フロントエンド（Next.js）が同一スキーマでデータを取得できるように、バックエンド（または Firestore）の JSON 形式を定義する。  
- **実装形態**:
  - A) Firestore 直購読（推奨: `incidents` / `alerts` / `feeds` コレクションを用意）
  - B) REST API（サーバー経由で正規化レスポンスを返却）
- **互換性**:
  - フィールド追加は後方互換（optional 追加）を原則とする。
  - 既存フィールドの削除・型変更は避けること。

---

## 1. 共通規約
- 文字コード: UTF-8  
- タイムスタンプ: **ミリ秒エポック（ms epoch）**  
- 緯度・経度: `number` 型  
- 言語: 値は基本的に日本語可（title 等）  
- 識別用フィールド（`hazard` 等）は英小文字固定  

---

## 2. Incidents
### 目的
地図上にピン表示する「発生中/最近の災害イベント」

### データソース
Firestore コレクション `incidents`

### モデル
```ts
type Incident = {
  id: string
  title: string
  lat: number
  lng: number
  severity?: "low" | "medium" | "high"
  reportedAt?: number // ms epoch
}
```

### 例
```json
{
  "id": "abc123",
  "title": "強い地震（震度5弱）",
  "lat": 35.68,
  "lng": 139.76,
  "severity": "high",
  "reportedAt": 1735932000000
}
```

---

## 3. Alerts
### 目的
現在有効な警報・注意報を表示するカードや一覧に利用

### 生成元
Agentic AI により判定、または外部 API からの警報/注意報を正規化

### モデル
```ts
type Alert = {
  id: string
  title: string
  level: "info" | "advisory" | "watch" | "warning" | "emergency"
  hazard: "earthquake" | "typhoon" | "flood" | "landslide" | "tsunami" | "wildfire" | "other"
  area: string
  startedAt: number
  updatedAt?: number
}
```

### 例
```json
[
  {
    "id": "alrt-001",
    "title": "大雨警報（東京23区）",
    "level": "watch",
    "hazard": "flood",
    "area": "東京23区",
    "startedAt": 1735928400000
  }
]
```

---

## 4. Feeds
### 目的
ニュース / RSS / 気象庁 API / ソーシャル (X 等) の正規化フィード

Agentic AI により `isAlertCandidate: true` が付与された場合、  
フロントエンドで「要確認」バッジを表示可能

### モデル
```ts
type FeedItem = {
  id: string
  source: "nhk" | "jma" | "tenki" | "x" | "news" | "other"
  title: string
  summary?: string
  url: string
  publishedAt: number
  labels?: string[]
  area?: string
  hazard?: string
  isAlertCandidate?: boolean
}
```

### 例
```json
[
  {
    "id": "feed-001",
    "source": "jma",
    "title": "【地震情報】関東南部で震度5弱",
    "summary": "交通機関に影響の可能性。余震に注意してください。",
    "url": "https://www.jma.go.jp/",
    "publishedAt": 1735932600000,
    "labels": ["警報","地震"],
    "area": "関東",
    "hazard": "earthquake",
    "isAlertCandidate": true
  }
]
```

---

## 5. 推奨エンドポイント例
- `GET /api/incidents?since=<ms>` → 最近のインシデント取得  
- `GET /api/alerts?active=true` → 有効なアラート取得  
- `GET /api/feeds?limit=50` → 最新フィード取得  

※ Firestore を直接購読する場合は REST エンドポイント不要
