#!/usr/bin/env python3
"""
災害情報システム API Gateway ローカル起動スクリプト
"""
import os
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """環境チェック"""
    logger.info("🔍 環境チェック開始...")
    
    # Google Cloud Project設定確認
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.warning("⚠️  GOOGLE_CLOUD_PROJECT環境変数が設定されていません")
        logger.info("以下のコマンドで設定してください:")
        logger.info("export GOOGLE_CLOUD_PROJECT=your-project-id")
    else:
        logger.info(f"✅ GOOGLE_CLOUD_PROJECT: {project_id}")
    
    # 認証確認
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and Path(creds_path).exists():
        logger.info(f"✅ 認証ファイル: {creds_path}")
    else:
        logger.warning("⚠️  GOOGLE_APPLICATION_CREDENTIALS が設定されていないか、ファイルが存在しません")
        logger.info("以下のコマンドで認証してください:")
        logger.info("gcloud auth application-default login")
    
    # 依存関係確認
    try:
        import fastapi
        import uvicorn
        import google.cloud.firestore
        logger.info("✅ 必要なパッケージがインストールされています")
    except ImportError as e:
        logger.error(f"❌ 必要なパッケージが不足しています: {e}")
        logger.info("以下のコマンドでインストールしてください:")
        logger.info("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """メイン関数"""
    logger.info("🚀 災害情報システム API Gateway 起動中...")
    
    if not check_environment():
        logger.error("❌ 環境チェックに失敗しました")
        sys.exit(1)
    
    # サーバー起動
    import uvicorn
    
    logger.info("🌐 サーバーを起動しています...")
    logger.info("📡 API: http://localhost:8081")
    logger.info("📖 Docs: http://localhost:8081/docs")
    logger.info("🔌 WebSocket: ws://localhost:8081/ws/connect")
    logger.info("✋ 停止: Ctrl+C")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()