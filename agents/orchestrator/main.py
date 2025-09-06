import asyncio
import os
import json
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from google.cloud import pubsub_v1

from orchestrator_agent import DisasterResponseOrchestrator
from shared.models.disaster import DisasterEvent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Disaster Response Orchestrator")
orchestrator = DisasterResponseOrchestrator()


@app.get("/health")
async def health_check():
    is_healthy = await orchestrator.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy"}


@app.post("/orchestrate")
async def orchestrate_response(event_data: dict, background_tasks: BackgroundTasks):
    try:
        event = DisasterEvent(**event_data)
        background_tasks.add_task(run_orchestration, event)
        
        return JSONResponse({
            "message": "Orchestration started",
            "event_id": event.event_id
        })
        
    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pubsub-trigger")
async def pubsub_trigger(request: Request, background_tasks: BackgroundTasks):
    try:
        request_json = await request.json()
        
        if 'message' in request_json:
            pubsub_message = request_json['message']
            if 'data' in pubsub_message:
                import base64
                message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
                event_data = json.loads(message_data)
                event = DisasterEvent(**event_data)
                
                background_tasks.add_task(run_orchestration, event)
                
                return JSONResponse({"message": "Orchestration triggered via Pub/Sub"})
        
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")
        
    except Exception as e:
        logger.error(f"Pub/Sub trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_orchestration(event: DisasterEvent):
    try:
        logger.info(f"Starting orchestration for event: {event.event_id}")
        result = await orchestrator.process_disaster_event(event)
        logger.info(f"Orchestration completed for event: {event.event_id}")
        
    except Exception as e:
        logger.error(f"Orchestration failed for event {event.event_id}: {e}")


@app.get("/orchestrations/{orchestration_id}")
async def get_orchestration_status(orchestration_id: str):
    try:
        doc_ref = orchestrator.gcp.firestore.collection('orchestrations').document(orchestration_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Orchestration not found")
            
    except Exception as e:
        logger.error(f"Failed to get orchestration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}/tasks")
async def get_event_tasks(event_id: str):
    try:
        tasks_ref = orchestrator.gcp.firestore.collection('tasks').where('event_id', '==', event_id)
        tasks = [doc.to_dict() for doc in tasks_ref.stream()]
        
        return {"event_id": event_id, "tasks": tasks}
        
    except Exception as e:
        logger.error(f"Failed to get event tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)