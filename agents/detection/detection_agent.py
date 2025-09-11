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
                "url": "https://www3.nhk.or.jp/rss/news/cat0.xml",
                "source": "nhk",
                "name": "NHKニュース"
            },
            {
                "url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
                "source": "yahoo",
                "name": "Yahoo!ニュース"
            }
        ]
        self.severity_threshold = 0.2  # より低いしきい値で災害を検知
        self.confidence_threshold = 0.4  # 信頼度も少し低く設定
    
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
        logger.info(f"Processing RSS source: {source['name']} ({source['url']})")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(source["url"], timeout=30.0)
            response.raise_for_status()
            
        feed = feedparser.parse(response.content)
        events = []
        total_entries = len(feed.entries)
        processed_entries = 0
        skipped_duplicates = 0
        vertex_ai_calls = 0
        
        logger.info(f"Found {total_entries} entries in {source['name']} feed")
        
        for entry in feed.entries[:10]:
            try:
                content = self._extract_content(entry)
                content_hash = hashlib.md5(content.encode()).hexdigest()
                title = entry.get("title", "No title")[:50]
                
                logger.info(f"Processing entry: {title}...")
                
                if await self._is_duplicate(content_hash, content):
                    logger.info(f"Skipping duplicate: {title}")
                    skipped_duplicates += 1
                    continue
                
                processed_entries += 1
                logger.info(f"Calling Vertex AI for analysis: {title}")
                
                analysis = await vertex_ai_client.generate_disaster_analysis(
                    content=content,
                    source_info={
                        "source": source["source"],
                        "url": entry.get("link", source["url"]),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                vertex_ai_calls += 1
                logger.info(f"Vertex AI analysis result for '{title}': is_disaster={analysis.get('is_disaster', False)}, confidence={analysis.get('confidence', 0.0)}")
                
                if analysis.get("is_disaster", False):
                    event = self._create_disaster_event(entry, source, analysis, content_hash)
                    events.append(event)
                    logger.info(f"Disaster event created: {event.event_id} - {analysis.get('disaster_type', 'unknown')}")
                    
            except Exception as e:
                logger.error(f"Failed to process entry {entry.get('title', 'Unknown')}: {e}")
                import traceback
                logger.error(f"Full error traceback: {traceback.format_exc()}")
        
        logger.info(f"RSS processing complete for {source['name']}: {total_entries} total, {processed_entries} analyzed, {skipped_duplicates} duplicates, {vertex_ai_calls} AI calls, {len(events)} disasters detected")
        return events
    
    def _extract_content(self, entry) -> str:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        
        if "content" in entry:
            content = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
        else:
            content = BeautifulSoup(summary, 'html.parser').get_text()
        
        return f"{title}\n{content}".strip()
    
    async def _is_duplicate(self, content_hash: str, content_text: str = "") -> bool:
        try:
            # 診断のため一時的に重複チェックを無効化
            logger.info(f"DEBUG: Checking duplicate for content: {content_text[:100]}...")
            
            doc_ref = self.gcp.firestore.collection('processed_content').document(content_hash)
            doc = doc_ref.get()
            
            if doc.exists:
                # 災害関連キーワードを含む記事は24時間後に再分析を許可
                disaster_keywords = ['災害', '地震', '津波', '台風', '洪水', '土砂', '避難', '警報', '注意報', 
                                   '大雨', '暴雨', '線状降水帯', '氾濫', '浸水', '落雷', '雷', '雨', '風', 
                                   '被害', '倒壊', '停電', '断水', '緊急', '危険', '警戒']
                
                has_disaster_keyword = any(keyword in content_text for keyword in disaster_keywords)
                logger.info(f"DEBUG: Has disaster keyword: {has_disaster_keyword}, Keywords found: {[kw for kw in disaster_keywords if kw in content_text]}")
                
                if has_disaster_keyword:
                    # 災害キーワード含有記事は時間に関係なく強制再分析
                    logger.info(f"DISASTER KEYWORD FOUND - Forcing re-analysis: {[kw for kw in disaster_keywords if kw in content_text]}")
                    doc_ref.set({'processed_at': datetime.utcnow(), 'disaster_related': True})
                    return False
                
                logger.info("DEBUG: Marking as duplicate (no disaster keywords or within 24h)")
                return True
            
            logger.info("DEBUG: New content, not a duplicate")
            doc_ref.set({'processed_at': datetime.utcnow()})
            return False
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            import traceback
            logger.error(f"Duplicate check traceback: {traceback.format_exc()}")
            return False
    
    def _create_disaster_event(self, entry, source: Dict[str, str], analysis: Dict[str, Any], content_hash: str) -> DisasterEvent:
        location_data = analysis.get("location", {})
        
        # Validate and sanitize location data
        try:
            lat = float(location_data.get("lat", 35.6762))
            if not (-90 <= lat <= 90):
                lat = 35.6762  # Default to Tokyo
        except (TypeError, ValueError):
            lat = 35.6762
            
        try:
            lng = float(location_data.get("lng", 139.6503))
            if not (-180 <= lng <= 180):
                lng = 139.6503  # Default to Tokyo
        except (TypeError, ValueError):
            lng = 139.6503
            
        admin = location_data.get("admin", "不明")
        if not admin or not isinstance(admin, str):
            admin = "不明"
        
        return DisasterEvent(
            event_id=str(uuid.uuid4()),
            detected_at=datetime.utcnow(),
            source=[source["source"]],
            type=DisasterType(analysis.get("disaster_type", "other")),
            location=Location(
                lat=lat,
                lng=lng,
                admin=admin
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