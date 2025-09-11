import asyncio
import os
import json
import base64
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from analyzer_agent import DisasterAnalyzerAgent
from shared.models.disaster import AgentTask


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("Analyzer Agent starting with enhanced logging")

app = FastAPI(title="Disaster Analyzer Agent")
analyzer = DisasterAnalyzerAgent()


@app.get("/health")
async def health_check():
    is_healthy = await analyzer.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/analyze")
async def analyze_disaster(task_data: dict, background_tasks: BackgroundTasks):
    try:
        task = AgentTask(**task_data)
        background_tasks.add_task(run_analysis, task)
        
        return JSONResponse({
            "message": "Analysis started",
            "task_id": task.task_id
        })
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pubsub-trigger")
async def pubsub_trigger(request: Request, background_tasks: BackgroundTasks):
    try:
        request_json = await request.json()
        
        if 'message' in request_json:
            pubsub_message = request_json['message']
            if 'data' in pubsub_message:
                message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
                task_data = json.loads(message_data)
                task = AgentTask(**task_data)
                
                background_tasks.add_task(run_analysis, task)
                
                return JSONResponse({"message": "Analysis triggered via Pub/Sub"})
        
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
    except Exception as e:
        logger.error(f"Pub/Sub trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis(task: AgentTask):
    try:
        logger.info(f"Starting analysis task: {task.task_id}")
        result = await analyzer.process(task)
        
        await analyzer.update_task_status(
            task.task_id,
            result.status,
            result.result,
            result.errors
        )
        
        logger.info(f"Analysis task completed: {task.task_id}")
        
    except Exception as e:
        logger.error(f"Analysis task failed: {e}")


@app.get("/events/{event_id}/analysis")
async def get_event_analysis(event_id: str):
    try:
        analysis_ref = analyzer.gcp.firestore.collection('analysis_results').where('event_id', '==', event_id)
        analyses = [doc.to_dict() for doc in analysis_ref.stream()]
        
        return {"event_id": event_id, "analyses": analyses}
        
    except Exception as e:
        logger.error(f"Failed to get event analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)