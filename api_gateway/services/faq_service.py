import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.cloud import firestore
from models.public_api import FAQModel, FAQResponse, FAQAnswerResponse
from shared.utils.vertex_ai_client import get_vertex_ai_client

logger = logging.getLogger(__name__)

class FAQService:
    def __init__(self):
        self.db = firestore.Client()
        self.ai_client = get_vertex_ai_client()
        # メモリキャッシュ（簡易版）
        self._faq_cache = {}
        self._answer_cache = {}
        self._cache_ttl = timedelta(minutes=30)  # 30分間キャッシュ
        
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """キャッシュの有効性確認"""
        return datetime.now() - cache_entry['timestamp'] < self._cache_ttl
    
    async def get_faqs_by_disaster(self, disaster_id: str) -> Optional[FAQResponse]:
        """災害IDに基づいてFAQを取得（キャッシュ対応）"""
        try:
            # キャッシュ確認
            if disaster_id in self._faq_cache and self._is_cache_valid(self._faq_cache[disaster_id]):
                logger.info(f"FAQ cache hit for disaster: {disaster_id}")
                return self._faq_cache[disaster_id]['data']
            # Firestoreからincident情報を取得
            disaster_ref = self.db.collection('incidents').document(disaster_id)
            disaster_doc = disaster_ref.get()
            
            if not disaster_doc.exists:
                logger.warning(f"Disaster not found: {disaster_id}")
                return None
                
            disaster_data = disaster_doc.to_dict()
            
            # FAQチャットログから既存のFAQを取得
            faq_ref = self.db.collection('faq_chat_logs').document(disaster_id)
            faq_doc = faq_ref.get()
            
            faqs = []
            if faq_doc.exists:
                faq_data = faq_doc.to_dict()
                stored_faqs = faq_data.get('faqs', [])
                
                for i, stored_faq in enumerate(stored_faqs):
                    faqs.append(FAQModel(
                        id=f"{disaster_id}_faq_{i}",
                        disaster_id=disaster_id,
                        question=stored_faq.get('question', ''),
                        answer=stored_faq.get('answer', ''),
                        category=stored_faq.get('category', 'action_guide'),
                        priority=stored_faq.get('priority', i + 1),
                        created_at=datetime.fromisoformat(faq_data.get('created_at', datetime.now().isoformat()))
                    ))
            else:
                # FAQが存在しない場合は動的生成
                faqs = await self._generate_faqs_for_disaster(disaster_id, disaster_data)
                
            faq_response = FAQResponse(
                disaster_id=disaster_id,
                disaster_title=disaster_data.get('title', ''),
                hazard_type=disaster_data.get('type', 'other'),
                area=disaster_data.get('location', {}).get('admin', ''),
                faqs=faqs,
                last_updated=datetime.now()
            )
            
            # キャッシュに保存
            self._faq_cache[disaster_id] = {
                'data': faq_response,
                'timestamp': datetime.now()
            }
            logger.info(f"FAQ cached for disaster: {disaster_id}")
            
            return faq_response
            
        except Exception as e:
            logger.error(f"Error getting FAQs for disaster {disaster_id}: {e}")
            return None
    
    async def _generate_faqs_for_disaster(self, disaster_id: str, disaster_data: Dict[str, Any]) -> List[FAQModel]:
        """災害情報を元にAIでFAQを生成"""
        try:
            # 災害情報からコンテキストを構築
            context = f"""
            災害タイトル: {disaster_data.get('title', '')}
            災害種別: {disaster_data.get('type', '')}
            地域: {disaster_data.get('location', {}).get('admin', '')}
            重要度: {disaster_data.get('severity', '')}
            説明: {disaster_data.get('description', '')}
            """
            
            # キーワード抽出
            keywords = await self.ai_client.extract_keywords(context, max_keywords=3)
            
            # 各キーワードでFAQ生成
            all_faqs = []
            for keyword in keywords:
                keyword_faqs = await self.ai_client.generate_faq_dynamic(keyword, context)
                all_faqs.extend(keyword_faqs)
            
            # FAQモデルに変換
            faqs = []
            categories = ['action_guide', 'safety_tips', 'evacuation', 'preparation', 'recovery']
            
            for i, faq_data in enumerate(all_faqs[:5]):  # 最大5個のFAQ
                faqs.append(FAQModel(
                    id=f"{disaster_id}_generated_{i}",
                    disaster_id=disaster_id,
                    question=faq_data.get('question', ''),
                    answer=faq_data.get('answer', ''),
                    category=categories[i % len(categories)],
                    priority=i + 1,
                    created_at=datetime.now()
                ))
            
            # Firestoreに保存
            await self._save_faqs_to_firestore(disaster_id, faqs)
            
            return faqs
            
        except Exception as e:
            logger.error(f"Error generating FAQs for disaster {disaster_id}: {e}")
            return []
    
    async def _save_faqs_to_firestore(self, disaster_id: str, faqs: List[FAQModel]):
        """生成されたFAQをFirestoreに保存"""
        try:
            faq_data = {
                'faqs': [
                    {
                        'question': faq.question,
                        'answer': faq.answer,
                        'category': faq.category,
                        'priority': faq.priority
                    }
                    for faq in faqs
                ],
                'user_interactions': [],
                'created_at': datetime.now().isoformat()
            }
            
            faq_ref = self.db.collection('faq_chat_logs').document(disaster_id)
            faq_ref.set(faq_data)
            
        except Exception as e:
            logger.error(f"Error saving FAQs to Firestore: {e}")
    
    async def answer_question(self, disaster_id: str, question: str) -> FAQAnswerResponse:
        """AIを使って質問に回答（キャッシュ対応）"""
        try:
            # 質問のキャッシュキー作成
            cache_key = f"{disaster_id}:{hash(question.strip().lower())}"
            
            # キャッシュ確認
            if cache_key in self._answer_cache and self._is_cache_valid(self._answer_cache[cache_key]):
                logger.info(f"Answer cache hit for question: {question[:50]}...")
                return self._answer_cache[cache_key]['data']
            # 既存のFAQを取得
            faq_response = await self.get_faqs_by_disaster(disaster_id)
            
            if not faq_response:
                return FAQAnswerResponse(
                    question=question,
                    answer="申し訳ございませんが、この災害に関する情報が見つかりません。",
                    timestamp=datetime.now(),
                    model_used="error"
                )
            
            # FAQを辞書形式に変換
            faqs_dict = [
                {
                    'question': faq.question,
                    'answer': faq.answer
                }
                for faq in faq_response.faqs
            ]
            
            # AIで回答生成
            answer = await self.ai_client.answer_with_faq(faqs_dict, question)
            
            # デバッグ：LLMの実際の出力をログ出力
            logger.info(f"LLM Raw Answer: {repr(answer)}")
            logger.info(f"LLM Answer Length: {len(answer)}")
            
            # ユーザーインタラクションを記録
            await self._save_user_interaction(disaster_id, question, answer)
            
            answer_response = FAQAnswerResponse(
                question=question,
                answer=answer,
                timestamp=datetime.now(),
                model_used="gemini-1.5-flash"
            )
            
            # 回答をキャッシュに保存
            self._answer_cache[cache_key] = {
                'data': answer_response,
                'timestamp': datetime.now()
            }
            logger.info(f"Answer cached for question: {question[:50]}...")
            
            return answer_response
            
        except Exception as e:
            logger.error(f"Error answering question for disaster {disaster_id}: {e}")
            return FAQAnswerResponse(
                question=question,
                answer="申し訳ございませんが、回答の生成に失敗しました。しばらく時間をおいて再度お試しください。",
                timestamp=datetime.now(),
                model_used="error"
            )
    
    async def _save_user_interaction(self, disaster_id: str, question: str, answer: str):
        """ユーザーインタラクションをFirestoreに保存"""
        try:
            faq_ref = self.db.collection('faq_chat_logs').document(disaster_id)
            faq_doc = faq_ref.get()
            
            if faq_doc.exists:
                faq_data = faq_doc.to_dict()
                interactions = faq_data.get('user_interactions', [])
            else:
                interactions = []
            
            # 新しいインタラクションを追加
            interactions.append({
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().isoformat()
            })
            
            # Firestoreを更新
            faq_ref.update({'user_interactions': interactions})
            
        except Exception as e:
            logger.error(f"Error saving user interaction: {e}")

# サービスインスタンス
faq_service = FAQService()