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


class PRAgent(BaseAgent):
    def __init__(self):
        super().__init__("pr")
        
    async def process(self, task: AgentTask) -> AgentResult:
        try:
            await self.log_agent_action("start_pr", {"task_id": task.task_id})
            await self.update_task_status(task.task_id, TaskStatus.RUNNING)
            
            payload = task.payload
            disaster_type = payload.get("disaster_type")
            location = payload.get("location", {})
            severity = payload.get("severity", 0.0)
            output_formats = payload.get("output_formats", ["web"])
            
            analysis_data = await self._get_analysis_data(task.event_id)
            collected_info = await self._get_collected_info(task.event_id)
            
            pr_content = {}
            
            if "web" in output_formats:
                pr_content["web"] = await self._generate_web_content(
                    disaster_type, location, severity, analysis_data, collected_info
                )
            
            # Mobile and emergency channels removed as requested
            
            await self._publish_to_channels(pr_content, task.event_id)
            
            result = {
                "generated_formats": list(pr_content.keys()),
                "content_summary": self._summarize_content(pr_content),
                "published_at": datetime.utcnow().isoformat()
            }
            
            await self.log_agent_action("pr_completed", result)
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.DONE,
                result=result,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"PR generation failed: {e}")
            await self.update_task_status(task.task_id, TaskStatus.FAILED, errors=[str(e)])
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.FAILED,
                result={},
                updated_at=datetime.utcnow(),
                errors=[str(e)]
            )
    
    async def _get_analysis_data(self, event_id: str) -> List[Dict[str, Any]]:
        try:
            analysis_ref = self.gcp.firestore.collection('analysis_results').where('event_id', '==', event_id)
            analyses = [doc.to_dict() for doc in analysis_ref.stream()]
            return analyses
        except Exception as e:
            logger.error(f"Failed to get analysis data: {e}")
            return []
    
    async def _get_collected_info(self, event_id: str) -> List[Dict[str, Any]]:
        try:
            info_ref = self.gcp.firestore.collection('collected_info').where('event_id', '==', event_id)
            info_items = [doc.to_dict() for doc in info_ref.stream()]
            return info_items
        except Exception as e:
            logger.error(f"Failed to get collected info: {e}")
            return []
    
    async def _generate_web_content(self, disaster_type: str, location: Dict[str, Any], severity: float, analysis_data: List[Dict[str, Any]], collected_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"DEBUG: PR Agent starting web content generation - disaster_type={disaster_type}, location={location}, severity={severity}")
        logger.info(f"DEBUG: Analysis data count: {len(analysis_data)}, Collected info count: {len(collected_info)}")
        
        if vertex_ai_client.is_local_mode:
            logger.info("DEBUG: Using local mode for PR content generation")
            return await vertex_ai_client.llm_gemini_pro.generate_web_content(disaster_type, location, severity)
        
        analysis_summary = self._extract_analysis_summary(analysis_data)
        latest_info = self._extract_latest_info(collected_info)
        
        logger.info(f"DEBUG: Analysis summary: {analysis_summary}")
        logger.info(f"DEBUG: Latest info: {latest_info}")
        
        prompt = f"""
災害情報Webサイト用のコンテンツを生成してください。

災害情報:
- 種類: {disaster_type}
- 場所: {location.get('admin', '不明')}
- 深刻度: {severity}

分析結果:
{analysis_summary}

最新情報:
{latest_info}

以下の形式でJSONで回答:
{{
    "headline": "見出し",
    "summary": "概要（2-3文）",
    "details": {{
        "current_situation": "現在の状況",
        "affected_areas": ["影響地域"],
        "safety_instructions": ["安全指示"],
        "evacuation_info": "避難情報",
        "traffic_info": "交通情報",
        "utility_status": "ライフライン状況"
    }},
    "updates": [
        {{
            "timestamp": "時刻",
            "content": "更新内容"
        }}
    ],
    "map_data": {{
        "center": {{"lat": 緯度, "lng": 経度}},
        "markers": [
            {{
                "lat": 緯度,
                "lng": 経度,
                "type": "incident|evacuation|closure",
                "title": "マーカータイトル",
                "description": "説明"
            }}
        ]
    }},
    "last_updated": "{datetime.utcnow().isoformat()}"
}}
"""
        
        try:
            logger.info("DEBUG: Attempting to get Vertex AI client for PR generation")
            
            # Force initialization and error if not available
            llm_client = vertex_ai_client.llm_gemini_pro
            logger.info(f"DEBUG: Got LLM client: {type(llm_client)}")
            
            logger.info("DEBUG: Calling LLM ainvoke method")
            response = await llm_client.ainvoke(prompt)
            logger.info(f"DEBUG: Raw LLM response: {response}")
            
            parsed_response = vertex_ai_client._parse_json_response(response)
            logger.info(f"DEBUG: Parsed JSON response: {parsed_response}")
            
            return parsed_response
            
        except Exception as e:
            error_msg = f"PR web content generation failed: {e}"
            logger.error(f"CRITICAL ERROR: {error_msg}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Re-raise the error instead of providing fallback
            raise RuntimeError(error_msg) from e
    
    # Mobile content generation removed as requested
    
    # Emergency alert generation removed as requested
    
    def _extract_analysis_summary(self, analysis_data: List[Dict[str, Any]]) -> str:
        if not analysis_data:
            return "分析データなし"
        
        summaries = []
        for analysis in analysis_data:
            result = analysis.get("result", {})
            if "impact_assessment" in result:
                impact = result["impact_assessment"]
                summaries.append(f"影響評価: {impact}")
            elif "situation_overview" in result:
                summaries.append(f"状況: {result['situation_overview']}")
        
        return "\n".join(summaries) if summaries else "分析結果の取得に失敗"
    
    def _extract_latest_info(self, collected_info: List[Dict[str, Any]]) -> str:
        if not collected_info:
            return "収集情報なし"
        
        sorted_info = sorted(
            collected_info,
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        latest_items = []
        for item in sorted_info[:5]:
            title = item.get("title", "")
            summary = item.get("summary", item.get("content", ""))[:200]
            latest_items.append(f"- {title}: {summary}")
        
        return "\n".join(latest_items)
    
    async def _publish_to_channels(self, pr_content: Dict[str, Any], event_id: str):
        try:
            bulletin_id = str(uuid.uuid4())
            
            doc_ref = self.gcp.firestore.collection('bulletins').document(bulletin_id)
            doc_ref.set({
                "bulletin_id": bulletin_id,
                "event_id": event_id,
                "content": pr_content,
                "published_at": datetime.utcnow().isoformat(),
                "approved_by": "system",
                "status": "published"
            })
            
            incident_ref = self.gcp.firestore.collection('incidents').document(event_id)
            incident_ref.update({
                "bulletins": firestore.ArrayUnion([bulletin_id]),
                "last_bulletin_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Published bulletin {bulletin_id} for event {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish to channels: {e}")
    
    def _summarize_content(self, pr_content: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        for format_type, content in pr_content.items():
            if isinstance(content, dict):
                if "headline" in content:
                    summary[format_type] = {"headline": content["headline"]}
                # Mobile and emergency alert summary removed
                else:
                    summary[format_type] = {"status": "generated"}
        return summary


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)