import os
from typing import Dict, Any


class Config:
    
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast1")
    
    PUBSUB_TOPICS = {
        "disaster_poll": "disaster-poll",
        "disaster_detected": "disaster-detected",
        "agent_task_info_collector": "agent-task-info-collector", 
        "agent_task_analyzer": "agent-task-analyzer",
        "agent_task_pr": "agent-task-pr",
        "agent_task_support": "agent-task-support"
    }
    
    FIRESTORE_COLLECTIONS = {
        "incidents": "incidents",
        "tasks": "tasks", 
        "orchestrations": "orchestrations",
        "rag_documents": "rag_documents",
        "collected_info": "collected_info",
        "analysis_results": "analysis_results",
        "bulletins": "bulletins",
        "processed_content": "processed_content"
    }
    
    AGENT_SERVICES = {
        "detection": os.getenv("DETECTION_SERVICE_URL", "http://detection:8080"),
        "orchestrator": os.getenv("ORCHESTRATOR_SERVICE_URL", "http://orchestrator:8080"),
        "info_collector": os.getenv("INFO_COLLECTOR_SERVICE_URL", "http://info-collector:8080"),
        "analyzer": os.getenv("ANALYZER_SERVICE_URL", "http://analyzer:8080"),
        "pr": os.getenv("PR_SERVICE_URL", "http://pr:8080"),
        "support": os.getenv("SUPPORT_SERVICE_URL", "http://support:8080")
    }
    
    DETECTION_CONFIG = {
        "rss_poll_interval": int(os.getenv("RSS_POLL_INTERVAL", "300")),
        "severity_threshold": float(os.getenv("SEVERITY_THRESHOLD", "0.3")),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    }
    
    VERTEX_AI_CONFIG = {
        "project_id": GOOGLE_CLOUD_PROJECT,
        "location": GOOGLE_CLOUD_REGION,
        "models": {
            "gemini_pro": "gemini-2.5-flash",
            "gemini_flash": "gemini-2.5-flash-lite", 
            "embedding": "textembedding-gecko-multilingual@001"
        }
    }
    
    @classmethod
    def get_topic_path(cls, topic_name: str) -> str:
        return f"projects/{cls.GOOGLE_CLOUD_PROJECT}/topics/{cls.PUBSUB_TOPICS[topic_name]}"
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        issues = []
        
        if not cls.GOOGLE_CLOUD_PROJECT:
            issues.append("GOOGLE_CLOUD_PROJECT not set")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "project": cls.GOOGLE_CLOUD_PROJECT,
                "region": cls.GOOGLE_CLOUD_REGION,
                "topics": cls.PUBSUB_TOPICS,
                "collections": cls.FIRESTORE_COLLECTIONS
            }
        }