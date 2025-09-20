from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

class DisasterService:
    def __init__(self):
        self.db = firestore.Client()
        self.logger = logging.getLogger(__name__)

    async def get_disasters(
        self,
        page: int = 1,
        limit: int = 20,
        prefecture: Optional[str] = None,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        sort_by: str = "detected_at",
        order: str = "desc"
    ) -> Tuple[List[Dict], int]:
        """
        災害一覧を取得（フィルタリング・ページネーション対応）
        シンプルプロキシ版：Firestoreから直接取得
        """
        try:
            # Firestoreクエリ構築
            query = self.db.collection('disasters')

            # フィルタ適用
            if prefecture:
                query = query.where('location.admin', '>=', prefecture)
                query = query.where('location.admin', '<', prefecture + '\uf8ff')

            if disaster_type:
                query = query.where('type', '==', disaster_type)

            if is_active is not None:
                query = query.where('is_active', '==', is_active)

            if since:
                query = query.where('detected_at', '>=', since)

            if until:
                query = query.where('detected_at', '<=', until)

            # ソート適用
            direction = firestore.Query.DESCENDING if order == "desc" else firestore.Query.ASCENDING
            query = query.order_by(sort_by, direction=direction)

            # 全件数取得（簡易版）
            all_docs = list(query.stream())
            total_count = len(all_docs)

            # ページネーション適用
            offset = (page - 1) * limit
            paginated_docs = all_docs[offset:offset + limit]

            # データ整形
            disasters = []
            for doc in paginated_docs:
                data = doc.to_dict()
                disaster = self._format_disaster_for_frontend(data, doc.id)
                
                # 重要度フィルタ（後処理）
                if severity and disaster['severity'] != severity:
                    continue
                    
                disasters.append(disaster)

            return disasters, total_count

        except Exception as e:
            self.logger.error(f"Error getting disasters: {e}")
            raise

    async def get_disaster_by_id(self, disaster_id: str) -> Optional[Dict]:
        """災害詳細情報を取得"""
        try:
            doc_ref = self.db.collection('disasters').document(disaster_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            disaster = self._format_disaster_for_frontend(doc.to_dict(), disaster_id)
            return disaster

        except Exception as e:
            self.logger.error(f"Error getting disaster {disaster_id}: {e}")
            raise

    async def get_map_markers(
        self,
        bounds: Optional[Dict] = None,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Dict]:
        """マップ表示用の軽量化マーカーデータを取得"""
        try:
            # Firestoreクエリ
            query = self.db.collection('disasters')

            if is_active is not None:
                query = query.where('is_active', '==', is_active)

            if disaster_type:
                query = query.where('type', '==', disaster_type)

            # 最新50件に制限（パフォーマンス考慮）
            query = query.order_by('detected_at', direction=firestore.Query.DESCENDING).limit(50)

            docs = query.stream()

            markers = []
            for doc in docs:
                data = doc.to_dict()
                location = data.get('location', {})

                # 地図範囲フィルタ（後処理）
                if bounds:
                    lat = location.get('lat', 0)
                    lng = location.get('lng', 0)
                    if not (bounds['south'] <= lat <= bounds['north'] and
                            bounds['west'] <= lng <= bounds['east']):
                        continue

                # 重要度フィルタ（後処理）
                disaster_severity = self._get_severity_level(data.get('severity', 0))
                if severity and disaster_severity != severity:
                    continue

                # 軽量化されたマーカーデータ
                marker = {
                    "id": doc.id,
                    "lat": location.get('lat', 0),
                    "lng": location.get('lng', 0),
                    "type": data.get('type', 'other'),
                    "severity": disaster_severity,
                    "title": data.get('summary', '災害情報'),
                    "is_active": data.get('is_active', False),
                    "reported_at": data.get('detected_at')
                }
                markers.append(marker)

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