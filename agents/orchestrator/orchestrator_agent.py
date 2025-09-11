import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
import logging

from agents.common.base_agent import BaseAgent
from shared.models.disaster import DisasterEvent, AgentTask, AgentResult, TaskStatus
from shared.utils.gcp_client import gcp_client


logger = logging.getLogger(__name__)


class OrchestrationState(str, Enum):
    INITIALIZING = "initializing"
    COLLECTING_INFO = "collecting_info"
    ANALYZING = "analyzing"
    PUBLISHING = "publishing"
    SUPPORTING = "supporting"
    COMPLETED = "completed"
    FAILED = "failed"


class DisasterResponseOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__("orchestrator")
        self.agent_endpoints = {
            "info_collector": os.getenv("INFO_COLLECTOR_URL", "http://info-collector:8080"),
            "analyzer": os.getenv("ANALYZER_URL", "http://analyzer:8080"),
            "pr": os.getenv("PR_URL", "http://pr:8080"),
            "support": os.getenv("SUPPORT_URL", "http://support:8080")
        }
    
    async def process(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent=self.agent_name,
            status=TaskStatus.DONE,
            result={"message": "Orchestrator does not process individual tasks"},
            created_at=datetime.utcnow()
        )
        
    async def process_disaster_event(self, event: DisasterEvent) -> Dict[str, Any]:
        orchestration_id = str(uuid.uuid4())
        
        try:
            await self.log_agent_action("start_orchestration", {
                "orchestration_id": orchestration_id,
                "event_id": event.event_id,
                "disaster_type": event.type.value
            })
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.INITIALIZING, {
                "event": event.dict(),
                "started_at": datetime.utcnow().isoformat()
            })
            
            # Create incidents document for other agents to update
            await self._create_incident_document(event)
            
            tasks = await self._create_agent_tasks(event)
            
            results = {}
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.COLLECTING_INFO)
            results["info_collection"] = await self._execute_info_collection(tasks["info_collection"])
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.ANALYZING)
            results["analysis"] = await self._execute_analysis(tasks["analysis"])
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.PUBLISHING)
            results["pr"] = await self._execute_pr_tasks(tasks["pr"])
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.SUPPORTING)
            results["support"] = await self._execute_support_tasks(tasks["support"])
            
            await self._update_orchestration_state(orchestration_id, OrchestrationState.COMPLETED, {
                "results": results,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            await self.log_agent_action("orchestration_completed", {
                "orchestration_id": orchestration_id,
                "results_summary": self._summarize_results(results)
            })
            
            return {
                "orchestration_id": orchestration_id,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            await self._update_orchestration_state(orchestration_id, OrchestrationState.FAILED, {
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })
            raise
    
    async def _create_agent_tasks(self, event: DisasterEvent) -> Dict[str, List[AgentTask]]:
        base_task_data = {
            "event_id": event.event_id,
            "disaster_type": event.type.value,
            "location": event.location.dict(),
            "severity": event.severity,
            "summary": event.summary
        }
        
        return {
            "info_collection": [
                AgentTask(
                    task_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    agent="info_collector",
                    status=TaskStatus.PENDING,
                    payload={
                        **base_task_data,
                        "collect_sources": ["news", "official", "social"],
                        "time_window_hours": 2
                    },
                    created_at=datetime.utcnow()
                )
            ],
            "analysis": [
                AgentTask(
                    task_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    agent="analyzer",
                    status=TaskStatus.PENDING,
                    payload={
                        **base_task_data,
                        "analysis_type": "impact_assessment"
                    },
                    created_at=datetime.utcnow()
                )
            ],
            "pr": [
                AgentTask(
                    task_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    agent="pr",
                    status=TaskStatus.PENDING,
                    payload={
                        **base_task_data,
                        "output_formats": ["web", "mobile", "emergency"]
                    },
                    created_at=datetime.utcnow()
                )
            ],
            "support": [
                AgentTask(
                    task_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    agent="support",
                    status=TaskStatus.PENDING,
                    payload={
                        **base_task_data,
                        "report_types": ["psychological", "economic"]
                    },
                    created_at=datetime.utcnow()
                )
            ]
        }
    
    async def _execute_info_collection(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        results = []
        for task in tasks:
            try:
                await self._publish_task_to_agent(task, "info-collector")
                result = await self._wait_for_task_completion(task.task_id, timeout=300)
                results.append(result)
            except Exception as e:
                logger.error(f"Info collection task {task.task_id} failed: {e}")
                results.append({"error": str(e), "task_id": task.task_id})
        return {"tasks": results}
    
    async def _execute_analysis(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        results = []
        for task in tasks:
            try:
                await self._publish_task_to_agent(task, "analyzer")
                result = await self._wait_for_task_completion(task.task_id, timeout=180)
                results.append(result)
            except Exception as e:
                logger.error(f"Analysis task {task.task_id} failed: {e}")
                results.append({"error": str(e), "task_id": task.task_id})
        return {"tasks": results}
    
    async def _execute_pr_tasks(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        results = []
        for task in tasks:
            try:
                await self._publish_task_to_agent(task, "pr")
                result = await self._wait_for_task_completion(task.task_id, timeout=120)
                results.append(result)
            except Exception as e:
                logger.error(f"PR task {task.task_id} failed: {e}")
                results.append({"error": str(e), "task_id": task.task_id})
        return {"tasks": results}
    
    async def _execute_support_tasks(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        results = []
        for task in tasks:
            try:
                await self._publish_task_to_agent(task, "support")
                result = await self._wait_for_task_completion(task.task_id, timeout=240)
                results.append(result)
            except Exception as e:
                logger.error(f"Support task {task.task_id} failed: {e}")
                results.append({"error": str(e), "task_id": task.task_id})
        return {"tasks": results}
    
    async def _publish_task_to_agent(self, task: AgentTask, topic_suffix: str):
        topic_name = f"agent-task-{topic_suffix}"
        message_data = task.json().encode('utf-8')
        
        doc_ref = self.gcp.firestore.collection('tasks').document(task.task_id)
        doc_ref.set(task.dict())
        
        message_id = self.gcp.publish_message(
            topic_name=topic_name,
            message=message_data,
            task_id=task.task_id,
            agent=task.agent
        )
        
        logger.info(f"Published task {task.task_id} to {topic_name}")
    
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                doc_ref = self.gcp.firestore.collection('tasks').document(task_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    task_data = doc.to_dict()
                    if task_data.get('status') == TaskStatus.DONE.value:
                        return task_data.get('result', {})
                    elif task_data.get('status') == TaskStatus.FAILED.value:
                        return {"error": "Task failed", "details": task_data.get('errors', [])}
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error waiting for task {task_id}: {e}")
                await asyncio.sleep(5)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    async def _create_incident_document(self, event: DisasterEvent):
        """Create initial incident document for other agents to update"""
        try:
            incident_ref = self.gcp.firestore.collection('incidents').document(event.event_id)
            incident_data = event.dict()
            incident_data.update({
                "orchestration_started_at": datetime.utcnow().isoformat(),
                "collected_info": [],
                "analysis_results": [],
                "bulletins": []
            })
            incident_ref.set(incident_data)
            logger.info(f"Created incident document for event {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to create incident document: {e}")

    async def _update_orchestration_state(self, orchestration_id: str, state: OrchestrationState, data: Dict[str, Any] = None):
        doc_ref = self.gcp.firestore.collection('orchestrations').document(orchestration_id)
        update_data = {
            "state": state.value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if data:
            update_data.update(data)
        
        doc_ref.set(update_data, merge=True)
    
    def _summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        for agent, result in results.items():
            if "tasks" in result:
                successful_tasks = sum(1 for task in result["tasks"] if "error" not in task)
                total_tasks = len(result["tasks"])
                summary[agent] = {
                    "success_rate": f"{successful_tasks}/{total_tasks}",
                    "completed": successful_tasks == total_tasks
                }
        return summary