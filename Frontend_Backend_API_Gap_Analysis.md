# フロントエンド - バックエンド API ギャップ分析

## 📋 概要
フロントエンドチームが必要とするAPIレスポンスと、現在のバックエンドが提供しているAPIレスポンスの差異を分析し、追加で必要な機能を明確にします。

---

## 🚨 **重要な問題点**

### **❌ 現在のバックエンドの課題**
| 問題 | 説明 | 影響 |
|------|------|------|
| **公開API不足** | エージェント間の内部通信APIのみ | フロントエンドが直接使用できない |
| **リアルタイム更新なし** | WebSocket/SSE未対応 | ユーザーへの即座な情報提供不可 |
| **データ取得API不足** | 災害リスト取得機能なし | 基本的な画面表示ができない |
| **フィルタリング機能なし** | 地域・時間・重要度での絞り込み不可 | ユーザビリティが低い |

---

## 🔍 **詳細比較分析**

### **1. 災害情報取得API**

| 項目 | フロントエンド要求 | 現在のバックエンド | **🚩 不足部分** |
|------|------------------|-------------------|------------------|
| **エンドポイント** | `GET /api/disasters` | ❌ 存在しない | **✅ 公開API作成必要** |
| **リスト取得** | 災害一覧 + メタ情報 | Agent間通信のみ | **✅ 一般向けAPI必要** |
| **フィルタリング** | 地域・時間・重要度別 | ❌ 未対応 | **✅ クエリパラメータ対応** |
| **ページネーション** | page, limit, total | ❌ 未対応 | **✅ ページング機能** |

**🏁 必要なレスポンス例:**
```json
{
  "disasters": [...],
  "total_count": 25,
  "current_page": 1,
  "total_pages": 3,
  "filters_applied": {
    "prefecture": "北海道",
    "severity": "high"
  }
}
```

---

### **2. マップ表示用API**

| 項目 | フロントエンド要求 | 現在のバックエンド | **🚩 不足部分** |
|------|------------------|-------------------|------------------|
| **軽量データ** | 座標 + 基本情報のみ | ❌ 未対応 | **✅ マップ専用API** |
| **地図境界情報** | bounds情報 | ❌ 未対応 | **✅ 表示範囲計算** |
| **クラスタリング** | 密集地域の統合表示 | ❌ 未対応 | **✅ クラスタリング機能** |

**🏁 必要なレスポンス例:**
```json
{
  "markers": [
    {
      "id": "d001",
      "lat": 43.0642,
      "lng": 141.3469,
      "severity": "high",
      "type": "earthquake",
      "title": "地震（震度5弱）"
    }
  ],
  "bounds": {
    "north": 45.0, "south": 40.0,
    "east": 145.0, "west": 135.0
  }
}
```

---

### **3. リアルタイム更新**

| 項目 | フロントエンド要求 | 現在のバックエンド | **🚩 不足部分** |
|------|------------------|-------------------|------------------|
| **WebSocket** | リアルタイム通知 | ❌ 未対応 | **✅ WebSocket実装** |
| **Server-Sent Events** | 一方向ストリーム | ❌ 未対応 | **✅ SSE実装** |
| **更新通知** | 新規・更新・解決通知 | ❌ 未対応 | **✅ イベント配信** |

**🏁 必要なWebSocketメッセージ例:**
```json
{
  "type": "disaster_update",
  "action": "created",
  "data": {
    "disaster_id": "d001",
    "title": "新しい地震情報",
    "severity": "high"
  }
}
```

---

### **4. 警報・アラート管理**

| 項目 | フロントエンド要求 | 現在のバックエンド | **🚩 不足部分** |
|------|------------------|-------------------|------------------|
| **アクティブ警報** | 現在有効な警報一覧 | 部分的対応 | **✅ 公開API化** |
| **地域フィルタ** | 特定地域の警報のみ | ❌ 未対応 | **✅ 地域絞り込み** |
| **重要度レベル** | critical/warning/info | 部分的対応 | **✅ レベル詳細化** |
| **行動指針** | 具体的な対処法 | ❌ 未対応 | **✅ アクション情報** |

---

### **5. ダッシュボード統計**

| 項目 | フロントエンド要求 | 現在のバックエンド | **🚩 不足部分** |
|------|------------------|-------------------|------------------|
| **統計データ** | 災害件数・影響人数等 | Support Agent部分対応 | **✅ 包括的統計API** |
| **トレンド分析** | 時間別・種類別推移 | ❌ 未対応 | **✅ トレンド計算** |
| **リアルタイム更新** | 統計の自動更新 | ❌ 未対応 | **✅ キャッシュ + 更新機能** |

---

## 🎯 **優先度別実装推奨事項**

### **🔴 最高優先度（即時実装必要）**
1. **`GET /api/public/disasters`** - 災害一覧取得
2. **`GET /api/public/disasters/{id}`** - 災害詳細取得
3. **`GET /api/public/alerts`** - アクティブ警報取得
4. **基本的なフィルタリング機能** (地域・時間・重要度)

### **🟡 高優先度（1週間以内）**
1. **`GET /api/public/disasters/map-data`** - マップ表示用軽量API
2. **WebSocket接続** - リアルタイム更新
3. **ページネーション機能**
4. **`GET /api/public/dashboard/stats`** - ダッシュボード統計

### **🟢 中優先度（2週間以内）**
1. **高度なフィルタリング**
2. **クラスタリング機能**
3. **APIレート制限**
4. **キャッシュ機能**

---

## 📝 **推奨実装アプローチ**

### **1. API Gateway層の追加**
```
Frontend → API Gateway → 既存Agents
```
- 既存のAgent APIをラップ
- 公開API用の認証・認可
- レスポンスフォーマット統一

### **2. 段階的実装**
1. **Phase 1**: 基本的なCRUD API
2. **Phase 2**: リアルタイム機能
3. **Phase 3**: 高度な機能（統計・分析）

### **3. 技術スタック推奨**
- **API Gateway**: FastAPI + Redis (キャッシュ)
- **リアルタイム**: WebSocket + Server-Sent Events
- **データベース**: Firestore (既存) + Redis (キャッシュ)

---

## 📊 **実装工数見積もり**

| 機能カテゴリ | 工数(人日) | 説明 |
|-------------|-----------|------|
| **基本API実装** | 5-7日 | CRUD + フィルタリング |
| **リアルタイム機能** | 3-5日 | WebSocket + SSE |
| **マップ最適化** | 2-3日 | 軽量化 + クラスタリング |
| **統計・ダッシュボード** | 4-6日 | 集計 + トレンド分析 |
| **テスト・文書化** | 2-3日 | API文書 + テストケース |
| **合計** | **16-24日** | 約3-4週間 |

---

## 🚀 **Next Steps**

### **即座に開始可能**
1. **Mock APIとの整合性確認** - 既存のsimple_backend.pyを参考
2. **API Gateway設計** - エンドポイント設計書作成
3. **データモデル調整** - フロントエンド要求に合わせた調整

### **チーム連携**
1. **フロントエンドチーム**: 必要なAPIの詳細仕様確認
2. **バックエンドチーム**: 既存Agentとの統合方法検討
3. **DevOpsチーム**: デプロイ・監視設定

---

**📌 この文書は、フロントエンドとバックエンドの連携をスムーズにし、ユーザーエクスペリエンスを向上させるための重要な指針です。**

---

# 🤖 **GenAI実装ガイド - 詳細コード変更指示**

## 📂 **ファイル構造と実装計画**

### **新規作成が必要なファイル**
```
Emergency-Aid-System/
├── api_gateway/
│   ├── main.py                    # メインAPIゲートウェイ
│   ├── routers/
│   │   ├── disasters.py          # 災害関連API
│   │   ├── alerts.py             # 警報関連API
│   │   ├── dashboard.py          # ダッシュボードAPI
│   │   └── websocket.py          # リアルタイム通信
│   ├── models/
│   │   ├── public_api.py         # 公開API用データモデル
│   │   └── responses.py          # レスポンス型定義
│   ├── services/
│   │   ├── disaster_service.py   # 災害データ処理サービス
│   │   ├── alert_service.py      # 警報処理サービス
│   │   └── stats_service.py      # 統計処理サービス
│   └── utils/
│       ├── cache.py              # Redis キャッシュ
│       ├── filters.py            # フィルタリング機能
│       └── pagination.py         # ページネーション
```

---

## 🔧 **1. メインAPIゲートウェイ実装**

### **ファイル: `api_gateway/main.py`**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import redis
import logging
from datetime import datetime
import json

from routers import disasters, alerts, dashboard, websocket
from utils.cache import get_redis_client

app = FastAPI(
    title="Emergency Aid System - Public API",
    description="一般ユーザー向け災害情報API",
    version="1.0.0"
)

# CORS設定（本番環境では適切に制限）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では適切なオリジンのみ許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# レスポンス圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ルーター登録
app.include_router(disasters.router, prefix="/api/public", tags=["disasters"])
app.include_router(alerts.router, prefix="/api/public", tags=["alerts"])
app.include_router(dashboard.router, prefix="/api/public", tags=["dashboard"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.on_startup
async def startup_event():
    """アプリケーション起動時の初期化"""
    # Redis接続確認
    redis_client = get_redis_client()
    try:
        redis_client.ping()
        logging.info("Redis connection established")
    except Exception as e:
        logging.error(f"Redis connection failed: {e}")

@app.get("/")
async def root():
    return {
        "service": "Emergency Aid System Public API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "disasters": "/api/public/disasters",
            "alerts": "/api/public/alerts",
            "dashboard": "/api/public/dashboard",
            "websocket": "/ws/connect"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
```

---

## 🔧 **2. 災害情報API実装**

### **ファイル: `api_gateway/routers/disasters.py`**
```python
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import json

from ..models.public_api import DisasterResponse, DisasterDetailResponse, MapDataResponse
from ..services.disaster_service import DisasterService
from ..utils.pagination import PaginationParams, paginate_response
from ..utils.filters import DisasterFilters

router = APIRouter()
disaster_service = DisasterService()

@router.get("/disasters", response_model=DisasterResponse)
async def get_disasters(
    # ページネーション
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),

    # フィルタリング
    prefecture: Optional[str] = Query(None, description="都道府県"),
    city: Optional[str] = Query(None, description="市区町村"),
    disaster_type: Optional[str] = Query(None, description="災害種別"),
    severity: Optional[str] = Query(None, description="重要度 (high/medium/low)"),
    is_active: Optional[bool] = Query(None, description="アクティブかどうか"),

    # 時間範囲
    since: Optional[datetime] = Query(None, description="この時刻以降の災害"),
    until: Optional[datetime] = Query(None, description="この時刻以前の災害"),

    # ソート
    sort_by: str = Query("reported_at", description="ソート項目"),
    order: str = Query("desc", regex="^(asc|desc)$", description="ソート順")
):
    """
    災害一覧を取得

    このエンドポイントは既存のFirestoreデータを取得し、
    フロントエンド向けに整形して返します。
    """
    try:
        # フィルター条件構築
        filters = DisasterFilters(
            prefecture=prefecture,
            city=city,
            disaster_type=disaster_type,
            severity=severity,
            is_active=is_active,
            since=since,
            until=until
        )

        # データ取得
        disasters, total_count = await disaster_service.get_disasters(
            filters=filters,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit
        )

        # レスポンス構築
        return DisasterResponse(
            disasters=disasters,
            total_count=total_count,
            current_page=page,
            total_pages=(total_count + limit - 1) // limit,
            per_page=limit,
            filters_applied=filters.to_dict(),
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"災害情報取得エラー: {str(e)}")

@router.get("/disasters/{disaster_id}", response_model=DisasterDetailResponse)
async def get_disaster_detail(disaster_id: str):
    """
    災害詳細情報を取得

    関連する分析結果、タイムライン、支援情報も含めて返します。
    """
    try:
        # 基本情報取得
        disaster = await disaster_service.get_disaster_by_id(disaster_id)
        if not disaster:
            raise HTTPException(status_code=404, detail="災害情報が見つかりません")

        # 関連情報取得
        timeline = await disaster_service.get_disaster_timeline(disaster_id)
        analysis = await disaster_service.get_disaster_analysis(disaster_id)
        support_info = await disaster_service.get_support_info(disaster_id)
        related_feeds = await disaster_service.get_related_feeds(disaster_id)

        return DisasterDetailResponse(
            disaster=disaster,
            timeline=timeline,
            analysis=analysis,
            support_info=support_info,
            related_feeds=related_feeds,
            last_updated=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"災害詳細取得エラー: {str(e)}")

@router.get("/disasters/map-data", response_model=MapDataResponse)
async def get_map_data(
    # 地図範囲
    north: Optional[float] = Query(None, description="北緯"),
    south: Optional[float] = Query(None, description="南緯"),
    east: Optional[float] = Query(None, description="東経"),
    west: Optional[float] = Query(None, description="西経"),

    # フィルタ
    disaster_type: Optional[str] = Query(None, description="災害種別"),
    severity: Optional[str] = Query(None, description="重要度"),
    is_active: Optional[bool] = Query(True, description="アクティブのみ"),

    # クラスタリング
    cluster: bool = Query(True, description="クラスタリング有効")
):
    """
    マップ表示用の軽量化された災害データを取得

    大量のマーカーを効率的に表示するため、
    必要最小限の情報のみを返します。
    """
    try:
        # 地図範囲フィルタ
        bounds = None
        if all([north, south, east, west]):
            bounds = {
                "north": north, "south": south,
                "east": east, "west": west
            }

        # マップデータ取得
        markers = await disaster_service.get_map_markers(
            bounds=bounds,
            disaster_type=disaster_type,
            severity=severity,
            is_active=is_active,
            cluster=cluster
        )

        # 全体の境界計算
        if markers:
            lats = [m["lat"] for m in markers]
            lngs = [m["lng"] for m in markers]
            computed_bounds = {
                "north": max(lats),
                "south": min(lats),
                "east": max(lngs),
                "west": min(lngs)
            }
        else:
            computed_bounds = bounds or {
                "north": 45.0, "south": 30.0,
                "east": 150.0, "west": 130.0
            }

        return MapDataResponse(
            markers=markers,
            bounds=computed_bounds,
            total_markers=len(markers),
            clustered=cluster,
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マップデータ取得エラー: {str(e)}")
```

---

## 🔧 **3. 災害データサービス実装**

### **ファイル: `api_gateway/services/disaster_service.py`**
```python
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from google.cloud import firestore
import json

from ..utils.cache import get_redis_client
from ..utils.filters import DisasterFilters

class DisasterService:
    def __init__(self):
        self.db = firestore.Client()
        self.redis = get_redis_client()
        self.logger = logging.getLogger(__name__)

    async def get_disasters(
        self,
        filters: DisasterFilters,
        sort_by: str = "reported_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        災害一覧を取得（フィルタリング・ページネーション対応）

        既存のFirestoreコレクションからデータを取得し、
        フロントエンド向けに整形します。
        """
        try:
            # キャッシュキー生成
            cache_key = f"disasters:{filters.cache_key()}:{sort_by}:{order}:{page}:{limit}"

            # キャッシュから取得試行
            cached = self.redis.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for disasters: {cache_key}")
                return json.loads(cached)

            # Firestoreクエリ構築
            query = self.db.collection('disasters')

            # フィルタ適用
            if filters.prefecture:
                query = query.where('location.admin', '>=', filters.prefecture)
                query = query.where('location.admin', '<', filters.prefecture + '\uf8ff')

            if filters.disaster_type:
                query = query.where('type', '==', filters.disaster_type)

            if filters.severity:
                severity_map = {"high": 0.7, "medium": 0.4, "low": 0.0}
                min_severity = severity_map.get(filters.severity, 0.0)
                max_severity = severity_map.get(filters.severity, 1.0) + 0.3
                query = query.where('severity', '>=', min_severity)
                query = query.where('severity', '<', max_severity)

            if filters.is_active is not None:
                query = query.where('is_active', '==', filters.is_active)

            if filters.since:
                query = query.where('detected_at', '>=', filters.since)

            if filters.until:
                query = query.where('detected_at', '<=', filters.until)

            # ソート適用
            direction = firestore.Query.DESCENDING if order == "desc" else firestore.Query.ASCENDING
            query = query.order_by(sort_by, direction=direction)

            # 全件数取得（キャッシュから）
            count_cache_key = f"disasters_count:{filters.cache_key()}"
            total_count = self.redis.get(count_cache_key)
            if not total_count:
                total_count = len(list(query.stream()))
                self.redis.setex(count_cache_key, 300, total_count)  # 5分キャッシュ
            else:
                total_count = int(total_count)

            # ページネーション適用
            offset = (page - 1) * limit
            docs = query.offset(offset).limit(limit).stream()

            # データ整形
            disasters = []
            for doc in docs:
                data = doc.to_dict()
                disaster = self._format_disaster_for_frontend(data, doc.id)
                disasters.append(disaster)

            result = (disasters, total_count)

            # キャッシュに保存（1分）
            self.redis.setex(cache_key, 60, json.dumps(result, default=str))

            return result

        except Exception as e:
            self.logger.error(f"Error getting disasters: {e}")
            raise

    async def get_disaster_by_id(self, disaster_id: str) -> Optional[Dict]:
        """災害詳細情報を取得"""
        try:
            # キャッシュ確認
            cache_key = f"disaster_detail:{disaster_id}"
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Firestoreから取得
            doc_ref = self.db.collection('disasters').document(disaster_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            disaster = self._format_disaster_for_frontend(doc.to_dict(), disaster_id)

            # キャッシュに保存（5分）
            self.redis.setex(cache_key, 300, json.dumps(disaster, default=str))

            return disaster

        except Exception as e:
            self.logger.error(f"Error getting disaster {disaster_id}: {e}")
            raise

    async def get_disaster_timeline(self, disaster_id: str) -> List[Dict]:
        """災害のタイムラインを取得"""
        try:
            # 複数のコレクションから時系列データを収集
            timeline = []

            # 1. 検知イベント
            timeline.append({
                "timestamp": datetime.utcnow(),  # 実際の検知時刻を使用
                "event_type": "detection",
                "title": "災害検知",
                "description": "自動システムにより災害を検知しました",
                "source": "detection_agent"
            })

            # 2. 分析結果
            analysis_docs = self.db.collection('analysis_results')\
                .where('event_id', '==', disaster_id)\
                .order_by('generated_at')\
                .stream()

            for doc in analysis_docs:
                data = doc.to_dict()
                timeline.append({
                    "timestamp": data.get('generated_at'),
                    "event_type": "analysis",
                    "title": "影響分析完了",
                    "description": f"被害規模: {data.get('severity', 'unknown')}",
                    "source": "analyzer_agent"
                })

            # 3. 支援情報
            support_docs = self.db.collection('support_reports')\
                .where('event_id', '==', disaster_id)\
                .order_by('generated_at')\
                .stream()

            for doc in support_docs:
                data = doc.to_dict()
                timeline.append({
                    "timestamp": data.get('generated_at'),
                    "event_type": "support",
                    "title": "支援分析完了",
                    "description": "支援計画が策定されました",
                    "source": "support_agent"
                })

            # 時系列ソート
            timeline.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)

            return timeline

        except Exception as e:
            self.logger.error(f"Error getting timeline for {disaster_id}: {e}")
            return []

    async def get_map_markers(
        self,
        bounds: Optional[Dict] = None,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = True,
        cluster: bool = True
    ) -> List[Dict]:
        """マップ表示用の軽量化マーカーデータを取得"""
        try:
            # キャッシュキー
            cache_key = f"map_markers:{bounds}:{disaster_type}:{severity}:{is_active}:{cluster}"
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Firestoreクエリ
            query = self.db.collection('disasters')

            if is_active is not None:
                query = query.where('is_active', '==', is_active)

            if disaster_type:
                query = query.where('type', '==', disaster_type)

            # 重要度フィルタ
            if severity:
                severity_map = {"high": 0.7, "medium": 0.4, "low": 0.0}
                min_severity = severity_map.get(severity, 0.0)
                query = query.where('severity', '>=', min_severity)

            docs = query.stream()

            markers = []
            for doc in docs:
                data = doc.to_dict()
                location = data.get('location', {})

                # 地図範囲フィルタ（Firestoreでは複雑なため、後処理）
                if bounds:
                    lat = location.get('lat', 0)
                    lng = location.get('lng', 0)
                    if not (bounds['south'] <= lat <= bounds['north'] and
                            bounds['west'] <= lng <= bounds['east']):
                        continue

                # 軽量化されたマーカーデータ
                marker = {
                    "id": doc.id,
                    "lat": location.get('lat', 0),
                    "lng": location.get('lng', 0),
                    "type": data.get('type', 'other'),
                    "severity": self._get_severity_level(data.get('severity', 0)),
                    "title": data.get('summary', '災害情報'),
                    "is_active": data.get('is_active', False),
                    "reported_at": data.get('detected_at')
                }
                markers.append(marker)

            # クラスタリング処理（簡易版）
            if cluster and len(markers) > 50:
                markers = self._cluster_markers(markers)

            # キャッシュに保存（2分）
            self.redis.setex(cache_key, 120, json.dumps(markers, default=str))

            return markers

        except Exception as e:
            self.logger.error(f"Error getting map markers: {e}")
            return []

    def _format_disaster_for_frontend(self, data: Dict, doc_id: str) -> Dict:
        """Firestoreデータをフロントエンド用に整形"""
        location = data.get('location', {})

        return {
            "id": doc_id,
            "title": data.get('summary', '災害情報'),
            "type": data.get('type', 'other'),
            "location": {
                "lat": location.get('lat', 0),
                "lng": location.get('lng', 0),
                "admin": location.get('admin', '不明')
            },
            "severity": self._get_severity_level(data.get('severity', 0)),
            "confidence": data.get('confidence', 0),
            "is_active": data.get('is_active', False),
            "reported_at": data.get('detected_at'),
            "last_updated": data.get('updated_at', data.get('detected_at')),
            "description": data.get('summary', ''),
            "source": data.get('source', [])
        }

    def _get_severity_level(self, severity_score: float) -> str:
        """重要度スコアをレベルに変換"""
        if severity_score >= 0.7:
            return "high"
        elif severity_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _cluster_markers(self, markers: List[Dict]) -> List[Dict]:
        """簡易マーカークラスタリング"""
        # 実装は省略（本格的なクラスタリングアルゴリズムを実装）
        # 近接するマーカーを統合し、クラスター情報を追加
        return markers
```

---

## 🔧 **4. データモデル定義**

### **ファイル: `api_gateway/models/public_api.py`**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class LocationModel(BaseModel):
    lat: float = Field(description="緯度")
    lng: float = Field(description="経度")
    admin: str = Field(description="行政区域名")

class DisasterModel(BaseModel):
    id: str = Field(description="災害ID")
    title: str = Field(description="災害タイトル")
    type: str = Field(description="災害種別")
    location: LocationModel
    severity: str = Field(description="重要度レベル (high/medium/low)")
    confidence: float = Field(ge=0.0, le=1.0, description="信頼度")
    is_active: bool = Field(description="アクティブ状態")
    reported_at: datetime = Field(description="報告日時")
    last_updated: datetime = Field(description="最終更新日時")
    description: str = Field(description="詳細説明")
    source: List[str] = Field(description="情報源")

class DisasterResponse(BaseModel):
    disasters: List[DisasterModel]
    total_count: int = Field(description="総件数")
    current_page: int = Field(description="現在のページ")
    total_pages: int = Field(description="総ページ数")
    per_page: int = Field(description="1ページあたりの件数")
    filters_applied: Dict[str, Any] = Field(description="適用されたフィルタ")
    last_updated: datetime = Field(description="データ最終更新時刻")

class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str = Field(description="イベントタイプ")
    title: str = Field(description="イベントタイトル")
    description: str = Field(description="イベント詳細")
    source: str = Field(description="情報源")

class SupportInfo(BaseModel):
    evacuation_centers: List[Dict] = Field(description="避難所情報")
    emergency_contacts: List[Dict] = Field(description="緊急連絡先")
    transport_status: List[Dict] = Field(description="交通状況")
    medical_facilities: List[Dict] = Field(description="医療機関情報")

class DisasterDetailResponse(BaseModel):
    disaster: DisasterModel
    timeline: List[TimelineEvent] = Field(description="時系列イベント")
    analysis: Dict[str, Any] = Field(description="分析結果")
    support_info: SupportInfo = Field(description="支援情報")
    related_feeds: List[Dict] = Field(description="関連フィード")
    last_updated: datetime

class MapMarker(BaseModel):
    id: str
    lat: float
    lng: float
    type: str
    severity: str
    title: str
    is_active: bool
    reported_at: Optional[datetime]

class MapBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float

class MapDataResponse(BaseModel):
    markers: List[MapMarker]
    bounds: MapBounds
    total_markers: int = Field(description="マーカー総数")
    clustered: bool = Field(description="クラスタリング適用済みか")
    last_updated: datetime
```

---

## 🔧 **5. WebSocket実装**

### **ファイル: `api_gateway/routers/websocket.py`**
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_subscriptions: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.user_subscriptions:
            del self.user_subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # 切断されたコネクションを削除
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_subscribed(self, message: dict, filter_func=None):
        """サブスクリプション条件に合致するクライアントにのみ送信"""
        disconnected = []
        for connection in self.active_connections:
            try:
                # サブスクリプション条件チェック
                subscriptions = self.user_subscriptions.get(connection, {})
                if filter_func and not filter_func(subscriptions, message):
                    continue

                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting to subscribed: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()
            message = json.loads(data)

            # メッセージタイプに応じて処理
            message_type = message.get("type")

            if message_type == "subscribe":
                # サブスクリプション設定
                subscriptions = message.get("subscriptions", {})
                manager.user_subscriptions[websocket] = subscriptions

                await manager.send_personal_message({
                    "type": "subscription_confirmed",
                    "subscriptions": subscriptions,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)

            elif message_type == "ping":
                # ハートビート
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)

            elif message_type == "get_status":
                # 現在のステータス取得
                await manager.send_personal_message({
                    "type": "status",
                    "connected_clients": len(manager.active_connections),
                    "your_subscriptions": manager.user_subscriptions.get(websocket, {}),
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# 災害情報更新時に呼び出される関数
async def broadcast_disaster_update(disaster_data: dict, action: str):
    """
    災害情報の更新をWebSocket経由で配信

    Args:
        disaster_data: 災害データ
        action: "created" | "updated" | "resolved"
    """
    message = {
        "type": "disaster_update",
        "action": action,
        "data": disaster_data,
        "timestamp": datetime.utcnow().isoformat()
    }

    # サブスクリプション条件に基づく配信
    def filter_func(subscriptions, message):
        # 地域フィルタ
        if "prefectures" in subscriptions:
            disaster_prefecture = message["data"].get("location", {}).get("admin", "")
            if not any(pref in disaster_prefecture for pref in subscriptions["prefectures"]):
                return False

        # 重要度フィルタ
        if "min_severity" in subscriptions:
            severity_map = {"low": 1, "medium": 2, "high": 3}
            disaster_severity = severity_map.get(message["data"].get("severity", "low"), 1)
            min_severity = severity_map.get(subscriptions["min_severity"], 1)
            if disaster_severity < min_severity:
                return False

        return True

    await manager.broadcast_to_subscribed(message, filter_func)

# アラート配信
async def broadcast_alert(alert_data: dict):
    """緊急アラートの配信"""
    message = {
        "type": "emergency_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }

    # 緊急アラートは全員に配信
    await manager.broadcast(message)
```

---

## 🔧 **6. キャッシュとユーティリティ**

### **ファイル: `api_gateway/utils/cache.py`**
```python
import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """Redis クライアントのシングルトン取得"""
    global _redis_client

    if _redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_db = int(os.getenv("REDIS_DB", 0))
        redis_password = os.getenv("REDIS_PASSWORD")

        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        logger.info(f"Redis client initialized: {redis_host}:{redis_port}")

    return _redis_client

def cache_key_builder(*args) -> str:
    """キャッシュキー構築ヘルパー"""
    return ":".join(str(arg) for arg in args if arg is not None)
```

### **ファイル: `api_gateway/utils/filters.py`**
```python
from typing import Optional
from datetime import datetime
import hashlib

class DisasterFilters:
    def __init__(
        self,
        prefecture: Optional[str] = None,
        city: Optional[str] = None,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ):
        self.prefecture = prefecture
        self.city = city
        self.disaster_type = disaster_type
        self.severity = severity
        self.is_active = is_active
        self.since = since
        self.until = until

    def to_dict(self) -> dict:
        """フィルタ情報を辞書形式で返す"""
        return {
            "prefecture": self.prefecture,
            "city": self.city,
            "disaster_type": self.disaster_type,
            "severity": self.severity,
            "is_active": self.is_active,
            "since": self.since.isoformat() if self.since else None,
            "until": self.until.isoformat() if self.until else None
        }

    def cache_key(self) -> str:
        """キャッシュキー生成"""
        filter_str = "|".join([
            str(self.prefecture or ""),
            str(self.city or ""),
            str(self.disaster_type or ""),
            str(self.severity or ""),
            str(self.is_active or ""),
            str(self.since or ""),
            str(self.until or "")
        ])
        return hashlib.md5(filter_str.encode()).hexdigest()
```

---

## 🔧 **7. 既存Agentとの統合**

### **既存ファイルの修正: `agents/orchestrator/main.py`**

```python
# 既存のコードの最後に追加

from api_gateway.routers.websocket import broadcast_disaster_update

async def run_orchestration(event: DisasterEvent):
    try:
        logger.info(f"Starting orchestration for event: {event.event_id}")
        result = await orchestrator.process_disaster_event(event)
        logger.info(f"Orchestration completed for event: {event.event_id}")

        # 🆕 WebSocket経由でリアルタイム配信
        disaster_data = {
            "id": event.event_id,
            "type": event.type.value,
            "location": {
                "lat": event.location.lat,
                "lng": event.location.lng,
                "admin": event.location.admin
            },
            "severity": _get_severity_level(event.severity),
            "summary": event.summary,
            "is_active": True
        }
        await broadcast_disaster_update(disaster_data, "created")

    except Exception as e:
        logger.error(f"Orchestration failed for event {event.event_id}: {e}")

def _get_severity_level(severity_score: float) -> str:
    """重要度スコアをレベルに変換"""
    if severity_score >= 0.7:
        return "high"
    elif severity_score >= 0.4:
        return "medium"
    else:
        return "low"
```

---

## 🔧 **8. デプロイメント設定**

### **ファイル: `api_gateway/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8081

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
```

### **ファイル: `api_gateway/requirements.txt`**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
redis==5.0.1
google-cloud-firestore==2.14.0
pydantic==2.5.0
python-multipart==0.0.6
```

### **ファイル: `api_gateway/docker-compose.yml`**
```yaml
version: '3.8'

services:
  api-gateway:
    build: .
    ports:
      - "8081:8081"
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    volumes:
      - ./service-account-key.json:/app/service-account-key.json
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## 📋 **実装チェックリスト**

### **Phase 1: 基本API (1週間)**
- [ ] `api_gateway/main.py` 作成
- [ ] `routers/disasters.py` 作成
- [ ] `services/disaster_service.py` 作成
- [ ] `models/public_api.py` 作成
- [ ] `utils/cache.py` 作成
- [ ] `utils/filters.py` 作成
- [ ] Redis セットアップ
- [ ] 基本的なテスト作成

### **Phase 2: リアルタイム機能 (3-5日)**
- [ ] `routers/websocket.py` 作成
- [ ] 既存Agent との統合
- [ ] WebSocket テスト
- [ ] フロントエンド連携テスト

### **Phase 3: 高度な機能 (1週間)**
- [ ] `routers/alerts.py` 作成
- [ ] `routers/dashboard.py` 作成
- [ ] クラスタリング機能実装
- [ ] APIレート制限
- [ ] 性能最適化

### **Phase 4: 本番対応 (3-5日)**
- [ ] セキュリティ強化
- [ ] 監視・ログ設定
- [ ] 本番デプロイ設定
- [ ] 文書化完成

---

## ⚡ **GenAI実装時の注意点**

1. **既存データ構造の保持**: Firestoreの既存コレクション構造を変更せず、API層で変換
2. **段階的実装**: 全機能を一度に実装せず、段階的にリリース
3. **エラーハンドリング**: 各APIで適切な例外処理と ログ記録
4. **キャッシュ戦略**: Redisを活用した効果的なキャッシュ
5. **セキュリティ**: 本番環境では適切な認証・認可を実装

この詳細ガイドに従って実装すれば、フロントエンドの要求を満たす堅牢なAPIが構築できます。