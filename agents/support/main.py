import asyncio
import os
import json
import base64
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from support_agent import SupportAgent
from shared.models.disaster import AgentTask


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Support Agent")
support_agent = SupportAgent()


@app.get("/health")
async def health_check():
    is_healthy = await support_agent.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/analyze")
async def analyze_support(task_data: dict, background_tasks: BackgroundTasks):
    """
    サポート分析の開始
    
    Args:
        task_data: 分析タスクデータ
    """
    try:
        task = AgentTask(**task_data)
        background_tasks.add_task(run_support_analysis, task)
        
        return JSONResponse({
            "message": "Support analysis started",
            "task_id": task.task_id
        })
        
    except Exception as e:
        logger.error(f"Failed to start support analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pubsub-trigger")
async def pubsub_trigger(request: Request, background_tasks: BackgroundTasks):
    """
    Pub/Sub経由でのサポート分析トリガー
    """
    try:
        request_json = await request.json()
        
        if 'message' in request_json:
            pubsub_message = request_json['message']
            if 'data' in pubsub_message:
                message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
                task_data = json.loads(message_data)
                task = AgentTask(**task_data)
                
                background_tasks.add_task(run_support_analysis, task)
                
                return JSONResponse({"message": "Support analysis triggered via Pub/Sub"})
        
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
    except Exception as e:
        logger.error(f"Pub/Sub trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_support_analysis(task: AgentTask):
    """
    サポート分析の実行
    
    Args:
        task: 分析タスク
    """
    try:
        logger.info(f"Starting support analysis for task: {task.task_id}")
        result = await support_agent.process(task)
        
        # 結果をFirestoreに保存
        await support_agent.update_task_status(
            task.task_id,
            result.status,
            result.result,
            result.errors
        )
        
        logger.info(f"Support analysis completed for task: {task.task_id}")
        
    except Exception as e:
        logger.error(f"Support analysis failed for task {task.task_id}: {e}")


@app.get("/reports/{event_id}")
async def get_support_reports(event_id: str):
    """
    イベントのサポートレポート取得
    
    Args:
        event_id: イベントID
    """
    try:
        reports_ref = support_agent.gcp.firestore.collection('support_reports').where('event_id', '==', event_id)
        reports = [doc.to_dict() for doc in reports_ref.stream()]
        
        return {"event_id": event_id, "reports": reports}
        
    except Exception as e:
        logger.error(f"Failed to get support reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/summary")
async def get_dashboard_summary():
    """
    ダッシュボード用の要約データ取得
    
    TODO: Looker Studio連携用のデータ整形
    """
    try:
        # 直近の分析結果を取得
        recent_reports = []
        reports_ref = support_agent.gcp.firestore.collection('support_reports').order_by('generated_at', direction='DESCENDING').limit(10)
        
        for doc in reports_ref.stream():
            report_data = doc.to_dict()
            recent_reports.append({
                "report_id": report_data.get("report_id"),
                "event_id": report_data.get("event_id"),
                "generated_at": report_data.get("generated_at"),
                "summary": {
                    "psychological_impact": report_data.get("analysis_data", {}).get("psychological", {}),
                    "economic_impact": report_data.get("analysis_data", {}).get("economic", {})
                }
            })
        
        return {
            "recent_reports": recent_reports,
            "total_reports": len(recent_reports),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)