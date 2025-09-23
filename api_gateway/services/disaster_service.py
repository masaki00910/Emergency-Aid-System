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
        order: str = "desc",
        recent_only: bool = True  # デフォルトで24時間以内のみ
    ) -> Tuple[List[Dict], int]:
        """
        災害一覧を取得（フィルタリング・ページネーション対応）
        シンプルプロキシ版：Firestoreから直接取得
        """
        try:
            # Firestoreクエリ構築 (incidentsコレクションを使用)
            query = self.db.collection('incidents')

            # 24時間以内フィルタ（パフォーマンス大幅改善）
            if recent_only and not since:
                from datetime import timedelta
                last_24_hours = datetime.now() - timedelta(hours=24)
                query = query.where('detected_at', '>=', last_24_hours)
                self.logger.info(f"Applied 24h filter: {last_24_hours}")

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

            # パフォーマンス最適化: 必要最小限のクエリ実行
            # ページネーション用のクエリ（実際に必要なドキュメントのみ取得）
            offset = (page - 1) * limit
            paginated_query = query.limit(limit * 2)  # 多少多めに取得してoffsetの代替
            
            # stream()の代わりにget()を使用（より高速）
            paginated_docs = list(paginated_query.stream())[offset:offset + limit]
            
            # 総件数は推定値を使用（パフォーマンス優先）
            # 実際のドキュメント数ではなく、取得件数を総数として返す
            total_count = len(paginated_docs)
            if len(paginated_docs) == limit:
                total_count = limit * page + 1  # 次ページが存在することを示唆

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
            doc_ref = self.db.collection('incidents').document(disaster_id)
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
            # Firestoreクエリ (incidentsコレクションを使用)
            query = self.db.collection('incidents')

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
        """incidentsコレクションデータをフロントエンド用に整形"""
        location = data.get('location', {})

        # incidents特有のフィールドを処理
        is_active = self._determine_is_active(data)
        
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
            "is_active": is_active,
            "reported_at": data.get('detected_at'),
            "last_updated": data.get('last_bulletin_at', data.get('orchestration_started_at', data.get('detected_at'))),
            "description": data.get('summary', ''),
            "source": data.get('source', []),
            # incidents特有の追加情報
            "bulletins_count": len(data.get('bulletins', [])),
            "has_analysis": len(data.get('analysis_results', [])) > 0,
            "has_collected_info": len(data.get('collected_info', [])) > 0,
            "related_news_count": len(data.get('collected_info', [])),
            "orchestration_started_at": data.get('orchestration_started_at'),
            "last_bulletin_at": data.get('last_bulletin_at')
        }

    def _get_severity_level(self, severity_score: float) -> str:
        """重要度スコアをレベルに変換"""
        if severity_score >= 0.7:
            return "high"
        elif severity_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _determine_is_active(self, data: Dict) -> bool:
        """incidentデータからis_activeを判定"""
        # 明示的にis_activeが設定されている場合
        if 'is_active' in data:
            return data['is_active']
        
        # bulletinが最近作成されていればアクティブ
        last_bulletin_at = data.get('last_bulletin_at')
        if last_bulletin_at:
            try:
                from datetime import datetime, timedelta
                last_bulletin_time = datetime.fromisoformat(last_bulletin_at.replace('Z', '+00:00'))
                # 過去24時間以内にbulletinがあればアクティブ
                return (datetime.now() - last_bulletin_time) < timedelta(hours=24)
            except:
                pass
        
        # orchestrationが開始されていればアクティブとみなす
        return 'orchestration_started_at' in data