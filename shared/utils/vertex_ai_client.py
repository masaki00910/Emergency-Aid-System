import os
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
import logging

logger = logging.getLogger(__name__)

try:
    from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
    LANGCHAIN_AVAILABLE = True
    logger.info("DEBUG: LangChain Google VertexAI imported successfully")
except ImportError as e:
    # LangChain is optional for basic functionality
    VertexAI = None
    VertexAIEmbeddings = None
    LANGCHAIN_AVAILABLE = False
    logger.warning(f"DEBUG: Failed to import LangChain Google VertexAI: {e}")

from .mock_llm_client import create_mock_vertex_ai_client


class VertexAIClient:
    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        self.project_id = project_id
        self.location = location
        self.is_local_mode = self._is_local_mode()
        
        if not self.is_local_mode:
            aiplatform.init(project=project_id, location=location)
        
        self._llm_gemini_pro = None
        self._llm_gemini_flash = None
        self._embeddings = None
        self._mock_client = None
    
    def _is_local_mode(self) -> bool:
        """ローカル開発環境かどうかを判定"""
        # 強制的にUSE_MOCK_LLM環境変数を最優先で確認
        use_mock = os.getenv("USE_MOCK_LLM", "").lower()
        logger.info(f"DEBUG: USE_MOCK_LLM={use_mock}")
        
        if use_mock in ["false", "0", "no"]:
            logger.info("DEBUG: USE_MOCK_LLM explicitly set to false -> Real Vertex AI")
            return False
        if use_mock in ["true", "1", "yes"]:
            logger.info("DEBUG: USE_MOCK_LLM explicitly set to true -> Mock LLM")
            return True
            
        # Cloud Run環境を検知
        k_service = os.getenv("K_SERVICE")
        logger.info(f"DEBUG: K_SERVICE={k_service}")
        if k_service:
            logger.info("DEBUG: Cloud Run environment detected -> Real Vertex AI")
            return False  # Cloud Run環境ではデフォルトでReal Vertex AI使用
        
        # ローカル開発環境
        firestore_emulator = os.getenv("FIRESTORE_EMULATOR_HOST")
        pubsub_emulator = os.getenv("PUBSUB_EMULATOR_HOST")
        logger.info(f"DEBUG: FIRESTORE_EMULATOR_HOST={firestore_emulator}, PUBSUB_EMULATOR_HOST={pubsub_emulator}")
        
        is_local = (firestore_emulator is not None or pubsub_emulator is not None)
        logger.info(f"DEBUG: Local environment detected: {is_local} -> {'Mock LLM' if is_local else 'Real Vertex AI'}")
        return is_local
    
    @property
    def llm_gemini_pro(self):
        if self.is_local_mode:
            logger.info("DEBUG: Using local mode - initializing mock client")
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._llm_gemini_pro is None:
            logger.info(f"DEBUG: Initializing Gemini Pro - LANGCHAIN_AVAILABLE={LANGCHAIN_AVAILABLE}, VertexAI={VertexAI is not None}")
            if not LANGCHAIN_AVAILABLE:
                error_msg = "LangChain Google VertexAI not available - cannot create real client"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            if not VertexAI:
                error_msg = "VertexAI class not imported - LangChain integration failed"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            try:
                logger.info("DEBUG: Creating VertexAI Pro client...")
                self._llm_gemini_pro = VertexAI(
                    model_name="gemini-1.5-pro",
                    temperature=0.1,
                    max_output_tokens=8192,
                    project=self.project_id,
                    location=self.location
                )
                logger.info("DEBUG: VertexAI Pro client created successfully")
            except Exception as e:
                error_msg = f"Failed to create VertexAI Pro client: {e}"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise RuntimeError(error_msg) from e
        return self._llm_gemini_pro
    
    @property
    def llm_gemini_flash(self):
        if self.is_local_mode:
            logger.info("DEBUG: Using local mode - initializing mock client")
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._llm_gemini_flash is None:
            logger.info(f"DEBUG: Initializing Gemini Flash - LANGCHAIN_AVAILABLE={LANGCHAIN_AVAILABLE}, VertexAI={VertexAI is not None}")
            if not LANGCHAIN_AVAILABLE:
                error_msg = "LangChain Google VertexAI not available - cannot create real client"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            if not VertexAI:
                error_msg = "VertexAI class not imported - LangChain integration failed"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            try:
                logger.info("DEBUG: Creating VertexAI Flash client...")
                self._llm_gemini_flash = VertexAI(
                    model_name="gemini-1.5-flash",
                    temperature=0.1,
                    max_output_tokens=8192,
                    project=self.project_id,
                    location=self.location
                )
                logger.info("DEBUG: VertexAI Flash client created successfully")
            except Exception as e:
                error_msg = f"Failed to create VertexAI Flash client: {e}"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise RuntimeError(error_msg) from e
        return self._llm_gemini_flash
    
    @property
    def embeddings(self):
        if self.is_local_mode:
            logger.info("DEBUG: Using local mode - initializing mock client for embeddings")
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._embeddings is None:
            logger.info(f"DEBUG: Initializing Embeddings - LANGCHAIN_AVAILABLE={LANGCHAIN_AVAILABLE}, VertexAIEmbeddings={VertexAIEmbeddings is not None}")
            if not LANGCHAIN_AVAILABLE:
                error_msg = "LangChain Google VertexAI not available - cannot create embeddings"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            if not VertexAIEmbeddings:
                error_msg = "VertexAIEmbeddings class not imported - LangChain integration failed"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                raise RuntimeError(error_msg)
            
            try:
                logger.info("DEBUG: Creating VertexAI Embeddings client...")
                self._embeddings = VertexAIEmbeddings(
                    model_name="textembedding-gecko-multilingual@001",
                    project=self.project_id,
                    location=self.location
                )
                logger.info("DEBUG: VertexAI Embeddings client created successfully")
            except Exception as e:
                error_msg = f"Failed to create VertexAI Embeddings: {e}"
                logger.error(f"CRITICAL ERROR: {error_msg}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise RuntimeError(error_msg) from e
        return self._embeddings
    
    async def generate_disaster_analysis(self, content: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_local_mode:
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return await self._mock_client.generate_disaster_analysis(content, source_info)
        
        prompt = f"""
あなたは災害情報分析の専門家です。以下の情報を分析し、災害の発生を判定してください。

情報源: {source_info.get('source', '不明')}
取得日時: {source_info.get('timestamp', '不明')}
URL: {source_info.get('url', '不明')}

分析対象テキスト:
{content}

以下の形式でJSONで回答してください:
{{
    "is_disaster": true/false,
    "disaster_type": "earthquake|flood|typhoon|landslide|wildfire|snow|other",
    "location": {{"lat": 緯度, "lng": 経度, "admin": "行政区域名"}},
    "severity": 0.0-1.0の深刻度,
    "confidence": 0.0-1.0の信頼度,
    "summary": "簡潔な要約",
    "reasoning": "判定根拠"
}}

注意事項:
- 出典を明確にし、憶測や推測は避けてください
- 深刻度は人的被害・インフラ影響・緊急性を総合評価
- 信頼度は情報源の信頼性・内容の具体性で判定
"""
        
        try:
            import asyncio
            import random
            
            # レート制限対応のリトライ機能
            for attempt in range(3):
                try:
                    response = await self.llm_gemini_flash.ainvoke(prompt)
                    return self._parse_json_response(response)
                except Exception as e:
                    if "429" in str(e) or "Resource exhausted" in str(e):
                        if attempt < 2:  # 最後の試行以外でリトライ
                            wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
                            logger.warning(f"Rate limit hit, retrying in {wait_time:.2f}s (attempt {attempt + 1}/3)")
                            await asyncio.sleep(wait_time)
                            continue
                    raise e
            
        except Exception as e:
            logger.error(f"Vertex AI analysis failed: {e}")
            return {
                "is_disaster": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            import json
            import re
            
            response_text = response.strip()
            logger.debug(f"DEBUG: Original response: {response_text}")
            
            # Remove JSON code block markers
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Remove JSON comments (// comments)
            response_text = re.sub(r'//.*$', '', response_text, flags=re.MULTILINE)
            
            # Clean up any trailing commas before closing brackets/braces
            response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
            
            response_text = response_text.strip()
            logger.debug(f"DEBUG: Cleaned response: {response_text}")
            
            parsed_json = json.loads(response_text)
            logger.info(f"DEBUG: Successfully parsed JSON: {type(parsed_json)}")
            return parsed_json
            
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"error": "JSON parsing failed", "raw_response": response}


vertex_ai_client = VertexAIClient(os.getenv("GOOGLE_CLOUD_PROJECT", ""))