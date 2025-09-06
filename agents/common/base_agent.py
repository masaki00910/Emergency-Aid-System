from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
import json
from datetime import datetime

from shared.models.disaster import AgentTask, AgentResult, TaskStatus
from shared.utils.gcp_client import gcp_client


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.gcp = gcp_client
        
    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResult:
        pass
    
    async def health_check(self) -> bool:
        return True
    
    async def update_task_status(self, task_id: str, status: TaskStatus, result: Dict[Any, Any] = None, errors: List[str] = None):
        doc_ref = self.gcp.firestore.collection('tasks').document(task_id)
        update_data = {
            'status': status.value,
            'updated_at': datetime.utcnow()
        }
        
        if result:
            update_data['result'] = result
        if errors:
            update_data['errors'] = errors
            
        doc_ref.update(update_data)
        logger.info(f"Task {task_id} status updated to {status.value}")
    
    async def log_agent_action(self, action: str, details: Dict[Any, Any] = None):
        log_data = {
            'agent': self.agent_name,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        logger.info(json.dumps(log_data, ensure_ascii=False))