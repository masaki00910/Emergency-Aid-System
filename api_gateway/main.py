from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
from datetime import datetime
import os

from routers import disasters, websocket
from services.disaster_service import DisasterService

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Emergency Aid System - Public API",
    description="一般ユーザー向け災害情報API（WebSocket対応）",
    version="1.0.0"
)

# CORS設定（開発環境用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# レスポンス圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ルーター登録
app.include_router(disasters.router, prefix="/api/public", tags=["disasters"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.on_startup
async def startup_event():
    """アプリケーション起動時の初期化"""
    logger.info("Emergency Aid System API Gateway starting up...")
    
    # Firestore接続確認
    try:
        disaster_service = DisasterService()
        # テスト用の軽量クエリでFirestore接続確認
        test_query = disaster_service.db.collection('disasters').limit(1)
        list(test_query.stream())
        logger.info("✅ Firestore connection established")
    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")

@app.get("/")
async def root():
    return {
        "service": "Emergency Aid System Public API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["REST API", "WebSocket", "Real-time updates"],
        "endpoints": {
            "disasters": "/api/public/disasters",
            "disaster_detail": "/api/public/disasters/{id}",
            "map_data": "/api/public/disasters/map-data",
            "websocket": "/ws/connect"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081, reload=True)