"""
既存エージェントとAPI Gatewayの統合ヘルパー
既存のOrchestratorから呼び出されるWebSocket配信機能
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class APIGatewayIntegration:
    """既存エージェントとAPI Gatewayの橋渡し"""
    
    def __init__(self):
        self.websocket_manager = None
        
    async def initialize_websocket_manager(self):
        """WebSocket管理クラスの初期化"""
        try:
            from routers.websocket import manager
            self.websocket_manager = manager
            logger.info("✅ WebSocket manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebSocket manager: {e}")
    
    async def notify_disaster_created(self, firestore_disaster_data: Dict[str, Any], disaster_id: str):
        """
        新しい災害が作成された時の通知
        
        Args:
            firestore_disaster_data: Firestoreから取得した災害データ
            disaster_id: 災害ID
        """
        if not self.websocket_manager:
            await self.initialize_websocket_manager()
            
        try:
            # Firestoreデータをフロントエンド用に変換
            frontend_data = self._convert_firestore_to_frontend(firestore_disaster_data, disaster_id)
            
            # WebSocket経由で配信
            if self.websocket_manager:
                from routers.websocket import broadcast_disaster_update
                await broadcast_disaster_update(frontend_data, "created")
                logger.info(f"📡 Broadcasted new disaster: {disaster_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast disaster creation: {e}")
    
    async def notify_disaster_updated(self, firestore_disaster_data: Dict[str, Any], disaster_id: str):
        """災害情報が更新された時の通知"""
        if not self.websocket_manager:
            await self.initialize_websocket_manager()
            
        try:
            frontend_data = self._convert_firestore_to_frontend(firestore_disaster_data, disaster_id)
            
            if self.websocket_manager:
                from routers.websocket import broadcast_disaster_update
                await broadcast_disaster_update(frontend_data, "updated")
                logger.info(f"📡 Broadcasted disaster update: {disaster_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to broadcast disaster update: {e}")
    
    async def notify_disaster_resolved(self, disaster_id: str):
        """災害が解決された時の通知"""
        if not self.websocket_manager:
            await self.initialize_websocket_manager()
            
        try:
            if self.websocket_manager:
                from routers.websocket import broadcast_disaster_update
                await broadcast_disaster_update({"id": disaster_id}, "resolved")
                logger.info(f"📡 Broadcasted disaster resolution: {disaster_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to broadcast disaster resolution: {e}")
    
    def _convert_firestore_to_frontend(self, firestore_data: Dict[str, Any], disaster_id: str) -> Dict[str, Any]:
        """Firestoreデータをフロントエンド用に変換"""
        location = firestore_data.get('location', {})
        
        return {
            "id": disaster_id,
            "title": firestore_data.get('summary', '災害情報'),
            "type": firestore_data.get('type', 'other'),
            "location": {
                "lat": location.get('lat', 0),
                "lng": location.get('lng', 0),
                "admin": location.get('admin', '不明')
            },
            "severity": self._get_severity_level(firestore_data.get('severity', 0)),
            "confidence": firestore_data.get('confidence', 0),
            "is_active": firestore_data.get('is_active', True),
            "reported_at": firestore_data.get('detected_at'),
            "last_updated": firestore_data.get('updated_at', firestore_data.get('detected_at')),
            "description": firestore_data.get('summary', ''),
            "source": firestore_data.get('source', [])
        }
    
    def _get_severity_level(self, severity_score: float) -> str:
        """重要度スコアをレベルに変換"""
        if severity_score >= 0.7:
            return "high"
        elif severity_score >= 0.4:
            return "medium"
        else:
            return "low"

# グローバルインスタンス
api_gateway_integration = APIGatewayIntegration()