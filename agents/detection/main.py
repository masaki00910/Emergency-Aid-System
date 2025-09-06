import asyncio
import os
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from detection_agent import DisasterDetectionAgent
from shared.models.disaster import AgentTask, TaskStatus


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Disaster Detection Agent")
detection_agent = DisasterDetectionAgent()


@app.get("/health")
async def health_check():
    is_healthy = await detection_agent.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/detect")
async def trigger_detection(background_tasks: BackgroundTasks):
    task = AgentTask(
        task_id=f"detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        event_id="",
        agent="disaster_detection",
        status=TaskStatus.PENDING,
        payload={"trigger": "manual"},
        created_at=datetime.utcnow()
    )
    
    background_tasks.add_task(run_detection, task)
    
    return JSONResponse({
        "message": "Detection started",
        "task_id": task.task_id
    })


async def run_detection(task: AgentTask):
    try:
        logger.info(f"Starting detection task: {task.task_id}")
        result = await detection_agent.process(task)
        logger.info(f"Detection task completed: {task.task_id}")
        
    except Exception as e:
        logger.error(f"Detection task failed: {e}")


@app.post("/pubsub-trigger")
async def pubsub_trigger(background_tasks: BackgroundTasks):
    task = AgentTask(
        task_id=f"detection_pubsub_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        event_id="",
        agent="disaster_detection",
        status=TaskStatus.PENDING,
        payload={"trigger": "pubsub"},
        created_at=datetime.utcnow()
    )
    
    background_tasks.add_task(run_detection, task)
    
    return JSONResponse({"message": "Detection triggered via Pub/Sub"})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)