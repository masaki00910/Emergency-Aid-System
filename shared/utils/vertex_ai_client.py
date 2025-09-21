import os
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
import logging

from .mock_llm_client import create_mock_vertex_ai_client


logger = logging.getLogger(__name__)


class VertexAIClient:
    def __init__(self, project_id: str, location: str = "asia-northeast1"):#"us-central1"
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
        return (
            os.getenv("FIRESTORE_EMULATOR_HOST") is not None or
            os.getenv("PUBSUB_EMULATOR_HOST") is not None or
            os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        )
    
    @property
    def llm_gemini_pro(self):
        if self.is_local_mode:
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._llm_gemini_pro is None:
            self._llm_gemini_pro = VertexAI(
                model_name="gemini-2.5-flash",
                temperature=0.1,
                max_output_tokens=8192,
                project=self.project_id,
                location=self.location
            )
        return self._llm_gemini_pro
    
    @property
    def llm_gemini_flash(self):
        if self.is_local_mode:
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._llm_gemini_flash is None:
            self._llm_gemini_flash = VertexAI(
                model_name="gemini-2.5-flash-lite",
                temperature=0.1,
                max_output_tokens=8192,
                project=self.project_id,
                location=self.location
            )
        return self._llm_gemini_flash
    
    @property
    def embeddings(self):
        if self.is_local_mode:
            if self._mock_client is None:
                self._mock_client = create_mock_vertex_ai_client(self.project_id, self.location)
            return self._mock_client
        
        if self._embeddings is None:
            self._embeddings = VertexAIEmbeddings(
                model_name="textembedding-gecko-multilingual@001",
                project=self.project_id,
                location=self.location
            )
        return self._embeddings
    
    async def generate_disaster_analysis(self, content: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_local_mode:
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
            response = await self.llm_gemini_flash.ainvoke(prompt)
            return self._parse_json_response(response)
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
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "JSON parsing failed", "raw_response": response}
        
        
    async def extract_keywords(self, content: str, max_keywords: int = 3) -> List[str]:
        """
        災害関連のキーワードをAIで抽出
        """
        prompt = f"""
    あなたは災害情報の専門家です。以下の文章から災害に関連する重要なキーワードを{max_keywords}個抽出してください。
    回答はJSON配列で返してください。

    文章:
    {content}

    回答例:
    ["地震", "津波", "避難"]

    キーワード:
    """
        try:
            response = await self.llm_gemini_pro.ainvoke(prompt)
            import json
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Vertex AI keyword extraction failed: {e}")
            return []

    async def generate_faq_dynamic(self, keyword: str, context: str) -> List[Dict[str, str]]:
        """
        与えられたキーワードと文章コンテキストからFAQを生成
        """
        prompt = f"""
あなたはFAQ生成の専門家です。以下のキーワードに関するFAQを文章コンテキストを考慮して作成してください。
FAQは必ず3つ生成してください。
重複は避けてください。

キーワード: {keyword}
文章: {context}

JSON形式で回答してください:
[
  {{"question": "質問文", "answer": "回答文"}}
]
"""
        try:
            response = await self.llm_gemini_pro.ainvoke(prompt)
            import json
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            faqs = json.loads(response_text)
            # dict なら list に変換
            if isinstance(faqs, dict):
                faqs = [faqs]
            return faqs
        except Exception as e:
            logger.error(f"Vertex AI FAQ generation failed: {e}")
            return [{"question": f"{keyword}に関する質問生成失敗", "answer": ""}]
        
        
    async def answer_with_faq(self, faqs: List[Dict[str, str]], user_question: str) -> str:
        """
        FAQとユーザの質問を元に回答を生成
        """
        faq_context = "\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in faqs])

        prompt = f"""
あなたは災害情報の専門家としてFAQ対応を行うアシスタントです。
以下のFAQを参考にしてください。FAQに直接回答がなくても、関連知識から適切に答えてください。

FAQ一覧:
{faq_context}

ユーザの質問:
{user_question}

回答:
"""

        try:
            response = await self.llm_gemini_pro.ainvoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"FAQ answer generation failed: {e}")
            return "すみません、回答を生成できませんでした。"        

vertex_ai_client = VertexAIClient(os.getenv("GOOGLE_CLOUD_PROJECT", ""))