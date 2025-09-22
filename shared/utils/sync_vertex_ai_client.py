#!/usr/bin/env python3
"""
同期版Vertex AI Client
非同期処理の問題を回避するためのシンプルな同期クライアント
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SyncVertexAIClient:
    """同期版Vertex AI Client"""
    
    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        self.project_id = project_id
        self.location = location
        self.is_local_mode = self._is_local_mode()
        
        if self.is_local_mode:
            logger.info("🔧 Running in local mode - using intelligent mock responses")
        else:
            logger.info(f"🚀 Running in production mode - using real Vertex AI")
            self._init_vertex_ai()
    
    def _is_local_mode(self) -> bool:
        """ローカル開発環境かどうかを判定"""
        use_mock = os.getenv("USE_MOCK_LLM", "").lower()
        if use_mock in ["true", "1", "yes"]:
            return True
        if use_mock in ["false", "0", "no"]:
            return False
        
        # デフォルトはローカルモード（安全側）
        return True
    
    def _init_vertex_ai(self):
        """実際のVertex AI初期化"""
        try:
            from langchain_google_vertexai import VertexAI
            from google.cloud import aiplatform
            
            aiplatform.init(project=self.project_id, location=self.location)
            
            self._llm = VertexAI(
                model_name="gemini-2.5-flash",
                temperature=0.1,
                max_output_tokens=8192,
                project=self.project_id,
                location=self.location
            )
            logger.info("✅ Vertex AI initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI: {e}")
            self.is_local_mode = True
            logger.info("🔧 Falling back to local mode")
    
    def answer_with_faq(self, faqs: List[Dict[str, str]], user_question: str) -> str:
        """FAQ-based answer generation (sync)"""
        if self.is_local_mode:
            return self._generate_local_answer(user_question)
        else:
            return self._generate_vertex_ai_answer(faqs, user_question)
    
    def generate_text(self, prompt: str) -> str:
        """General text generation (sync)"""
        if self.is_local_mode:
            return self._generate_local_answer(prompt)
        else:
            return self._generate_vertex_ai_text(prompt)
    
    def _generate_local_answer(self, user_question: str) -> str:
        """ローカル環境での詳細回答生成"""
        question_lower = user_question.lower()
        
        # 金沢特有の質問
        if "金沢" in user_question and "避難" in user_question:
            return """金沢市にお住まいの方の避難について回答いたします。

**緊急避難場所：**
• 金沢市役所（広坂1-1-1）
• 石川県庁（鞍月1-1）
• 金沢駅周辺の指定避難所

**避難の目安：**
• 災害の種類により異なりますが、一般的に市街地から10-15km離れた高台や堅固な建物への避難をおすすめします
• 犀川・浅野川の氾濫が懸念される場合は、河川から離れた高台（例：卯辰山方面、野田山方面）へ
• 地震の場合は、まず最寄りの小中学校などの指定避難所へ

**アクセス手段：**
• 公共交通機関が停止している可能性があるため、徒歩での避難ルートを事前に確認
• 北陸自動車道が利用可能な場合は、福井方面または富山方面への避難も検討

現在の災害状況に応じて、金沢市の防災情報や石川県の災害情報を随時確認してください。"""
        
        # 災害準備の質問
        if "準備" in user_question:
            return """災害への準備について、以下の重要な項目をご確認ください：

**緊急持ち出し品（最優先）：**
• 現金、通帳、印鑑、身分証明書
• 飲料水（1人1日3L、3日分）
• 非常食（3日分以上）
• 懐中電灯、ラジオ、電池
• 救急医薬品、常用薬

**避難準備：**
• 避難場所・避難ルートの確認
• 家族との連絡方法の確認
• 重要書類のコピー保管
• 近隣住民との連携体制

**情報収集手段：**
• 防災行政無線
• 携帯電話の緊急速報メール
• ラジオ（AM/FM）
• インターネット（自治体HP、SNS）

準備は早めに、そして定期的な点検をお忘れなく。"""
        
        # 安全確保の質問
        if "安全" in user_question:
            return """災害時の安全確保について重要なポイントをお伝えします：

**身の安全確保（最優先）：**
• まず自分の身を守る（頭部保護、安全な場所への移動）
• 落下物や倒壊の危険から離れる
• ガス漏れ、火災の確認と対処

**状況判断：**
• 周囲の状況を冷静に確認
• 信頼できる情報源からの情報収集
• 避難の必要性を適切に判断

**避難時の注意：**
• 慌てずに冷静な行動
• 近隣住民との協力
• 要支援者（高齢者、障害者、乳幼児）への配慮

**二次災害の防止：**
• 余震への警戒
• 土砂災害、浸水等の危険性確認
• 不安定な建物からの離脱

安全第一で行動し、無理をしないことが最も重要です。"""
        
        # デフォルトの詳細回答
        return f"""ご質問「{user_question}」について回答いたします。

災害時における基本的な対応として、以下の点を重視してください：

1. **安全確保**: 何よりもまず身の安全を確保
2. **情報収集**: 信頼できる情報源からの正確な情報入手
3. **適切な判断**: 状況に応じた冷静な判断と行動
4. **連携**: 家族・地域・行政との適切な連携

具体的な状況や地域については、お住まいの自治体の防災情報、気象庁の発表、緊急速報等を確認してください。

ご不明な点がございましたら、お近くの避難所や自治体にお問い合わせください。"""
    
    def _generate_vertex_ai_answer(self, faqs: List[Dict[str, str]], user_question: str) -> str:
        """実際のVertex AIでの回答生成"""
        try:
            faq_context = "\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in faqs])
            
            prompt = f"""あなたは災害情報の専門家としてFAQ対応を行うアシスタントです。
以下のFAQを参考にしてください。FAQに直接回答がなくても、関連知識から適切に答えてください。

FAQ一覧:
{faq_context}

ユーザの質問:
{user_question}

回答:"""
            
            response = self._llm.invoke(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Vertex AI generation failed: {e}")
            return self._generate_local_answer(user_question)
    
    def _generate_vertex_ai_text(self, prompt: str) -> str:
        """実際のVertex AIでのテキスト生成"""
        try:
            response = self._llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"❌ Vertex AI text generation failed: {e}")
            return self._generate_local_answer(prompt)

# グローバルクライアント
_sync_client = None

def get_sync_vertex_ai_client():
    """同期版Vertex AIクライアントの取得"""
    global _sync_client
    if _sync_client is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        _sync_client = SyncVertexAIClient(project_id)
    return _sync_client