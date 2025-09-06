import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any
import feedparser
import httpx
from bs4 import BeautifulSoup
import logging

from agents.common.base_agent import BaseAgent
from shared.models.disaster import DisasterEvent, DisasterType, Location, Evidence, AgentTask, AgentResult, TaskStatus
from shared.utils.vertex_ai_client import vertex_ai_client


logger = logging.getLogger(__name__)


class DisasterDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("disaster_detection")
        self.rss_sources = [
            {
                "url": "https://www.jma.go.jp/bosai/forecast/data/forecast/rss/region.xml",
                "source": "jma",
                "name": "気象庁防災情報"
            },
            {
                "url": "https://www3.nhk.or.jp/rss/news/cat0.xml",
                "source": "nhk",
                "name": "NHKニュース"
            }
        ]
        self.severity_threshold = 0.3
        self.confidence_threshold = 0.5
    
    async def process(self, task: AgentTask) -> AgentResult:
        try:
            await self.log_agent_action("start_detection", {"task_id": task.task_id})
            
            detected_events = []
            
            for source in self.rss_sources:
                try:
                    events = await self._process_rss_source(source)
                    detected_events.extend(events)
                except Exception as e:
                    logger.error(f"Failed to process source {source['name']}: {e}")
            
            significant_events = [
                event for event in detected_events 
                if event.severity >= self.severity_threshold and event.confidence >= self.confidence_threshold
            ]
            
            for event in significant_events:
                await self._publish_disaster_event(event)
            
            result = {
                "processed_sources": len(self.rss_sources),
                "detected_events": len(detected_events),
                "significant_events": len(significant_events),
                "events": [event.dict() for event in significant_events]
            }
            
            await self.log_agent_action("detection_completed", result)
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.DONE,
                result=result,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Detection agent failed: {e}")
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.FAILED,
                result={},
                updated_at=datetime.utcnow(),
                errors=[str(e)]
            )
    
    async def _process_rss_source(self, source: Dict[str, str]) -> List[DisasterEvent]:
        async with httpx.AsyncClient() as client:
            response = await client.get(source["url"], timeout=30.0)
            response.raise_for_status()
            
        feed = feedparser.parse(response.content)
        events = []
        
        for entry in feed.entries[:10]:
            try:
                content = self._extract_content(entry)
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if await self._is_duplicate(content_hash):
                    continue
                
                analysis = await vertex_ai_client.generate_disaster_analysis(
                    content=content,
                    source_info={
                        "source": source["source"],
                        "url": entry.get("link", source["url"]),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                if analysis.get("is_disaster", False):
                    event = self._create_disaster_event(entry, source, analysis, content_hash)
                    events.append(event)
                    
            except Exception as e:
                logger.error(f"Failed to process entry {entry.get('title', 'Unknown')}: {e}")
        
        return events
    
    def _extract_content(self, entry) -> str:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        
        if "content" in entry:
            content = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
        else:
            content = BeautifulSoup(summary, 'html.parser').get_text()
        
        return f"{title}\n{content}".strip()
    
    async def _is_duplicate(self, content_hash: str) -> bool:
        try:
            doc_ref = self.gcp.firestore.collection('processed_content').document(content_hash)
            doc = doc_ref.get()
            
            if doc.exists:
                return True
            
            doc_ref.set({'processed_at': datetime.utcnow()})
            return False
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False
    
    def _create_disaster_event(self, entry, source: Dict[str, str], analysis: Dict[str, Any], content_hash: str) -> DisasterEvent:
        location_data = analysis.get("location", {})
        
        return DisasterEvent(
            event_id=str(uuid.uuid4()),
            detected_at=datetime.utcnow(),
            source=[source["source"]],
            type=DisasterType(analysis.get("disaster_type", "other")),
            location=Location(
                lat=location_data.get("lat", 35.6762),
                lng=location_data.get("lng", 139.6503),
                admin=location_data.get("admin", "不明")
            ),
            severity=analysis.get("severity", 0.0),
            confidence=analysis.get("confidence", 0.0),
            summary=analysis.get("summary", ""),
            evidence=[Evidence(
                url=entry.get("link", source["url"]),
                title=entry.get("title", ""),
                source=source["source"],
                timestamp=datetime.utcnow(),
                hash=content_hash
            )]
        )
    
    async def _publish_disaster_event(self, event: DisasterEvent):
        try:
            message_data = event.json().encode('utf-8')
            message_id = self.gcp.publish_message(
                topic_name="disaster-detected",
                message=message_data,
                event_id=event.event_id,
                severity=str(event.severity)
            )
            
            doc_ref = self.gcp.firestore.collection('incidents').document(event.event_id)
            doc_ref.set(event.dict())
            
            logger.info(f"Published disaster event {event.event_id} with message_id {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish disaster event: {e}")
            raise