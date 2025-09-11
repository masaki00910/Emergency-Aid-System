import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from google.cloud import firestore

from agents.common.base_agent import BaseAgent
from shared.models.disaster import AgentTask, AgentResult, TaskStatus, DisasterType
from shared.utils.vertex_ai_client import vertex_ai_client


logger = logging.getLogger(__name__)


class DisasterAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__("analyzer")
        
    async def process(self, task: AgentTask) -> AgentResult:
        try:
            await self.log_agent_action("start_analysis", {"task_id": task.task_id})
            await self.update_task_status(task.task_id, TaskStatus.RUNNING)
            
            payload = task.payload
            disaster_type = payload.get("disaster_type")
            location = payload.get("location", {})
            severity = payload.get("severity", 0.0)
            analysis_type = payload.get("analysis_type", "impact_assessment")
            
            rag_context = await self._get_rag_context(task.event_id)
            
            if analysis_type == "impact_assessment":
                analysis_result = await self._perform_impact_assessment(
                    disaster_type, location, severity, rag_context
                )
            else:
                analysis_result = await self._perform_general_analysis(
                    disaster_type, location, severity, rag_context
                )
            
            await self._store_analysis_result(task.event_id, analysis_result)
            
            result = {
                "analysis_type": analysis_type,
                "disaster_type": disaster_type,
                "location": location,
                "analysis_result": analysis_result,
                "rag_documents_used": len(rag_context)
            }
            
            await self.log_agent_action("analysis_completed", {
                "task_id": task.task_id,
                "analysis_type": analysis_type
            })
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.DONE,
                result=result,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            await self.update_task_status(task.task_id, TaskStatus.FAILED, errors=[str(e)])
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.FAILED,
                result={},
                updated_at=datetime.utcnow(),
                errors=[str(e)]
            )
    
    async def _get_rag_context(self, event_id: str) -> List[Dict[str, Any]]:
        try:
            docs_ref = self.gcp.firestore.collection('rag_documents').where('metadata.event_id', '==', event_id)
            docs = [doc.to_dict() for doc in docs_ref.stream()]
            
            return docs[:10]
            
        except Exception as e:
            logger.error(f"Failed to get RAG context: {e}")
            return []
    
    async def _perform_impact_assessment(self, disaster_type: str, location: Dict[str, Any], severity: float, rag_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        if vertex_ai_client.is_local_mode:
            return await vertex_ai_client.llm_gemini_pro.generate_impact_assessment(disaster_type, location, "")
        
        context_text = "\n".join([doc.get("content", "") for doc in rag_context])
        
        prompt = f"""
災害影響評価を実施してください。

災害情報:
- 種類: {disaster_type}
- 場所: {location.get('admin', '不明')} (緯度: {location.get('lat')}, 経度: {location.get('lng')})
- 深刻度: {severity}

収集済み情報:
{context_text[:3000]}

以下の形式でJSONで回答:
{{
    "impact_assessment": {{
        "human_impact": {{
            "estimated_affected_population": 推定影響人口,
            "vulnerability_areas": ["脆弱性のある地域"],
            "evacuation_recommendations": ["避難推奨事項"]
        }},
        "infrastructure_impact": {{
            "transportation": "交通への影響評価",
            "utilities": "ライフラインへの影響",
            "facilities": "重要施設への影響"
        }},
        "economic_impact": {{
            "estimated_damage": "推定被害額",
            "affected_industries": ["影響を受ける産業"],
            "recovery_timeline": "復旧見込み"
        }}
    }},
    "response_recommendations": {{
        "immediate_actions": ["即座に必要な対応"],
        "resource_allocation": ["必要リソース"],
        "coordination_points": ["調整が必要な組織"]
    }},
    "information_gaps": ["不足している情報"],
    "confidence_level": 0.0-1.0,
    "sources_used": ["使用した情報源"]
}}
"""
        
        try:
            # Use the global client to ensure proper Vertex AI usage
            if hasattr(vertex_ai_client, 'llm_gemini_pro') and vertex_ai_client.llm_gemini_pro:
                response = await vertex_ai_client.llm_gemini_pro.ainvoke(prompt)
                return vertex_ai_client._parse_json_response(response)
            else:
                # Fallback if client not properly initialized
                logger.warning("Vertex AI client not properly initialized, using fallback impact assessment")
                return {
                    "impact_assessment": {
                        "human_impact": {
                            "estimated_affected_population": 1000,
                            "vulnerability_areas": ["Unknown areas"],
                            "evacuation_recommendations": ["Follow local authorities guidance"]
                        },
                        "infrastructure_impact": {
                            "transportation": "Impact unknown",
                            "utilities": "Impact unknown",
                            "facilities": "Impact unknown"
                        },
                        "economic_impact": {
                            "estimated_damage": "Unknown",
                            "affected_industries": ["Unknown"],
                            "recovery_timeline": "Unknown"
                        }
                    },
                    "response_recommendations": {
                        "immediate_actions": ["Monitor situation"],
                        "resource_allocation": ["Standard emergency resources"],
                        "coordination_points": ["Local emergency services"]
                    },
                    "information_gaps": ["Detailed impact assessment needed"],
                    "confidence_level": 0.3,
                    "sources_used": ["Fallback analysis"]
                }
        except Exception as e:
            logger.error(f"Impact assessment failed: {e}")
            return {"error": str(e)}
    
    async def _perform_general_analysis(self, disaster_type: str, location: Dict[str, Any], severity: float, rag_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        context_text = "\n".join([doc.get("content", "") for doc in rag_context])
        
        prompt = f"""
災害状況の一般分析を実施してください。

災害情報:
- 種類: {disaster_type}
- 場所: {location.get('admin', '不明')}
- 深刻度: {severity}

収集済み情報:
{context_text[:3000]}

以下の形式でJSONで回答:
{{
    "situation_overview": "現状概要",
    "key_developments": ["主要な展開"],
    "affected_areas": ["影響地域"],
    "current_response": ["現在の対応状況"],
    "recommendations": ["推奨事項"],
    "next_steps": ["次のステップ"]
}}
"""
        
        try:
            # Use the global client to ensure proper Vertex AI usage
            if hasattr(vertex_ai_client, 'llm_gemini_flash') and vertex_ai_client.llm_gemini_flash:
                response = await vertex_ai_client.llm_gemini_flash.ainvoke(prompt)
                return vertex_ai_client._parse_json_response(response)
            else:
                # Fallback if client not properly initialized
                logger.warning("Vertex AI client not properly initialized, using fallback analysis")
                return {
                    "situation_overview": f"{disaster_type} disaster in {location.get('admin', 'Unknown location')}",
                    "key_developments": ["Situation being monitored"],
                    "affected_areas": [location.get('admin', 'Unknown location')],
                    "current_response": ["Emergency services responding"],
                    "recommendations": ["Follow official guidance"],
                    "next_steps": ["Continue monitoring"]
                }
        except Exception as e:
            logger.error(f"General analysis failed: {e}")
            return {"error": str(e)}
    
    async def _store_analysis_result(self, event_id: str, analysis_result: Dict[str, Any]):
        try:
            analysis_id = str(uuid.uuid4())
            
            doc_ref = self.gcp.firestore.collection('analysis_results').document(analysis_id)
            doc_ref.set({
                "analysis_id": analysis_id,
                "event_id": event_id,
                "result": analysis_result,
                "created_at": datetime.utcnow().isoformat()
            })
            
            incident_ref = self.gcp.firestore.collection('incidents').document(event_id)
            incident_ref.update({
                "analysis_results": firestore.ArrayUnion([analysis_id])
            })
            
            logger.info(f"Stored analysis result {analysis_id} for event {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to store analysis result: {e}")