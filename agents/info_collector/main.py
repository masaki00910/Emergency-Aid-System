import asyncio
import os
import sys
import json
import base64
import logging
import traceback
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("Info Collector Agent starting with enhanced logging")

app = FastAPI(title="Info Collector Agent")

# Initialize with error handling
info_collector = None
startup_error = None

try:
    logger.info("Starting Info Collector Agent initialization...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Test imports separately for better error diagnosis
    logger.info("Importing AgentTask...")
    from shared.models.disaster import AgentTask
    logger.info("AgentTask imported successfully")
    
    logger.info("Importing InfoCollectorAgent...")
    from info_collector_agent import InfoCollectorAgent
    logger.info("InfoCollectorAgent imported successfully")
    
    logger.info("Creating InfoCollectorAgent instance...")
    # Lazy initialization - only create when needed to speed up startup
    info_collector = None
    logger.info("Info Collector Agent setup completed (lazy initialization)")
    
except ImportError as e:
    startup_error = str(e)
    error_traceback = traceback.format_exc()
    logger.error(f"Import error during initialization: {e}")
    logger.error(f"Traceback: {error_traceback}")
    
    # Check specific paths
    logger.error(f"Contents of current directory: {os.listdir('.')}")
    if os.path.exists('../../shared'):
        logger.error(f"Contents of ../../shared: {os.listdir('../../shared')}")
    if os.path.exists('/app/shared'):
        logger.error(f"Contents of /app/shared: {os.listdir('/app/shared')}")
    
except Exception as e:
    startup_error = str(e)
    error_traceback = traceback.format_exc()
    logger.error(f"General error during initialization: {e}")
    logger.error(f"Traceback: {error_traceback}")
    
    # Skip normal endpoint definition if startup failed
    pass

def get_info_collector():
    """Lazy initialization of InfoCollectorAgent"""
    global info_collector
    if info_collector is None and startup_error is None:
        try:
            logger.info("Lazy initializing InfoCollectorAgent...")
            info_collector = InfoCollectorAgent()
            logger.info("InfoCollectorAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InfoCollectorAgent: {e}")
            raise e
    return info_collector

@app.get("/health")
async def health_check():
    if startup_error:
        return {"status": "unhealthy", "error": startup_error}
    
    # For health check, just return healthy if no startup error
    # This allows the container to start faster
    return {"status": "healthy", "message": "Service is ready"}


@app.post("/collect")
async def collect_info(task_data: dict, background_tasks: BackgroundTasks):
    if startup_error:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {startup_error}")
    
    try:
        # Initialize on first use
        collector = get_info_collector()
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
    if startup_error:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {startup_error}")
        
    try:
        # Initialize on first use
        collector = get_info_collector()
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
        # Get or initialize collector
        collector = get_info_collector()
        result = await collector.process(task)
        
        await collector.update_task_status(
            task.task_id,
            result.status,
            result.result,
            result.errors
        )
        
        logger.info(f"Collection task completed: {task.task_id}")
        
    except Exception as e:
        logger.error(f"Collection task failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    import uvicorn
    import sys
    
    logger.info("=== DETAILED STARTUP DIAGNOSTICS ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Environment PORT: {os.getenv('PORT', 'NOT_SET')}")
    logger.info(f"Files in current dir: {os.listdir('.')}")
    logger.info(f"Files in /app: {os.listdir('/app') if os.path.exists('/app') else 'NOT_EXISTS'}")
    logger.info(f"Startup error status: {startup_error}")
    logger.info("=== END DIAGNOSTICS ===")
    
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start uvicorn: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)