import asyncio
import os
import json
import base64
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from info_collector_agent import InfoCollectorAgent
from shared.models.disaster import AgentTask


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Info Collector Agent")
info_collector = InfoCollectorAgent()


@app.get("/health")
async def health_check():
    is_healthy = await info_collector.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/collect")
async def collect_info(task_data: dict, background_tasks: BackgroundTasks):
    try:
        task = AgentTask(**task_data)
        background_tasks.add_task(run_collection, task)
        
        return JSONResponse({
            "message": "Info collection started",
            "task_id": task.task_id
        })
        
    except Exception as e:
        logger.error(f"Failed to start collection: {e}")
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
                
                background_tasks.add_task(run_collection, task)
                
                return JSONResponse({"message": "Collection triggered via Pub/Sub"})
        
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
    except Exception as e:
        logger.error(f"Pub/Sub trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_collection(task: AgentTask):
    try:
        logger.info(f"Starting collection task: {task.task_id}")
        result = await info_collector.process(task)
        
        await info_collector.update_task_status(
            task.task_id,
            result.status,
            result.result,
            result.errors
        )
        
        logger.info(f"Collection task completed: {task.task_id}")
        
    except Exception as e:
        logger.error(f"Collection task failed: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)