# Disaster Response System - フロントエンド向け API 仕様（ドラフト・更新版）

本書はフロントエンド実装に合わせて **スキーマ変更** を反映した最新版です。  
（変更点：`Incident.isActive` 追加、`FeedItem.incidentId` 追加、関連フィード取得の推奨エンドポイント追加）

---

## 0. 概要
- 目的: フロントエンド（Next.js）が **同一スキーマ** でデータを取得できるように、バックエンド（または Firestore）の **JSON 形式** を定義する。  
- 実装形態:
  - A) Firestore 直購読（推奨: `incidents` / `alerts` / `feeds` コレクション）
  - B) REST API（サーバー経由で正規化レスポンス）
- 互換性原則: 既存フィールドの削除・型変更は避け、**optional 追加** で進化させる。

---

## 1. 共通規約
- 文字コード: UTF-8
- タイムスタンプ: **ミリ秒エポック（ms epoch）**
- 緯度・経度: `number`
- 言語: 表示系フィールド（`title`, `area` など）は日本語可
- 識別子: `id` はユニーク。`hazard` 等の分類値は英小文字固定を推奨

---

## 2. Incidents
### 2.1 用途
- 地図上のピン表示（**赤=Active**, **青=Inactive**）
- 画面カード「Active Alerts」「Events Today」の集計に利用（※フロントは可視範囲で集計）

### 2.2 モデル
```ts
type Incident = {
  id: string
  title: string
  lat: number
  lng: number
  severity?: "low" | "medium" | "high"
  reportedAt?: number                // ms epoch
  isActive?: boolean                 // 追加: アクティブ判定（true=赤ピン）
  hazard?: "earthquake" | "typhoon" | "flood" | "landslide" | "tsunami" | "wildfire" | "other"
  area?: string
  description?: string
}
```

### 2.3 例
```json
{
  "id": "i11",
  "title": "大雨・交通影響",
  "lat": 35.6895,
  "lng": 139.6917,
  "severity": "medium",
  "reportedAt": 1736380200000,
  "isActive": false,
  "hazard": "flood",
  "area": "東京"
}
```

---

## 3. Alerts
### 3.1 用途
- 有効な警報・注意報のカード/一覧表示（AI 判定または外部 API の正規化）

### 3.2 モデル
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

### 3.3 例
```json
[
  {
    "id": "alrt-001",
    "title": "大雨警報（東京23区）",
    "level": "watch",
    "hazard": "flood",
    "area": "東京23区",
    "startedAt": 1736376600000
  }
]
```

---

## 4. Feeds
### 4.1 用途
- ニュース/RSS/気象庁 API/ソーシャル(X 等)の **正規化フィード**
- **Incident と紐付くフィードを強調表示**（フロントで `incidentId` をキーにハイライト）

### 4.2 モデル（更新）
```ts
type FeedItem = {
  id: string
  incidentId?: string            // 追加: 対応する Incident の id（存在すれば UI で強調）
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

### 4.3 例
```json
[
  {
    "id": "f2",
    "incidentId": "i11",
    "source": "nhk",
    "title": "大雨の影響で一部路線で遅延",
    "url": "https://www.nhk.or.jp/",
    "publishedAt": 1736373000000,
    "labels": ["注意報","大雨"],
    "area": "東京",
    "hazard": "flood",
    "isAlertCandidate": true
  }
]
```

---

## 5. 推奨エンドポイント例（REST 実装時）
- `GET /api/incidents?since=<ms>`  
  - 目的: 最近のインシデント取得
  - クエリ例: `?since=1736369400000`  
- `GET /api/alerts?active=true`  
  - 目的: 現在有効なアラート取得
- `GET /api/feeds?limit=50`  
  - 目的: 最新フィード
- `GET /api/feeds?incidentId=<id>&limit=50`   ← **新規推奨**
  - 目的: 指定 Incident に紐付くフィードを取得（UI で強調・先頭表示）
  - 返却: `FeedItem[]`（`incidentId` が一致するもののみ）
- `GET /api/incidents/:id`（任意）
  - 目的: 1件詳細

※ Firestore 直購読の場合は上記 REST を省略可。  
※ 紐付けは `feeds` ドキュメントに `incidentId` を保持するか、中間コレクションを用いる実装でも可。

---

## 6. Firestore 構成（推奨）
- コレクション:
  - `incidents`（`reportedAt` 降順で取得するクエリが多い）
  - `alerts`
  - `feeds`（`publishedAt` 降順、`incidentId` での絞り込み）
- 推奨インデックス例:
  - `feeds`: `incidentId ASC, publishedAt DESC`
  - `incidents`: `reportedAt DESC`
- 更新設計:
  - `Incident.isActive` はサーバー側で算出・更新（例：発生から一定時間以内、または外部シグナルで判定）
  - フィード取り込み時に関連 Incident 判定を行い `incidentId` を付与

---

## 7. 表示要件（UI 連携のための補足）
- 地図上のピン: `isActive=true` は赤、`false` は青
- ピン（Incident）クリック時:
  - 詳細カード表示（`title / area / hazard / severity / reportedAt / lat,lng`）
  - **関連フィード（`incidentId` が一致）を優先的に表示**  
    - UI は該当フィードを最上部に移動し、背景色を淡い黄色で強調
- 時刻はフロントで `new Date(ms).toLocaleString()` を用いて表示

---

## 8. サンプル・ミニダンプ
### 8.1 incidents（抜粋）
```json
[
  { "id":"i9",  "title":"地震（震度5弱）", "lat":36.3902, "lng":139.0600, "severity":"high", "reportedAt":1736379300000, "isActive":true,  "hazard":"earthquake", "area":"前橋" },
  { "id":"i11", "title":"大雨・交通影響",   "lat":35.6895, "lng":139.6917, "severity":"medium","reportedAt":1736380200000, "isActive":false, "hazard":"flood",      "area":"東京" }
]
```

### 8.2 feeds（対応付け例）
```json
[
  { "id":"f1","incidentId":"i9","source":"jma","title":"【地震情報】関東南部で震度5弱","url":"https://www.jma.go.jp/","publishedAt":1736379600000,"labels":["警報","地震"],"area":"関東","hazard":"earthquake","isAlertCandidate":true },
  { "id":"f2","incidentId":"i11","source":"nhk","title":"大雨の影響で一部路線で遅延","url":"https://www.nhk.or.jp/","publishedAt":1736373000000,"labels":["注意報","大雨"],"area":"東京","hazard":"flood","isAlertCandidate":true }
]
```

---

## 9. AI생성 FAQ
### 9.1 용도
- 현재 활성화된 Alert에 대한 동적 FAQ 생성
- 재해 유형별 행동요령, 주의사항, 대피방법 등을 GenAI로 생성

### 9.2 모델
```ts
type AIGeneratedFAQ = {
  id: string
  alertId: string                    // 관련 Alert ID
  hazardType: "earthquake" | "typhoon" | "flood" | "landslide" | "tsunami" | "wildfire" | "other"
  category: "action_guide" | "safety_tips" | "evacuation" | "preparation" | "recovery"
  question: string
  answer: string
  priority: number                   // 표시 우선순위 (낮을수록 상위)
  generatedAt: number               // 생성 시각 (ms epoch)
  isRelevant: boolean               // 현재 상황과의 관련성
}

type AIFAQResponse = {
  alertId: string
  alertTitle: string
  hazardType: string
  area: string
  faqs: AIGeneratedFAQ[]
  lastUpdated: number
}
```

### 9.3 예시
```json
{
  "alertId": "alrt-001",
  "alertTitle": "대지진 경보 (도쿄 23구)",
  "hazardType": "earthquake",
  "area": "도쿄 23구",
  "faqs": [
    {
      "id": "faq-ai-001",
      "alertId": "alrt-001",
      "hazardType": "earthquake",
      "category": "action_guide",
      "question": "지진이 발생했을 때 가장 먼저 해야 할 일은?",
      "answer": "먼저 안전한 곳으로 몸을 피하세요. 책상 아래나 견고한 가구 밑으로 들어가 머리를 보호하고, 출입구 근처에서 떨어질 수 있는 물건들로부터 멀리 떨어져 있으세요.",
      "priority": 1,
      "generatedAt": 1736400000000,
      "isRelevant": true
    },
    {
      "id": "faq-ai-002",
      "alertId": "alrt-001",
      "hazardType": "earthquake",
      "category": "evacuation",
      "question": "지진 후 대피할 때 주의사항은?",
      "answer": "건물에서 나갈 때는 엘리베이터를 사용하지 말고 계단을 이용하세요. 가스밸브를 잠그고 전기 차단기를 내린 후 안전한 대피장소로 이동하세요.",
      "priority": 2,
      "generatedAt": 1736400000000,
      "isRelevant": true
    }
  ],
  "lastUpdated": 1736400000000
}
```

### 9.4 추천 엔드포인트
- `GET /api/faq/ai?alertId=<alertId>`
  - 목적: 특정 Alert에 대한 AI생성 FAQ 취득
  - 예시: `?alertId=alrt-001`
- `GET /api/faq/ai/active`
  - 목적: 현재 활성화된 모든 Alert에 대한 FAQ 취득
  - 반환: `AIFAQResponse[]`

---

## 10. 변경履歴（본版の差분）
- Incident: `isActive`, `hazard`, `area`, `description` を定義
- FeedItem: `incidentId` を追가
- 推奨 REST: `GET /api/feeds?incidentId=<id>` を追가
- AIGeneratedFAQ: GenAI 기반 FAQ 시스템 추가