import asyncio
import os
import json
import base64
import logging
from datetime import datetime
from google.cloud import firestore

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse

from pr_agent import PRAgent
from shared.models.disaster import AgentTask
from faq_generator import FAQGeneratorAgent
from google.cloud import firestore

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("PR Agent starting with enhanced logging")

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
        bulletins_ref = (pr_agent.gcp.firestore.collection('bulletins')
                        .order_by('published_at', direction=firestore.Query.DESCENDING)
                        .limit(limit))
        bulletins = [doc.to_dict() for doc in bulletins_ref.stream()]
        
        return {"bulletins": bulletins}
        
    except Exception as e:
        logger.error(f"Failed to get latest bulletins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

faq_db = firestore.Client()  # Firestore クライアント
faq_agent = FAQGeneratorAgent()

def save_faq_and_chats(event_id: str, faqs: list, user_interactions: list | None = None):
    """FAQ と初期のユーザ対話（通常は空）を 1 ドキュメントにまとめて保存"""
    doc_ref = faq_db.collection("faq_chat_logs").document(event_id)
    data = {
        "faqs": faqs,
        "user_interactions": user_interactions or [],
        "created_at": datetime.utcnow().isoformat()
    }
    doc_ref.set(data)
    logger.info(f"FAQとチャット（初期）を保存しました: {doc_ref.id}")

def add_user_interaction(event_id: str, user_input: str, answer: str):
    """既存ドキュメントにユーザの質問＆回答を追加"""
    doc_ref = faq_db.collection("faq_chat_logs").document(event_id)
    new_entry = {
        "user_input": user_input,
        "answer": answer,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        doc_ref.update({"user_interactions": firestore.ArrayUnion([new_entry])})
        logger.info(f"ユーザ質問を追加しました: {doc_ref.id}")
    except Exception as e:
        # ドキュメントが無い場合は新規作成
        doc_ref.set({
            "faqs": [],
            "user_interactions": [new_entry],
            "created_at": datetime.utcnow().isoformat()
        })
        logger.info(f"ドキュメントが無かったため新規作成して追加しました: {doc_ref.id}")

@app.post("/faq-generate")
async def generate_faq(request: Request):
    """
    FAQGeneratorAgent を呼び出してユーザ対話＋Firestore保存を行う
    """
    try:
        data = await request.json()
        event_id = data.get("event_id", "test-event")
        user_question = data.get("question", "")

        if not user_question:
            raise HTTPException(status_code=400, detail="Missing 'question' field")

        # =========================
        # FAQ生成
        faqs_result = await faq_agent.process(AgentTask(
            task_id=f"faq-{datetime.utcnow().timestamp()}",
            event_id=event_id,
            agent="faq_generator",
            payload={"content": user_question},
            created_at=datetime.utcnow()
        ))
        faqs = faqs_result.result.get("faqs", [])

        # Firestoreに初期保存（user_interactions は空）
        save_faq_and_chats(event_id, faqs)

        # Vertex AI を使ってユーザ質問に回答
        answer = await faq_agent.vertex_ai_client.answer_with_faq(faqs, user_question)

        # Firestore にユーザ質問と回答を追加
        add_user_interaction(event_id, user_question, answer)
        # =========================

        return {"question": user_question, "answer": answer, "faqs": faqs}

    except Exception as e:
        logger.error(f"FAQ generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)