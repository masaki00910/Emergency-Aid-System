#!/usr/bin/env python3
"""
Production FAQ API with real Vertex AI integration
"""

import os
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import logging
from typing import List, Dict, Any

# 環境変数設定
os.environ['GOOGLE_CLOUD_PROJECT'] = 'sharelabai-hackathon2'
os.environ['USE_MOCK_LLM'] = 'false'

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

# Firestoreクライアント設定
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
    logger.info("✅ Firestore client available")
except ImportError:
    logger.error("❌ google-cloud-firestore not available. Please install: pip install google-cloud-firestore")
    FIRESTORE_AVAILABLE = False

class ProductionFAQHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Vertex AI クライアント初期化
        try:
            from shared.utils.sync_vertex_ai_client import get_sync_vertex_ai_client
            self.vertex_client = get_sync_vertex_ai_client()
            logger.info(f"✅ Vertex AI client initialized")
            logger.info(f"   project_id: {self.vertex_client.project_id}")
            logger.info(f"   is_local_mode: {self.vertex_client.is_local_mode}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI: {e}")
            self.vertex_client = None
        
        # Firestore クライアント初期化
        self.db = None
        if FIRESTORE_AVAILABLE:
            try:
                self.db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT', 'sharelabai-hackathon2'))
                logger.info("✅ Firestore client initialized")
            except Exception as e:
                logger.error(f"❌ Firestore initialization failed: {e}")
                self.db = None
        
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """GET request handling"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        logger.info(f"🌐 GET Request: {path}")
        
        if path == '/health':
            self.send_json_response({'status': 'healthy', 'vertex_ai': self.vertex_client is not None})
        elif path.startswith('/api/public/faq/') and not path.endswith('/ask'):
            # Handle FAQ list for disaster: /api/public/faq/{disaster_id}
            disaster_id = path.split('/')[-1]
            self.handle_faq_list(disaster_id)
        elif path == '/api/public/faq/active':
            self.handle_active_faqs()
        elif path == '/api/public/disasters':
            self.handle_disasters()
        elif path == '/api/alerts':
            self.handle_alerts()
        elif path == '/api/feeds':
            self.handle_feeds()
        else:
            self.send_json_response({'status': 'ok', 'message': 'Production FAQ API with Vertex AI'})
    
    def do_POST(self):
        """POST request handling"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        logger.info(f"🌐 POST Request: {path}")
        
        if path.startswith('/api/public/faq/') and path.endswith('/ask'):
            self.handle_faq_question()
        else:
            self.send_error_response(404, 'Not Found')
    
    def handle_faq_question(self):
        """FAQ質問処理 - 実際のVertex AI使用"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(request_body)
            
            question = request_data.get('question', '')
            logger.info(f"❓ FAQ Question: {question}")
            
            if not self.vertex_client:
                answer = "Vertex AIクライアントが利用できません。システム管理者にお問い合わせください。"
                model_used = "error"
            else:
                # 災害コンテキストを取得
                disaster_context = self.get_disaster_context()
                
                # 実際のVertex AI（Gemini 2.5）で回答生成
                logger.info(f"🤖 Generating answer with Vertex AI...")
                try:
                    # コンテキスト込みでFAQ回答を生成
                    prompt = f"""あなたは災害情報の専門家です。以下の災害情報を踏まえて、ユーザーの質問に具体的で実用的な回答を提供してください。

災害情報:
{disaster_context}

ユーザーの質問: {question}

回答は以下の点を含めてください:
- 具体的な行動指針
- 安全確保の方法  
- 緊急時の連絡先
- 避難に関する情報（必要に応じて）

300文字程度で、分かりやすく回答してください。"""

                    answer = self.vertex_client.generate_text(prompt)
                    model_used = "gemini-2.5-flash"
                    logger.info(f"✅ Answer generated successfully")
                except Exception as e:
                    logger.error(f"❌ Vertex AI error: {e}")
                    answer = f"申し訳ございません。AI回答の生成中にエラーが発生しました: {str(e)}"
                    model_used = "gemini-2.5-flash-error"
            
            response = {
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().isoformat() + 'Z',
                'model_used': model_used
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"❌ FAQ processing error: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.send_error_response(500, str(e))
    
    def handle_faq_list(self, disaster_id):
        """FAQ一覧を生成 - LLMで動的生成"""
        try:
            logger.info(f"🤖 Generating FAQ list for disaster: {disaster_id}")
            
            if not self.vertex_client:
                # Fallback to basic FAQs
                faqs = self.get_fallback_faqs(disaster_id)
            else:
                # 災害コンテキストを取得
                disaster_context = self.get_disaster_context()
                
                # LLMでFAQ生成
                faqs = self.generate_faqs_with_llm(disaster_id, disaster_context)
            
            response = {
                "disaster_id": disaster_id,
                "disaster_title": "金沢市内での大雨による洪水警報",
                "hazard_type": "flood",
                "area": "金沢市",
                "faqs": faqs,
                "last_updated": datetime.now().isoformat() + 'Z'
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"❌ FAQ list generation error: {e}")
            # Fallback to basic FAQs
            faqs = self.get_fallback_faqs(disaster_id)
            response = {
                "disaster_id": disaster_id,
                "disaster_title": "金沢市内での大雨による洪水警報", 
                "hazard_type": "flood",
                "area": "金沢市",
                "faqs": faqs,
                "last_updated": datetime.now().isoformat() + 'Z'
            }
            self.send_json_response(response)
    
    def generate_faqs_with_llm(self, disaster_id, context):
        """LLMでFAQを動的生成"""
        try:
            prompt = f"""あなたは災害対応の専門家です。以下の災害情報に基づいて、住民が最も知りたがる重要なFAQを3つ生成してください。

災害情報:
{context}

以下のJSON形式で回答してください:
[
  {{
    "question": "質問文",
    "answer": "具体的で実用的な回答（200文字程度）",
    "category": "action_guide|evacuation|safety_tips|preparation|recovery のいずれか",
    "priority": 1
  }}
]

質問は災害の種類と地域に特化し、実際に住民が知りたい内容にしてください。"""

            response_text = self.vertex_client.generate_text(prompt)
            logger.info(f"🤖 LLM FAQ Response: {response_text}")
            
            # JSONパース
            try:
                faq_data = json.loads(response_text.strip())
                if not isinstance(faq_data, list):
                    raise ValueError("Expected list format")
                
                # FAQデータを整形
                faqs = []
                for i, faq in enumerate(faq_data[:3]):  # 最大3つ
                    faqs.append({
                        "id": f"{disaster_id}_llm_faq_{i+1}",
                        "disaster_id": disaster_id,
                        "question": faq.get("question", ""),
                        "answer": faq.get("answer", ""),
                        "category": faq.get("category", "action_guide"),
                        "priority": i + 1,
                        "created_at": datetime.now().isoformat() + 'Z'
                    })
                
                return faqs
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error: {e}")
                return self.get_fallback_faqs(disaster_id)
                
        except Exception as e:
            logger.error(f"❌ LLM FAQ generation error: {e}")
            return self.get_fallback_faqs(disaster_id)
    
    def get_fallback_faqs(self, disaster_id):
        """フォールバック用の基本FAQ"""
        return [
            {
                "id": f"{disaster_id}_fallback_1",
                "disaster_id": disaster_id,
                "question": "災害時の基本的な対応は？",
                "answer": "まず安全確保を最優先に行動してください。避難が必要な場合は、指定された避難場所へ向かい、正確な情報を確認してください。",
                "category": "action_guide",
                "priority": 1,
                "created_at": datetime.now().isoformat() + 'Z'
            },
            {
                "id": f"{disaster_id}_fallback_2",
                "disaster_id": disaster_id,
                "question": "避難のタイミングは？",
                "answer": "避難準備情報が発表されたら、高齢者や移動が困難な方は避難を開始してください。避難勧告が出されたら、速やかに避難してください。",
                "category": "evacuation",
                "priority": 2,
                "created_at": datetime.now().isoformat() + 'Z'
            },
            {
                "id": f"{disaster_id}_fallback_3",
                "disaster_id": disaster_id,
                "question": "緊急時の連絡方法は？",
                "answer": "緊急時は119番（消防・救急）または110番（警察）に連絡してください。災害用伝言ダイヤル171も活用できます。",
                "category": "safety_tips",
                "priority": 3,
                "created_at": datetime.now().isoformat() + 'Z'
            }
        ]
    
    def get_disaster_context(self):
        """災害コンテキストを取得"""
        return """
災害タイプ: 洪水
地域: 金沢市
重要度: 高
説明: 犀川・浅野川流域で水位上昇。避難準備情報が発表されています。
状況: 大雨により河川水位が上昇中。浸水被害の可能性があります。
対象地域: 金沢市内の犀川・浅野川流域
避難情報: 高齢者等避難開始
"""
    
    def handle_active_faqs(self):
        """アクティブなFAQ一覧"""
        self.send_json_response([])
    
    def handle_disasters(self):
        """災害一覧データ - Firestoreから取得"""
        try:
            disasters = self.fetch_disasters_from_firestore()
            
            response = {
                "disasters": disasters,
                "total": len(disasters),
                "source": "firestore+vertex_ai",
                "timestamp": datetime.now().isoformat() + 'Z'
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch disasters: {e}")
            # フォールバック用サンプルデータ
            fallback_disasters = [
                {
                    "id": "sample-disaster-1",
                    "title": "金沢市内での大雨による洪水警報",
                    "description": "犀川・浅野川流域で水位上昇。避難準備情報が発表されています。",
                    "type": "flood",
                    "severity": "high",
                    "location": {"lat": 36.5944, "lng": 136.6258, "admin": "金沢市"},
                    "reported_at": "2025-09-22T15:00:00Z",
                    "confidence": 0.9,
                    "source": ["金沢市防災"],
                    "evidence": [],
                    "status": "active"
                }
            ]
            
            response = {
                "disasters": fallback_disasters,
                "total": len(fallback_disasters),
                "source": "fallback_data",
                "error": str(e)
            }
            
            self.send_json_response(response)
    
    def handle_alerts(self):
        """アラート一覧"""
        alerts = [{
            "id": "alert-1",
            "title": "洪水警報 - 金沢市",
            "level": "warning",
            "hazard": "flood",
            "area": "金沢市",
            "startedAt": 1727023200000,
            "summary": "犀川・浅野川流域で水位上昇中",
            "description": "大雨により河川水位が上昇しています。避難準備情報に注意してください。"
        }]
        
        self.send_json_response(alerts)
    
    def handle_feeds(self):
        """フィード一覧 - Firestoreから取得してLLMで拡張"""
        try:
            # Firestoreから実際の災害データを取得
            disasters = self.fetch_disasters_from_firestore()
            
            # 災害データをフィード形式に変換
            firestore_feeds = self.convert_disasters_to_feeds(disasters)
            
            if self.vertex_client and len(firestore_feeds) > 0:
                # LLMで追加フィードを生成（実際のデータに基づく）
                additional_feeds = self.generate_feeds_with_llm_from_real_data(disasters)
                all_feeds = firestore_feeds + additional_feeds
            else:
                all_feeds = firestore_feeds
                
            logger.info(f"📡 Generated {len(all_feeds)} feeds from Firestore data")
            self.send_json_response(all_feeds)
            
        except Exception as e:
            logger.error(f"❌ Feed generation error: {e}")
            # フォールバック
            fallback_feeds = self.get_base_feeds()
            self.send_json_response(fallback_feeds)
    
    def get_base_feeds(self):
        """基本フィードデータ"""
        return [
            {
                "id": "feed-1",
                "incidentId": "sample-disaster-1",
                "title": "金沢市内での大雨による洪水警報",
                "source": "金沢市防災",
                "publishedAt": 1727023200000,
                "area": "金沢市",
                "hazard": "flood",
                "category": "洪水",
                "severity": "high",
                "summary": "犀川・浅野川流域で水位上昇。避難準備情報が発表されています。",
                "url": "#",
                "labels": ["flood", "high"],
                "isAlertCandidate": True,
                "status": "active",
                "risk_assessment": "high",
                "has_analysis": True,
                "has_collected_info": True
            }
        ]
    
    def generate_feeds_with_llm(self):
        """LLMで追加フィードを生成"""
        try:
            prompt = """金沢市の洪水災害に関する追加の情報フィードを3つ生成してください。
各フィードは異なる情報源（河川管理課、気象庁、危機管理課など）からの情報とし、
時系列で情報が更新されている状況を表現してください。

以下のJSON形式で回答してください:
[
  {
    "title": "フィードタイトル",
    "source": "情報源",
    "category": "カテゴリ",
    "summary": "要約（100文字程度）",
    "severity": "high|medium|low"
  }
]"""

            response_text = self.vertex_client.generate_text(prompt)
            
            try:
                feed_data = json.loads(response_text.strip())
                additional_feeds = []
                
                for i, feed in enumerate(feed_data[:3]):
                    additional_feeds.append({
                        "id": f"feed-llm-{i+2}",
                        "incidentId": "sample-disaster-1",
                        "title": feed.get("title", "LLM生成フィード"),
                        "source": feed.get("source", "AI生成"),
                        "publishedAt": 1727023200000 - (i+1) * 3600000,  # 1時間ずつ前
                        "area": "金沢市",
                        "hazard": "flood",
                        "category": feed.get("category", "情報"),
                        "severity": feed.get("severity", "medium"),
                        "summary": feed.get("summary", "LLMにより生成された情報"),
                        "url": "#",
                        "labels": ["llm-generated", feed.get("severity", "medium")],
                        "isAlertCandidate": feed.get("severity") == "high",
                        "status": "active",
                        "risk_assessment": feed.get("severity", "medium"),
                        "has_analysis": True,
                        "has_collected_info": True
                    })
                
                return additional_feeds
                
            except json.JSONDecodeError:
                logger.error("❌ Failed to parse LLM feed response")
                return []
                
        except Exception as e:
            logger.error(f"❌ LLM feed generation error: {e}")
            return []
    
    def fetch_disasters_from_firestore(self) -> List[Dict[str, Any]]:
        """Firestoreから災害データを取得"""
        if not self.db:
            logger.warning("❌ Firestore client not available, using fallback data")
            return []
        
        try:
            logger.info("🔍 Querying Firestore for disasters...")
            
            # 'incidents' コレクションから取得
            collection_ref = self.db.collection('incidents')
            
            # 最新順でソート
            query = collection_ref.order_by('detected_at', direction=firestore.Query.DESCENDING)
            
            # 最大50件に制限
            query = query.limit(50)
            
            docs = query.stream()
            disasters = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # フロントエンド互換性のためデータ変換
                transformed_data = self.transform_firestore_data(data)
                disasters.append(transformed_data)
            
            logger.info(f"✅ Found {len(disasters)} disasters in Firestore")
            return disasters
            
        except Exception as e:
            logger.error(f"❌ Firestore query failed: {e}")
            return []
    
    def transform_firestore_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Firestoreデータをフロントエンド形式に変換"""
        try:
            # 基本的な変換
            transformed = {
                'id': data.get('id', ''),
                'title': data.get('title', '不明な災害'),
                'description': data.get('description', data.get('title', '')),
                'type': data.get('type', data.get('hazard', 'other')),
                'severity': self.convert_severity(data.get('severity', 2)),
                'location': data.get('location', {'lat': 35.6762, 'lng': 139.6503, 'admin': '不明'}),
                'reported_at': self.convert_timestamp(data.get('detected_at', data.get('reported_at'))),
                'confidence': data.get('confidence', 0.8),
                'source': data.get('source', ['API']),
                'evidence': data.get('evidence', []),
                'status': self.determine_status(data),
                'is_active': True,
                'affected_population': data.get('affected_population'),
                'risk_assessment': data.get('risk_assessment', 'unknown'),
                'has_analysis': data.get('has_analysis', False),
                'has_collected_info': data.get('has_collected_info', False)
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"❌ Transform error: {e}")
            return data
    
    def convert_severity(self, severity):
        """数値の重要度を文字列に変換"""
        if isinstance(severity, (int, float)):
            if severity >= 3:
                return 'high'
            elif severity >= 2:
                return 'medium'
            else:
                return 'low'
        return severity or 'medium'
    
    def convert_timestamp(self, timestamp):
        """タイムスタンプを変換"""
        if timestamp:
            if hasattr(timestamp, 'isoformat'):
                return timestamp.isoformat() + 'Z'
            elif isinstance(timestamp, str):
                return timestamp
        return datetime.now().isoformat() + 'Z'
    
    def determine_status(self, data):
        """ステータスを決定"""
        severity = data.get('severity', 2)
        if isinstance(severity, (int, float)) and severity >= 3:
            return 'active'
        return 'monitoring'
    
    def convert_disasters_to_feeds(self, disasters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """災害データをフィード形式に変換"""
        feeds = []
        
        for disaster in disasters:
            feed = {
                "id": f"feed-{disaster['id']}",
                "incidentId": disaster['id'],
                "title": disaster['title'],
                "source": disaster.get('source', ['不明'])[0] if disaster.get('source') else '不明',
                "publishedAt": int(datetime.fromisoformat(disaster['reported_at'].replace('Z', '+00:00')).timestamp() * 1000),
                "area": disaster.get('location', {}).get('admin', '不明'),
                "hazard": disaster['type'],
                "category": self.get_hazard_category(disaster['type']),
                "severity": disaster['severity'],
                "summary": disaster['description'],
                "url": "#",
                "labels": [disaster['type'], disaster['severity']],
                "isAlertCandidate": disaster['severity'] == 'high',
                "status": disaster['status'],
                "risk_assessment": disaster.get('risk_assessment', 'unknown'),
                "has_analysis": disaster.get('has_analysis', False),
                "has_collected_info": disaster.get('has_collected_info', False)
            }
            feeds.append(feed)
        
        return feeds
    
    def get_hazard_category(self, hazard_type: str) -> str:
        """ハザードタイプを日本語カテゴリに変換"""
        hazard_mapping = {
            'earthquake': '地震',
            'tsunami': '津波',
            'flood': '洪水',
            'typhoon': '台風',
            'landslide': '土砂災害',
            'volcano': '火山',
            'wildfire': '山火事',
            'other': 'その他'
        }
        return hazard_mapping.get(hazard_type, hazard_type)
    
    def generate_feeds_with_llm_from_real_data(self, disasters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """実際の災害データに基づいてLLMで追加フィードを生成"""
        if not disasters:
            return []
        
        try:
            # 最新の災害情報を基にプロンプトを作成
            latest_disaster = disasters[0]
            disaster_context = f"""
現在の災害状況:
- 災害タイプ: {latest_disaster['type']}
- 地域: {latest_disaster.get('location', {}).get('admin', '不明')}
- 重要度: {latest_disaster['severity']}
- 説明: {latest_disaster['description']}
"""

            prompt = f"""現在の災害状況に基づいて、関連する追加の情報フィードを2つ生成してください。

{disaster_context}

以下のJSON形式で回答してください:
[
  {{
    "title": "フィードタイトル",
    "source": "情報源",
    "category": "カテゴリ",
    "summary": "要約（100文字程度）",
    "severity": "high|medium|low"
  }}
]"""

            response_text = self.vertex_client.generate_text(prompt)
            
            try:
                feed_data = json.loads(response_text.strip())
                additional_feeds = []
                
                for i, feed in enumerate(feed_data[:2]):
                    additional_feeds.append({
                        "id": f"feed-llm-{i+1}",
                        "incidentId": latest_disaster['id'],
                        "title": feed.get("title", "LLM生成フィード"),
                        "source": feed.get("source", "AI生成"),
                        "publishedAt": int((datetime.now().timestamp() - (i+1) * 3600) * 1000),
                        "area": latest_disaster.get('location', {}).get('admin', '不明'),
                        "hazard": latest_disaster['type'],
                        "category": feed.get("category", "情報"),
                        "severity": feed.get("severity", "medium"),
                        "summary": feed.get("summary", "LLMにより生成された関連情報"),
                        "url": "#",
                        "labels": ["llm-generated", feed.get("severity", "medium")],
                        "isAlertCandidate": feed.get("severity") == "high",
                        "status": "active",
                        "risk_assessment": feed.get("severity", "medium"),
                        "has_analysis": True,
                        "has_collected_info": True
                    })
                
                return additional_feeds
                
            except json.JSONDecodeError:
                logger.error("❌ Failed to parse LLM feed response")
                return []
                
        except Exception as e:
            logger.error(f"❌ LLM feed generation error: {e}")
            return []
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {'error': message}
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

def main():
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting Production FAQ API with Vertex AI on port {port}")
    
    server = HTTPServer(('0.0.0.0', port), ProductionFAQHandler)
    logger.info(f"✅ Server running on port {port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()