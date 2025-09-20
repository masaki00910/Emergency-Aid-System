from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """WebSocket接続を管理するクラス"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_subscriptions: Dict[WebSocket, Dict] = {}
        self._connection_id_counter = 0

    async def connect(self, websocket: WebSocket):
        """新しいWebSocket接続を受け入れ"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self._connection_id_counter += 1
        
        logger.info(f"🔗 WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # 接続確認メッセージ送信
        await self.send_personal_message({
            "type": "connection_established",
            "message": "災害情報システムに接続しました",
            "connection_id": self._connection_id_counter,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """WebSocket接続を切断"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.user_subscriptions:
            del self.user_subscriptions[websocket]
        
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """特定のクライアントにメッセージ送信"""
        try:
            await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))
        except Exception as e:
            logger.error(f"❌ Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """全クライアントにブロードキャスト"""
        if not self.active_connections:
            logger.info("📡 No active connections for broadcast")
            return

        disconnected = []
        sent_count = 0
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str, ensure_ascii=False))
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # 切断されたコネクションを削除
        for conn in disconnected:
            self.disconnect(conn)
            
        logger.info(f"📡 Broadcast sent to {sent_count} connections")

    async def broadcast_to_subscribed(self, message: dict, filter_func=None):
        """サブスクリプション条件に合致するクライアントにのみ送信"""
        if not self.active_connections:
            return

        disconnected = []
        sent_count = 0
        
        for connection in self.active_connections:
            try:
                # サブスクリプション条件チェック
                subscriptions = self.user_subscriptions.get(connection, {})
                if filter_func and not filter_func(subscriptions, message):
                    continue

                await connection.send_text(json.dumps(message, default=str, ensure_ascii=False))
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Error broadcasting to subscribed: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)
            
        logger.info(f"📡 Targeted broadcast sent to {sent_count} connections")

# グローバル接続マネージャー
manager = ConnectionManager()

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント"""
    await manager.connect(websocket)
    
    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: dict):
    """WebSocketメッセージハンドラ"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # サブスクリプション設定
        subscriptions = message.get("subscriptions", {})
        manager.user_subscriptions[websocket] = subscriptions
        
        await manager.send_personal_message({
            "type": "subscription_confirmed",
            "subscriptions": subscriptions,
            "message": "サブスクリプションを設定しました",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        logger.info(f"📥 Subscription set: {subscriptions}")

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

    elif message_type == "unsubscribe":
        # サブスクリプション解除
        if websocket in manager.user_subscriptions:
            del manager.user_subscriptions[websocket]
        
        await manager.send_personal_message({
            "type": "unsubscribed",
            "message": "サブスクリプションを解除しました",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

# 災害情報更新時に呼び出される関数（外部から使用）
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
        if not subscriptions:
            return True  # サブスクリプション未設定の場合は全て配信

        # 地域フィルタ
        if "prefectures" in subscriptions:
            disaster_admin = message["data"].get("location", {}).get("admin", "")
            prefectures = subscriptions["prefectures"]
            if not any(pref in disaster_admin for pref in prefectures):
                return False

        # 重要度フィルタ
        if "min_severity" in subscriptions:
            severity_map = {"low": 1, "medium": 2, "high": 3}
            disaster_severity = severity_map.get(message["data"].get("severity", "low"), 1)
            min_severity = severity_map.get(subscriptions["min_severity"], 1)
            if disaster_severity < min_severity:
                return False

        # 災害種別フィルタ
        if "disaster_types" in subscriptions:
            disaster_type = message["data"].get("type", "")
            if disaster_type not in subscriptions["disaster_types"]:
                return False

        return True

    await manager.broadcast_to_subscribed(message, filter_func)

# 緊急アラート配信
async def broadcast_emergency_alert(alert_data: dict):
    """緊急アラートの配信（全員に送信）"""
    message = {
        "type": "emergency_alert",
        "data": alert_data,
        "priority": "high",
        "timestamp": datetime.utcnow().isoformat()
    }

    # 緊急アラートは全員に配信
    await manager.broadcast(message)

# 統計情報の配信
async def broadcast_stats_update(stats_data: dict):
    """統計情報の更新を配信"""
    message = {
        "type": "stats_update",
        "data": stats_data,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast(message)

# 接続数取得（デバッグ用）
def get_connection_count() -> int:
    """現在の接続数を取得"""
    return len(manager.active_connections)