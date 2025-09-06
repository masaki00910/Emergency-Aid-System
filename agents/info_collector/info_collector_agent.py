import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from bs4 import BeautifulSoup
import logging

from agents.common.base_agent import BaseAgent
from shared.models.disaster import AgentTask, AgentResult, TaskStatus, Evidence
from shared.utils.vertex_ai_client import vertex_ai_client


logger = logging.getLogger(__name__)


class InfoCollectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("info_collector")
        self.news_sources = [
            {"url": "https://www3.nhk.or.jp/rss/news/cat0.xml", "source": "nhk", "type": "news"},
            {"url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml", "source": "yahoo", "type": "news"},
            {"url": "https://www.jma.go.jp/bosai/forecast/data/forecast/rss/region.xml", "source": "jma", "type": "official"}
        ]
        
    async def process(self, task: AgentTask) -> AgentResult:
        try:
            await self.log_agent_action("start_info_collection", {"task_id": task.task_id})
            await self.update_task_status(task.task_id, TaskStatus.RUNNING)
            
            payload = task.payload
            disaster_type = payload.get("disaster_type")
            location = payload.get("location", {})
            time_window_hours = payload.get("time_window_hours", 2)
            collect_sources = payload.get("collect_sources", ["news", "official"])
            
            collected_info = []
            
            if "news" in collect_sources:
                news_info = await self._collect_news_info(disaster_type, location, time_window_hours)
                collected_info.extend(news_info)
            
            if "official" in collect_sources:
                official_info = await self._collect_official_info(disaster_type, location, time_window_hours)
                collected_info.extend(official_info)
            
            if "social" in collect_sources:
                social_info = await self._collect_social_info(disaster_type, location, time_window_hours)
                collected_info.extend(social_info)
            
            processed_info = await self._process_and_store_info(collected_info, task.event_id)
            
            result = {
                "collected_items": len(collected_info),
                "processed_items": len(processed_info),
                "sources_used": collect_sources,
                "time_window_hours": time_window_hours,
                "summary": await self._generate_collection_summary(processed_info)
            }
            
            await self.log_agent_action("info_collection_completed", result)
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.DONE,
                result=result,
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Info collection failed: {e}")
            await self.update_task_status(task.task_id, TaskStatus.FAILED, errors=[str(e)])
            
            return AgentResult(
                task_id=task.task_id,
                agent=self.agent_name,
                status=TaskStatus.FAILED,
                result={},
                updated_at=datetime.utcnow(),
                errors=[str(e)]
            )
    
    async def _collect_news_info(self, disaster_type: str, location: Dict[str, Any], time_window_hours: int) -> List[Dict[str, Any]]:
        news_items = []
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        for source in self.news_sources:
            if source["type"] != "news":
                continue
                
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(source["url"], timeout=30.0)
                    response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:20]:
                    try:
                        entry_time = self._parse_entry_time(entry)
                        if entry_time and entry_time < cutoff_time:
                            continue
                        
                        content = self._extract_content(entry)
                        
                        if await self._is_relevant_to_disaster(content, disaster_type, location):
                            news_items.append({
                                "source": source["source"],
                                "type": "news",
                                "title": entry.get("title", ""),
                                "content": content,
                                "url": entry.get("link", ""),
                                "timestamp": entry_time or datetime.utcnow(),
                                "raw_entry": entry
                            })
                    except Exception as e:
                        logger.error(f"Failed to process news entry: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to fetch news from {source['url']}: {e}")
        
        return news_items
    
    async def _collect_official_info(self, disaster_type: str, location: Dict[str, Any], time_window_hours: int) -> List[Dict[str, Any]]:
        official_items = []
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        for source in self.news_sources:
            if source["type"] != "official":
                continue
                
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(source["url"], timeout=30.0)
                    response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:20]:
                    try:
                        entry_time = self._parse_entry_time(entry)
                        if entry_time and entry_time < cutoff_time:
                            continue
                        
                        content = self._extract_content(entry)
                        
                        official_items.append({
                            "source": source["source"],
                            "type": "official",
                            "title": entry.get("title", ""),
                            "content": content,
                            "url": entry.get("link", ""),
                            "timestamp": entry_time or datetime.utcnow(),
                            "priority": "high",
                            "raw_entry": entry
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to process official entry: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to fetch official info from {source['url']}: {e}")
        
        return official_items
    
    async def _collect_social_info(self, disaster_type: str, location: Dict[str, Any], time_window_hours: int) -> List[Dict[str, Any]]:
        logger.info("Social media collection not implemented yet - returning empty list")
        return []
    
    def _parse_entry_time(self, entry) -> Optional[datetime]:
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                import time
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                import time
                return datetime.fromtimestamp(time.mktime(entry.updated_parsed))
        except Exception as e:
            logger.error(f"Failed to parse entry time: {e}")
        return None
    
    def _extract_content(self, entry) -> str:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        
        if hasattr(entry, 'content') and entry.content:
            content = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
        else:
            content = BeautifulSoup(summary, 'html.parser').get_text()
        
        return f"{title}\n{content}".strip()
    
    async def _is_relevant_to_disaster(self, content: str, disaster_type: str, location: Dict[str, Any]) -> bool:
        try:
            prompt = f"""
以下のニュース内容が災害「{disaster_type}」および地域「{location.get('admin', '')}」に関連するかを判定してください。

内容:
{content[:1000]}

true/falseで回答してください。
"""
            response = await vertex_ai_client.llm_gemini_flash.ainvoke(prompt)
            return "true" in response.lower()
            
        except Exception as e:
            logger.error(f"Relevance check failed: {e}")
            return True
    
    async def _process_and_store_info(self, collected_info: List[Dict[str, Any]], event_id: str) -> List[Dict[str, Any]]:
        processed_items = []
        
        for item in collected_info:
            try:
                content_hash = hashlib.md5(item["content"].encode()).hexdigest()
                
                if await self._is_duplicate_content(content_hash):
                    continue
                
                enhanced_info = await self._enhance_with_ai(item)
                enhanced_info["content_hash"] = content_hash
                enhanced_info["event_id"] = event_id
                
                await self._store_to_rag_system(enhanced_info)
                await self._store_to_firestore(enhanced_info, event_id)
                
                processed_items.append(enhanced_info)
                
            except Exception as e:
                logger.error(f"Failed to process info item: {e}")
        
        return processed_items
    
    async def _is_duplicate_content(self, content_hash: str) -> bool:
        try:
            doc_ref = self.gcp.firestore.collection('processed_content').document(content_hash)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False
    
    async def _enhance_with_ai(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = f"""
以下の情報を分析し、構造化してください:

タイトル: {item.get('title', '')}
内容: {item['content']}
情報源: {item['source']}

以下の形式でJSONで回答:
{{
    "key_facts": ["重要な事実1", "重要な事実2"],
    "entities": ["場所", "人物", "組織"],
    "timestamp_mentioned": "記事中の時刻情報",
    "urgency_level": "low|medium|high",
    "reliability_score": 0.0-1.0,
    "summary": "要約"
}}
"""
            
            response = await vertex_ai_client.llm_gemini_flash.ainvoke(prompt)
            enhanced_data = vertex_ai_client._parse_json_response(response)
            
            enhanced_item = item.copy()
            enhanced_item.update(enhanced_data)
            enhanced_item["ai_processed_at"] = datetime.utcnow().isoformat()
            
            return enhanced_item
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return item
    
    async def _store_to_rag_system(self, info: Dict[str, Any]):
        try:
            doc_id = info.get("content_hash", str(uuid.uuid4()))
            content_for_embedding = f"{info.get('title', '')}\n{info.get('content', '')}\n{info.get('summary', '')}"
            
            embedding = await vertex_ai_client.embeddings.aembed_query(content_for_embedding)
            
            rag_document = {
                "id": doc_id,
                "content": content_for_embedding,
                "embedding": embedding,
                "metadata": {
                    "source": info.get("source"),
                    "type": info.get("type"),
                    "timestamp": info.get("timestamp", datetime.utcnow()).isoformat(),
                    "url": info.get("url"),
                    "event_id": info.get("event_id"),
                    "reliability_score": info.get("reliability_score", 0.5)
                }
            }
            
            doc_ref = self.gcp.firestore.collection('rag_documents').document(doc_id)
            doc_ref.set(rag_document)
            
            logger.info(f"Stored document {doc_id} to RAG system")
            
        except Exception as e:
            logger.error(f"Failed to store to RAG system: {e}")
    
    async def _store_to_firestore(self, info: Dict[str, Any], event_id: str):
        try:
            doc_id = info.get("content_hash", str(uuid.uuid4()))
            
            doc_ref = self.gcp.firestore.collection('collected_info').document(doc_id)
            doc_ref.set({
                **info,
                "stored_at": datetime.utcnow().isoformat()
            })
            
            incident_ref = self.gcp.firestore.collection('incidents').document(event_id)
            incident_ref.update({
                "collected_info": firestore.ArrayUnion([doc_id])
            })
            
        except Exception as e:
            logger.error(f"Failed to store to Firestore: {e}")
    
    async def _generate_collection_summary(self, processed_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not processed_info:
            return {"message": "No information collected"}
        
        try:
            sources = {}
            urgency_levels = {"low": 0, "medium": 0, "high": 0}
            
            for item in processed_info:
                source = item.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
                
                urgency = item.get("urgency_level", "low")
                urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            return {
                "total_items": len(processed_info),
                "sources": sources,
                "urgency_distribution": urgency_levels,
                "latest_timestamp": max(
                    [item.get("timestamp", datetime.min) for item in processed_info],
                    default=datetime.utcnow()
                ).isoformat() if processed_info else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {"error": "Summary generation failed"}