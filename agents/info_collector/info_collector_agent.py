import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from bs4 import BeautifulSoup
import logging
from google.cloud import firestore

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
            # JMA RSS URL temporarily disabled due to 404 error
            # {"url": "https://www.jma.go.jp/bosai/forecast/data/forecast/rss/region.xml", "source": "jma", "type": "official"}
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
        logger.info(f"DEBUG: Starting news collection - disaster_type: {disaster_type}, time_window_hours: {time_window_hours}")
        news_items = []
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        logger.info(f"DEBUG: Cutoff time: {cutoff_time}")
        
        for source in self.news_sources:
            if source["type"] != "news":
                continue
                
            try:
                logger.info(f"DEBUG: Fetching from {source['source']} - {source['url']}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(source["url"], timeout=30.0)
                    response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                logger.info(f"DEBUG: Got {len(feed.entries)} entries from {source['source']}")
                
                for entry in feed.entries[:20]:
                    try:
                        entry_time = self._parse_entry_time(entry)
                        title = entry.get("title", "No title")
                        logger.info(f"DEBUG: Processing entry: {title[:50]}... Time: {entry_time}")
                        
                        if entry_time and entry_time < cutoff_time:
                            logger.info(f"DEBUG: Skipping old entry: {title[:50]}...")
                            continue
                        
                        content = self._extract_content(entry)
                        
                        is_relevant = await self._is_relevant_to_disaster(content, disaster_type, location)
                        logger.info(f"DEBUG: Relevance check for '{title[:50]}...': {is_relevant}")
                        
                        if is_relevant:
                            news_items.append({
                                "source": source["source"],
                                "type": "news",
                                "title": entry.get("title", ""),
                                "content": content,
                                "url": entry.get("link", ""),
                                "timestamp": entry_time or datetime.utcnow(),
                                "raw_entry": entry
                            })
                            logger.info(f"DEBUG: Added relevant news item: {title[:50]}...")
                    except Exception as e:
                        logger.error(f"Failed to process news entry: {e}")
                
                logger.info(f"DEBUG: Collected {len([item for item in news_items if item['source'] == source['source']])} items from {source['source']}")
            except Exception as e:
                logger.error(f"Failed to fetch from {source['source']}: {e}")
        
        logger.info(f"DEBUG: Total news items collected: {len(news_items)}")
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
            # More comprehensive disaster relevance checking
            prompt = f"""
以下のニュース内容が災害情報として収集すべき内容かを判定してください。

災害関連キーワード例：
- 気象災害：台風、豪雨、大雨、洪水、雷雨、雷、暴風、竜巻、雹、雪害、吹雪
- 地震・津波：地震、津波、震度、マグニチュード、余震
- その他災害：土砂崩れ、山崩れ、火災、火事、停電、断水、避難、警報、注意報
- 緊急・危険：緊急事態、危険、警戒、被害、救助、災害対策

参考情報：
- 現在の災害タイプ: {disaster_type}
- 対象地域: {location.get('admin', '日本全国')}

分析対象内容:
{content[:1500]}

判定基準：
1. 上記の災害関連キーワードが含まれている
2. 気象警報・注意報に関する情報
3. 防災・避難に関する情報
4. インフラ被害や社会への影響
5. 緊急性の高い安全情報

以下の形式で回答してください：
{{
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "keywords_found": ["見つかったキーワード"],
    "reasoning": "判定理由"
}}
"""
            logger.info(f"DEBUG: Checking relevance for disaster_type='{disaster_type}', location='{location.get('admin', '')}'")
            logger.info(f"DEBUG: Content preview: {content[:200]}...")
            
            # Use the global client to ensure proper Vertex AI usage
            if hasattr(vertex_ai_client, 'llm_gemini_flash') and vertex_ai_client.llm_gemini_flash:
                response = await vertex_ai_client.llm_gemini_flash.ainvoke(prompt)
                logger.info(f"DEBUG: AI relevance response: {response}")
                
                # Try to parse JSON response
                try:
                    import json
                    response_text = response.strip()
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]
                    
                    parsed_response = json.loads(response_text)
                    is_relevant = parsed_response.get("is_relevant", False)
                    confidence = parsed_response.get("confidence", 0.0)
                    keywords_found = parsed_response.get("keywords_found", [])
                    reasoning = parsed_response.get("reasoning", "")
                    
                    logger.info(f"DEBUG: Parsed relevance result: relevant={is_relevant}, confidence={confidence}, keywords={keywords_found}")
                    logger.info(f"DEBUG: Reasoning: {reasoning}")
                    
                    return is_relevant and confidence >= 0.3
                    
                except json.JSONDecodeError:
                    # Fallback to keyword-based analysis when JSON parsing fails
                    logger.warning(f"Failed to parse JSON response, using keyword-based fallback: {response}")
                    
                    # Check if this is a mock response
                    if "モック応答" in response or "mock" in response.lower():
                        logger.warning("Detected mock response, using keyword-based analysis")
                        disaster_keywords = ['災害', '地震', '津波', '台風', '洪水', '土砂', '避難', '警報', '注意報', 
                                           '大雨', '暴雨', '線状降水帯', '氾濫', '浸水', '落雷', '雷', '雨', '風', 
                                           '被害', '倒壊', '停電', '断水', '緊急', '危険', '警戒', 'クマ', '熊', 
                                           '動物', '襲撃', '襲われ', '大けが', '重傷', '安全対策', '品薄']
                        
                        found_keywords = [kw for kw in disaster_keywords if kw in content]
                        has_keywords = len(found_keywords) > 0
                        
                        logger.info(f"DEBUG: Mock response fallback - keyword check: {has_keywords}, found: {found_keywords}")
                        return has_keywords
                    
                    # Try simple text parsing for real responses
                    response_lower = response.lower()
                    is_relevant = ("true" in response_lower and "is_relevant" in response_lower) or \
                                ("relevant" in response_lower and "true" in response_lower)
                    
                    # Additional keyword safety net
                    disaster_keywords = ['災害', '地震', '津波', '台風', '洪水', '土砂', '避難', '警報', '注意報', 
                                       '大雨', '暴雨', '線状降水帯', '氾濫', '浸水', '落雷', '雷', '雨', '風', 
                                       '被害', '倒壊', '停電', '断水', '緊急', '危険', '警戒', 'クマ', '熊', 
                                       '動物', '襲撃', '襲われ', '大けが', '重傷', '安全対策', '品薄']
                    
                    has_disaster_keyword = any(keyword in content for keyword in disaster_keywords)
                    
                    if has_disaster_keyword and not is_relevant:
                        logger.info(f"DEBUG: Overriding AI decision - disaster keywords found: {[kw for kw in disaster_keywords if kw in content]}")
                        return True
                    
                    return is_relevant
            else:
                # Fallback if client not properly initialized
                logger.warning("Vertex AI client not properly initialized, using keyword-based fallback")
                disaster_keywords = ['災害', '地震', '津波', '台風', '洪水', '土砂', '避難', '警報', '注意報', 
                                   '大雨', '暴雨', '線状降水帯', '氾濫', '浸水', '落雷', '雷', '雨', '風', 
                                   '被害', '倒壊', '停電', '断水', '緊急', '危険', '警戒']
                
                found_keywords = [kw for kw in disaster_keywords if kw in content]
                has_keywords = len(found_keywords) > 0
                
                logger.info(f"DEBUG: Keyword-based relevance check: {has_keywords}, found: {found_keywords}")
                return has_keywords
            
        except Exception as e:
            logger.error(f"Relevance check failed: {e}")
            import traceback
            logger.error(f"Relevance check traceback: {traceback.format_exc()}")
            # Default to True to avoid losing potentially relevant content
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
            
            # Use the global client to ensure proper Vertex AI usage
            if hasattr(vertex_ai_client, 'llm_gemini_flash') and vertex_ai_client.llm_gemini_flash:
                response = await vertex_ai_client.llm_gemini_flash.ainvoke(prompt)
                enhanced_data = vertex_ai_client._parse_json_response(response)
            else:
                # Fallback if client not properly initialized
                logger.warning("Vertex AI client not properly initialized, using basic enhancement")
                enhanced_data = {
                    "key_facts": [item.get('title', 'Unknown')],
                    "entities": [],
                    "urgency_level": "medium",
                    "reliability_score": 0.5,
                    "summary": item.get('title', 'No summary available')
                }
            
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