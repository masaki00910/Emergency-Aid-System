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
        self.similarity_threshold = 0.8  # 意味的類似度しきい値
        self.similarity_time_window_hours = 24  # 類似度チェックの時間窓
    
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
            logger.info(f"DEBUG: Checking duplicate for content: {content_text[:100]}...")
            
            # 1. ハッシュベースの完全一致チェック
            doc_ref = self.gcp.firestore.collection('processed_content').document(content_hash)
            doc = doc_ref.get()
            
            if doc.exists:
                logger.info("DEBUG: Exact hash match found - duplicate")
                return True
            
            # 2. 意味的類似度チェック（災害関連のみ）
            disaster_keywords = ['災害', '地震', '津波', '台風', '洪水', '土砂', '避難', '警報', '注意報', 
                               '大雨', '暴雨', '線状降水帯', '氾濫', '浸水', '落雷', '雷', '雨', '風', 
                               '被害', '倒壊', '停電', '断水', '緊急', '危険', '警戒']
            
            has_disaster_keyword = any(keyword in content_text for keyword in disaster_keywords)
            
            if has_disaster_keyword:
                logger.info(f"DEBUG: Disaster keywords found: {[kw for kw in disaster_keywords if kw in content_text]}")
                
                # 意味的類似度チェック
                similar_content = await self._check_semantic_similarity(content_text, content_hash)
                if similar_content:
                    logger.info(f"DEBUG: Semantic similarity found - merging with existing content: {similar_content}")
                    await self._merge_similar_content(content_hash, content_text, similar_content)
                    return True
            
            # 3. 新規コンテンツとして保存
            logger.info("DEBUG: New content, not a duplicate")
            await self._save_content_with_embedding(content_hash, content_text, has_disaster_keyword)
            return False
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            import traceback
            logger.error(f"Duplicate check traceback: {traceback.format_exc()}")
            return False
    
    async def _check_semantic_similarity(self, content_text: str, current_hash: str) -> str:
        """
        意味的類似度チェック
        類似度がしきい値以上の既存コンテンツのハッシュを返す。なければNone。
        """
        try:
            # 現在のコンテンツの埋め込みベクトル生成
            current_embedding = await self._generate_embedding(content_text)
            if not current_embedding:
                logger.warning("Failed to generate embedding for current content")
                return None
            
            # 設定された時間窓での災害関連コンテンツから類似度チェック
            from datetime import timedelta
            time_threshold = datetime.utcnow() - timedelta(hours=self.similarity_time_window_hours)
            
            query = self.gcp.firestore.collection('processed_content')\
                .where('disaster_related', '==', True)\
                .where('processed_at', '>=', time_threshold)\
                .limit(50)  # パフォーマンス制限
            
            docs = query.stream()
            
            for doc in docs:
                doc_data = doc.to_dict()
                if doc.id == current_hash:
                    continue
                
                stored_embedding = doc_data.get('embedding')
                if not stored_embedding:
                    continue
                
                # コサイン類似度計算
                similarity = self._calculate_cosine_similarity(current_embedding, stored_embedding)
                logger.info(f"DEBUG: Similarity with {doc.id[:8]}...: {similarity:.3f}")
                
                if similarity >= self.similarity_threshold:
                    logger.info(f"High similarity found: {similarity:.3f} >= {self.similarity_threshold}")
                    return doc.id
            
            return None
            
        except Exception as e:
            logger.error(f"Semantic similarity check failed: {e}")
            return None
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        テキストの埋め込みベクトル生成
        """
        try:
            from shared.utils.vertex_ai_client import get_vertex_ai_client
            vertex_client = get_vertex_ai_client()
            
            # LangChainのVertexAIEmbeddingsを使用
            embedding_result = await vertex_client.embeddings.aembed_query(text)
            return embedding_result
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        コサイン類似度計算
        """
        try:
            import numpy as np
            
            # ベクトルを正規化
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            # コサイン類似度計算
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0
    
    async def _save_content_with_embedding(self, content_hash: str, content_text: str, is_disaster_related: bool):
        """
        コンテンツを埋め込みベクトルとともに保存
        """
        try:
            doc_data = {
                'processed_at': datetime.utcnow(),
                'disaster_related': is_disaster_related,
                'content_preview': content_text[:200]  # デバッグ用プレビュー
            }
            
            # 災害関連の場合のみ埋め込みベクトル生成・保存
            if is_disaster_related:
                embedding = await self._generate_embedding(content_text)
                if embedding:
                    doc_data['embedding'] = embedding
                    logger.info(f"Saved content with embedding (vector size: {len(embedding)})")
                else:
                    logger.warning("Failed to generate embedding, saving without vector")
            
            doc_ref = self.gcp.firestore.collection('processed_content').document(content_hash)
            doc_ref.set(doc_data)
            
        except Exception as e:
            logger.error(f"Failed to save content with embedding: {e}")
    
    async def _merge_similar_content(self, new_hash: str, new_content: str, existing_hash: str):
        """
        類似コンテンツの統合処理
        より詳細で信頼性の高いコンテンツを保持
        """
        try:
            # 既存コンテンツ情報取得
            existing_doc = self.gcp.firestore.collection('processed_content').document(existing_hash).get()
            if not existing_doc.exists:
                logger.warning(f"Existing document {existing_hash} not found for merging")
                return
            
            existing_data = existing_doc.to_dict()
            existing_preview = existing_data.get('content_preview', '')
            
            # より詳細なコンテンツを判定（文字数で簡易判定）
            if len(new_content) > len(existing_preview):
                logger.info(f"New content is more detailed ({len(new_content)} vs {len(existing_preview)} chars) - updating")
                
                # 新しいコンテンツで更新
                await self._save_content_with_embedding(existing_hash, new_content, True)
                
                # 新ハッシュは既存ハッシュへの参照として保存
                ref_data = {
                    'processed_at': datetime.utcnow(),
                    'disaster_related': True,
                    'merged_to': existing_hash,
                    'content_preview': new_content[:200]
                }
                self.gcp.firestore.collection('processed_content').document(new_hash).set(ref_data)
            else:
                logger.info(f"Existing content is more detailed - keeping original")
                
                # 新ハッシュは既存ハッシュへの参照として保存
                ref_data = {
                    'processed_at': datetime.utcnow(),
                    'disaster_related': True,
                    'merged_to': existing_hash,
                    'content_preview': new_content[:200]
                }
                self.gcp.firestore.collection('processed_content').document(new_hash).set(ref_data)
                
        except Exception as e:
            logger.error(f"Failed to merge similar content: {e}")
    
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