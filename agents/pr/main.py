import asyncio
import os
import json
import base64
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from pr_agent import PRAgent
from shared.models.disaster import AgentTask


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PR Agent")
pr_agent = PRAgent()


@app.get("/health")
async def health_check():
    is_healthy = await pr_agent.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/generate")
async def generate_pr_content(task_data: dict, background_tasks: BackgroundTasks):
    try:
        task = AgentTask(**task_data)
        background_tasks.add_task(run_pr_generation, task)
        
        return JSONResponse({
            "message": "PR content generation started",
            "task_id": task.task_id
        })
        
    except Exception as e:
        logger.error(f"Failed to start PR generation: {e}")
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
                
                background_tasks.add_task(run_pr_generation, task)
                
                return JSONResponse({"message": "PR generation triggered via Pub/Sub"})
        
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
    except Exception as e:
        logger.error(f"Pub/Sub trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_pr_generation(task: AgentTask):
    try:
        logger.info(f"Starting PR generation task: {task.task_id}")
        result = await pr_agent.process(task)
        
        await pr_agent.update_task_status(
            task.task_id,
            result.status,
            result.result,
            result.errors
        )
        
        logger.info(f"PR generation task completed: {task.task_id}")
        
    except Exception as e:
        logger.error(f"PR generation task failed: {e}")


@app.get("/events/{event_id}/bulletins")
async def get_event_bulletins(event_id: str):
    try:
        bulletins_ref = pr_agent.gcp.firestore.collection('bulletins').where('event_id', '==', event_id)
        bulletins = [doc.to_dict() for doc in bulletins_ref.stream()]
        
        return {"event_id": event_id, "bulletins": bulletins}
        
    except Exception as e:
        logger.error(f"Failed to get event bulletins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/latest")
async def get_latest_bulletins(limit: int = 10):
    try:
        bulletins_ref = (self.gcp.firestore.collection('bulletins')
                        .order_by('published_at', direction=firestore.Query.DESCENDING)
                        .limit(limit))
        bulletins = [doc.to_dict() for doc in bulletins_ref.stream()]
        
        return {"bulletins": bulletins}
        
    except Exception as e:
        logger.error(f"Failed to get latest bulletins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)