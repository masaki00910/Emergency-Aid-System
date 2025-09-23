#!/usr/bin/env python3
"""
災害情報システム - Firestore連携APIサーバー
リアルタイムでFirestoreからデータを取得し、フロントエンドに提供
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import sys
import asyncio

# 環境変数を確実に設定
os.environ['GOOGLE_CLOUD_PROJECT'] = 'sharelabai-hackathon2'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hiroki/Emergency-Aid-System/keys/service-account-key.json'
os.environ['USE_MOCK_LLM'] = 'false'

# Vertex AI クライアント統合（同期版）
try:
    import sys
    sys.path.append('/Users/hiroki/Emergency-Aid-System')
    from shared.utils.sync_vertex_ai_client import get_sync_vertex_ai_client
    VERTEX_AI_AVAILABLE = True
    print("✅ Sync Vertex AI client module imported successfully")
except ImportError as e:
    print(f"⚠️  Sync Vertex AI client not available: {e}")
    VERTEX_AI_AVAILABLE = False
    get_sync_vertex_ai_client = None

# 公的データソース統合
try:
    from official_data_sources import OfficialDataIntegrator
    OFFICIAL_SOURCES_AVAILABLE = True
    print("✅ Official data sources module loaded")
except ImportError as e:
    print(f"⚠️  Official data sources not available: {e}")
    OFFICIAL_SOURCES_AVAILABLE = False

# Firestoreクライアント設定
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    print("ERROR: google-cloud-firestore not available. Please install: pip install google-cloud-firestore")
    FIRESTORE_AVAILABLE = False

class FirestoreAPIHandler(BaseHTTPRequestHandler):
    """Firestore連携API ハンドラー"""
    
    def __init__(self, *args, **kwargs):
        # Firestoreクライアント初期化
        self.db = None
        if FIRESTORE_AVAILABLE:
            try:
                # エミュレータ設定確認
                if os.getenv('FIRESTORE_EMULATOR_HOST'):
                    print(f"🔧 Firestore Emulator: {os.getenv('FIRESTORE_EMULATOR_HOST')}")
                
                self.db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT', 'test-disaster-response'))
                print("✅ Firestore client initialized")
            except Exception as e:
                print(f"❌ Firestore initialization failed: {e}")
                self.db = None
        
        # 公的データソース統合初期化
        self.official_integrator = None
        if OFFICIAL_SOURCES_AVAILABLE:
            try:
                self.official_integrator = OfficialDataIntegrator()
                print("✅ Official data integrator initialized")
            except Exception as e:
                print(f"❌ Official data integrator initialization failed: {e}")
                self.official_integrator = None
        
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """CORS preflight request handling"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """GET request handling"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            print(f"🌐 API Request: {path}")
            
            if path == '/':
                self.handle_root()
            elif path == '/api/public/disasters':
                self.handle_disasters(query_params)
            elif path == '/api/public/disasters/official':
                self.handle_official_disasters(query_params)
            elif path.startswith('/api/public/disasters/'):
                path_parts = path.split('/')
                disaster_id = path_parts[-1]
                
                # 詳細データ用のサブエンドポイント
                if len(path_parts) > 5 and path_parts[-2] == 'disasters':
                    if disaster_id.endswith('/analysis'):
                        disaster_id = path_parts[-2]
                        self.handle_disaster_analysis(disaster_id)
                    elif disaster_id.endswith('/bulletins'):
                        disaster_id = path_parts[-2]
                        self.handle_disaster_bulletins(disaster_id)
                    elif disaster_id.endswith('/collected-info'):
                        disaster_id = path_parts[-2]
                        self.handle_disaster_collected_info(disaster_id)
                    else:
                        self.handle_disaster_detail(disaster_id)
                else:
                    self.handle_disaster_detail(disaster_id)
            elif path == '/api/public/disasters/map-data':
                self.handle_map_data(query_params)
            elif path.startswith('/api/public/faq/') and path != '/api/public/faq/active':
                # Handle FAQ for specific disaster: /api/public/faq/{disaster_id}
                disaster_id = path.split('/')[-1]
                self.handle_faq_by_disaster(disaster_id)
            elif path == '/api/public/faq/active':
                self.handle_active_faqs()
            elif path == '/api/alerts':
                self.handle_alerts(query_params)
            elif path == '/api/feeds':
                self.handle_feeds(query_params)
            elif path == '/api/incidents':
                self.handle_incidents(query_params)
            elif path == '/api/health':
                self.handle_health()
            elif path == '/api/debug/collections':
                self.handle_collections_debug()
            else:
                self.send_response(404)
                self.end_headers()
                response = {'error': 'Endpoint not found'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        """POST request handling"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"🌐 POST Request: {path}")
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            if path.startswith('/api/public/faq/') and path.endswith('/ask'):
                # Handle FAQ question: /api/public/faq/{disaster_id}/ask
                disaster_id = path.split('/')[-2]
                self.handle_faq_question(disaster_id, request_body)
            else:
                self.send_response(404)
                self.end_headers()
                response = {'error': 'POST endpoint not found'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ POST Request error: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_root(self):
        """ルート endpoint"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            'service': '災害情報システム - Firestore API Gateway',
            'version': '1.0.0',
            'firestore_status': 'connected' if self.db else 'unavailable',
            'emulator_mode': bool(os.getenv('FIRESTORE_EMULATOR_HOST')),
            'endpoints': [
                'GET /api/public/disasters - 災害一覧取得',
                'GET /api/public/disasters/{id} - 災害詳細取得',  
                'GET /api/public/disasters/map-data - マップ用データ',
                'GET /api/public/faq/{disaster_id} - 災害特化FAQ取得',
                'POST /api/public/faq/{disaster_id}/ask - FAQ質問',
                'GET /api/public/faq/active - アクティブ災害FAQ一覧',
                'GET /api/health - ヘルスチェック'
            ]
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disasters(self, query_params):
        """災害一覧 endpoint（公的データソース + Firestore統合）"""
        try:
            all_disasters = []
            data_sources = []
            
            # 公的データソース（Tier 1）から取得
            if self.official_integrator:
                try:
                    official_disasters = self.fetch_official_disasters(query_params)
                    if official_disasters:
                        all_disasters.extend(official_disasters)
                        data_sources.append('official')
                except Exception as e:
                    print(f"❌ Error fetching official disasters: {e}")
                    official_disasters = []
            
            # Firestoreデータを取得
            if self.db:
                try:
                    firestore_disasters = self.fetch_disasters_from_firestore(query_params)
                    if firestore_disasters:
                        all_disasters.extend(firestore_disasters)
                        data_sources.append('firestore')
                except Exception as e:
                    print(f"❌ Error fetching firestore disasters: {e}")
                    firestore_disasters = []
            
            # 統合データの重複削除
            print(f"🔍 Debug: Before deduplication - {len(all_disasters)} disasters")
            print(f"🔍 Debug: First 3 disasters types: {[type(d) for d in all_disasters[:3]]}")
            
            deduplicated_disasters = self.deduplicate_disasters_api_level(all_disasters)
            print(f"🔍 Debug: After deduplication - {len(deduplicated_disasters)} disasters")
            print(f"🔍 Debug: First 3 deduplicated types: {[type(d) for d in deduplicated_disasters[:3]]}")
            
            # 表示閾値でフィルタリング
            disasters = self.filter_by_display_threshold(deduplicated_disasters)
            print(f"🔍 Debug: After filtering - {len(disasters)} disasters")
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'disasters': disasters,
                'total': len(disasters),
                'timestamp': datetime.utcnow().isoformat(),
                'source': '+'.join(data_sources) if data_sources else 'fallback',
                'data_summary': {
                    'official_count': len([d for d in disasters if d is not None and d.get('official_source', False)]),
                    'firestore_count': len([d for d in disasters if d is not None and not d.get('official_source', False)]),
                    'sources_used': data_sources,
                    'total_raw': len(all_disasters),
                    'duplicates_removed': len(all_disasters) - len(disasters)
                }
            }
            
            print(f"✅ Disasters fetched: {len(disasters)} items (from {len(all_disasters)} raw items)")
            print(f"📤 Integrated response: Official={response['data_summary']['official_count']}, Firestore={response['data_summary']['firestore_count']}")
            print(f"🔄 Duplicates removed: {response['data_summary']['duplicates_removed']}")
            print(f"📤 Response structure: {{'disasters': {len(disasters)} items, 'total': {len(disasters)}, 'source': '{response['source']}'}}")
            if disasters:
                print(f"📋 First disaster keys: {list(disasters[0].keys())}")
                print(f"📋 First disaster title: {disasters[0].get('title', 'N/A')}")
            
            response_json = json.dumps(response, ensure_ascii=False, default=str)
            print(f"📤 Response JSON length: {len(response_json)} characters")
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            import traceback
            print(f"❌ Error fetching disasters: {e}")
            print(f"❌ Full traceback:")
            traceback.print_exc()
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e), 'traceback': traceback.format_exc()}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_official_disasters(self, query_params):
        """公的データソース災害一覧 endpoint"""
        try:
            # 公的データソースからのみ取得
            official_disasters = []
            if self.official_integrator:
                official_disasters = self.fetch_official_disasters(query_params)
            
            # 重複削除
            deduplicated_disasters = self.deduplicate_disasters_api_level(official_disasters)
            
            # 表示閾値でフィルタリング
            filtered_disasters = self.filter_by_display_threshold(deduplicated_disasters)
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'disasters': filtered_disasters,
                'total': len(filtered_disasters),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'official',
                'tier': 'Tier 1 (JMA + P2P)',
                'data_summary': {
                    'jma_count': len([d for d in filtered_disasters if d.get('data_source') == 'jma']),
                    'p2p_count': len([d for d in filtered_disasters if d.get('data_source') == 'p2p_earthquake']),
                    'total_official': len(filtered_disasters),
                    'raw_count': len(official_disasters),
                    'deduplicated_count': len(deduplicated_disasters),
                    'filtered_count': len(deduplicated_disasters) - len(filtered_disasters)
                }
            }
            
            print(f"✅ Official disasters filtered: {len(filtered_disasters)} items (from {len(deduplicated_disasters)} deduplicated)")
            print(f"📤 Official data response: JMA={response['data_summary']['jma_count']}, P2P={response['data_summary']['p2p_count']}")
            print(f"🚫 Filtered low-significance disasters: {response['data_summary']['filtered_count']}")
            
            if filtered_disasters:
                print(f"📋 First official disaster keys: {list(filtered_disasters[0].keys())}")
                print(f"📋 First official disaster title: {filtered_disasters[0].get('title', 'N/A')}")
            
            response_json = json.dumps(response, ensure_ascii=False, default=str)
            print(f"📤 Official response JSON length: {len(response_json)} characters")
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching official disasters: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disaster_detail(self, disaster_id: str):
        """災害詳細 endpoint"""
        try:
            disaster = self.fetch_disaster_detail_from_firestore(disaster_id)
            
            if disaster:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(disaster, ensure_ascii=False, default=str).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                response = {'error': 'Disaster not found'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Error fetching disaster detail: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_map_data(self, query_params):
        """マップデータ endpoint"""
        try:
            disasters = self.fetch_disasters_from_firestore(query_params)
            
            # マップ用に座標データのみ抽出
            map_data = []
            for disaster in disasters:
                if 'location' in disaster:
                    map_data.append({
                        'id': disaster.get('id'),
                        'title': disaster.get('title', disaster.get('summary', 'Unknown')),
                        'lat': disaster['location'].get('lat'),
                        'lng': disaster['location'].get('lng'),
                        'severity': disaster.get('severity', 'low'),
                        'type': disaster.get('type', 'other')
                    })
            
            self.send_response(200)
            self.end_headers()
            
            response = {
                'map_data': map_data,
                'total': len(map_data),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching map data: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_health(self):
        """ヘルスチェック endpoint"""
        firestore_status = 'ok' if self.db else 'unavailable'
        
        self.send_response(200)
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'firestore': firestore_status,
            'timestamp': datetime.utcnow().isoformat(),
            'emulator_mode': bool(os.getenv('FIRESTORE_EMULATOR_HOST'))
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_collections_debug(self):
        """Firestoreコレクション調査 endpoint"""
        try:
            if not self.db:
                self.send_response(503)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                response = {'error': 'Firestore not available'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return

            # 災害対応システムの主要コレクションを調査
            collections_to_check = [
                'incidents',           # 災害インシデント (Master)
                'bulletins',          # 公報・発表情報 (PR Agent)
                'analysis_results',   # 分析結果 (Analyzer Agent)
                'collected_info',     # 収集情報 (Info Collector Agent)
                'detection_logs',     # 検知ログ (Detection Agent)
                'orchestration_logs', # オーケストレーションログ (Orchestrator Agent)
                'support_requests',   # 支援要請 (Support Agent)
                'feed_items'          # フィード項目
            ]
            
            collection_status = {}
            total_documents = 0
            
            for collection_name in collections_to_check:
                try:
                    collection_ref = self.db.collection(collection_name)
                    
                    # ドキュメント数をカウント
                    docs = list(collection_ref.limit(1000).stream())  # 最大1000件で制限
                    doc_count = len(docs)
                    total_documents += doc_count
                    
                    # サンプルドキュメントの取得
                    sample_doc = None
                    sample_fields = []
                    if docs:
                        sample_doc = docs[0].to_dict()
                        sample_fields = list(sample_doc.keys()) if sample_doc else []
                        
                        # 最新のタイムスタンプを探す
                        latest_timestamp = None
                        for doc in docs[:5]:  # 最初の5件をチェック
                            doc_data = doc.to_dict()
                            for field in ['detected_at', 'created_at', 'timestamp', 'reported_at']:
                                if field in doc_data and doc_data[field]:
                                    try:
                                        if hasattr(doc_data[field], 'timestamp'):
                                            ts = doc_data[field].timestamp()
                                        else:
                                            from datetime import datetime
                                            ts = datetime.fromisoformat(str(doc_data[field]).replace('Z', '+00:00')).timestamp()
                                        
                                        if latest_timestamp is None or ts > latest_timestamp:
                                            latest_timestamp = ts
                                    except:
                                        pass
                    
                    collection_status[collection_name] = {
                        'document_count': doc_count,
                        'has_data': doc_count > 0,
                        'sample_fields': sample_fields[:10],  # 最初の10フィールドのみ
                        'latest_activity': datetime.fromtimestamp(latest_timestamp).isoformat() if latest_timestamp else None,
                        'status': 'active' if doc_count > 0 else 'empty'
                    }
                    
                except Exception as e:
                    collection_status[collection_name] = {
                        'document_count': 0,
                        'has_data': False,
                        'error': str(e),
                        'status': 'error'
                    }
            
            # 分析結果
            active_collections = [name for name, status in collection_status.items() if status.get('has_data', False)]
            empty_collections = [name for name, status in collection_status.items() if not status.get('has_data', False) and 'error' not in status]
            error_collections = [name for name, status in collection_status.items() if 'error' in status]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'firestore_status': 'connected',
                'total_documents': total_documents,
                'collections_summary': {
                    'total_checked': len(collections_to_check),
                    'active_collections': len(active_collections),
                    'empty_collections': len(empty_collections),
                    'error_collections': len(error_collections)
                },
                'collections': collection_status,
                'analysis': {
                    'active_collections': active_collections,
                    'empty_collections': empty_collections,
                    'error_collections': error_collections,
                    'potential_issues': []
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 潜在的な問題を特定
            if 'incidents' in empty_collections:
                response['analysis']['potential_issues'].append("incidents collection is empty - Detection Agent may not be running")
            if 'detection_logs' in empty_collections:
                response['analysis']['potential_issues'].append("detection_logs collection is empty - Detection Agent may not be processing RSS feeds")
            if len(active_collections) == 0:
                response['analysis']['potential_issues'].append("No collections have data - All agents may be offline")
            if 'orchestration_logs' in empty_collections and len(active_collections) > 0:
                response['analysis']['potential_issues'].append("orchestration_logs is empty but other collections have data - Orchestrator Agent may not be running")
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Collections debug error: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def deduplicate_disasters_api_level(self, disasters: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """API応答時重複削除 - タイトル類似度による重複削除"""
        if not disasters:
            return disasters
        
        print(f"🔍 Deduplication: Processing {len(disasters)} disasters")
        
        seen = {}
        
        # 時間でソート（最新が先）
        sorted_disasters = sorted(disasters, key=lambda x: self._get_timestamp(x), reverse=True)
        
        for i, disaster in enumerate(sorted_disasters):
            if disaster is None:
                print(f"⚠️ Debug: Found None disaster at index {i}")
                continue
            
            if not isinstance(disaster, dict):
                print(f"⚠️ Debug: Found non-dict disaster at index {i}: {type(disaster)}")
                continue
                
            # 類似度キー生成
            try:
                similarity_key = self.generate_similarity_key_api(disaster.get('title', ''))
                location_key = self.normalize_location_api(disaster.get('location', {}).get('admin', ''))
            except Exception as e:
                print(f"❌ Debug: Error processing disaster at index {i}: {e}")
                print(f"❌ Debug: Disaster data: {disaster}")
                continue
            
            # 組み合わせキー（タイトル + 場所）
            combined_key = f"{similarity_key}_{location_key}"
            
            existing = seen.get(combined_key)
            
            # 重複がない、または既存より新しい場合は更新
            if not existing or self._get_timestamp(disaster) > self._get_timestamp(existing):
                seen[combined_key] = disaster
        
        deduplicated = [d for d in seen.values() if d is not None]
        
        # 最新順で返す
        deduplicated.sort(key=lambda x: self._get_timestamp(x), reverse=True)
        
        print(f"✅ Deduplication: {len(disasters)} -> {len(deduplicated)} disasters (removed {len(disasters) - len(deduplicated)} duplicates)")
        
        return deduplicated
    
    def generate_similarity_key_api(self, title: str) -> str:
        """類似度キー生成（タイトル正規化）"""
        if not title:
            return ""
        
        # 日本語記号削除、空白削除、小文字化
        normalized = (title
                     .replace('「', '').replace('」', '').replace('。', '').replace('、', '')
                     .replace('！', '').replace('？', '').replace('・', '')
                     .replace(' ', '').replace('\t', '').replace('\n', '')
                     .replace(',', '').replace('.', '').replace('!', '').replace('?', '').replace('-', '')
                     .replace('（', '').replace('）', '').replace('(', '').replace(')', '')
                     .replace('年', '').replace('月', '').replace('日', '')
                     .replace('2024', '').replace('2025', '')
                     .lower())
        
        # キーワード抽出による類似度向上
        keywords = []
        disaster_keywords = ['地震', '津波', '台風', '洪水', '土砂災害', '豪雨', '雪', '火山', 'クマ', '熊']
        location_keywords = ['能登', '北海道', '福島', '石川', '東京', '大阪', '京都', '沖縄', '十島村']
        
        for keyword in disaster_keywords + location_keywords:
            if keyword in normalized:
                keywords.append(keyword)
        
        # キーワードがある場合はキーワードベース、ない場合は最初の20文字
        if keywords:
            return '_'.join(sorted(keywords))
        else:
            return normalized[:20]
    
    def normalize_location_api(self, location: str) -> str:
        """場所名正規化"""
        if not location:
            return ""
        
        # 地名の正規化
        normalized = location.lower()
        
        # 能登地方の統一
        if any(keyword in normalized for keyword in ['能登', 'のと']):
            return 'noto'
        
        # 北海道の統一
        if '北海道' in normalized or 'hokkaido' in normalized:
            return 'hokkaido'
        
        # 福島の統一
        if '福島' in normalized or 'fukushima' in normalized:
            return 'fukushima'
        
        # 石川の統一
        if '石川' in normalized or 'ishikawa' in normalized:
            return 'ishikawa'
        
        # 十島村の統一
        if '十島' in normalized or 'toshima' in normalized:
            return 'toshima'
        
        # 共通の地名修飾語を削除
        common_suffixes = ['県', '市', '区', '町', '村', '都', '府', '道', '地方', '半島']
        for suffix in common_suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break
        
        return normalized
    
    def _get_timestamp(self, disaster: Dict[Any, Any]) -> float:
        """災害データからタイムスタンプを抽出"""
        if disaster is None:
            return 0.0
            
        # reported_at または detected_at フィールドを探す
        timestamp_field = disaster.get('reported_at') or disaster.get('detected_at')
        if not timestamp_field:
            return 0.0
        
        try:
            if hasattr(timestamp_field, 'timestamp'):
                return timestamp_field.timestamp()
            else:
                from datetime import datetime
                dt = datetime.fromisoformat(str(timestamp_field).replace('Z', '+00:00'))
                return dt.timestamp()
        except Exception:
            return 0.0

    def filter_by_display_threshold(self, disasters: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """表示閾値による災害フィルタリング"""
        filtered_disasters = []
        filtered_count = 0
        
        for i, disaster in enumerate(disasters):
            if disaster is None:
                print(f"⚠️ Filter Debug: Found None disaster at index {i}")
                continue
            
            if not isinstance(disaster, dict):
                print(f"⚠️ Filter Debug: Found non-dict disaster at index {i}: {type(disaster)}")
                continue
                
            try:
                disaster_type = disaster.get('type', 'other')
                severity = disaster.get('severity', 'low')
            except Exception as e:
                print(f"❌ Filter Debug: Error accessing disaster fields at index {i}: {e}")
                print(f"❌ Filter Debug: Disaster data: {disaster}")
                continue
            
            # 地震の場合の詳細チェック
            if disaster_type == 'earthquake':
                earthquake_details = disaster.get('earthquake_details')
                if earthquake_details is None or not isinstance(earthquake_details, dict):
                    print(f"⚠️ Filter Debug: earthquake_details is {type(earthquake_details)} for disaster {disaster.get('id', 'unknown')}")
                    earthquake_details = {}
                
                magnitude = earthquake_details.get('magnitude', 0.0)
                max_scale = earthquake_details.get('max_scale', 0)
                max_intensity = earthquake_details.get('max_intensity', '1')
                
                # 地震表示閾値: M3.5以上 または 震度3以上
                if magnitude >= 3.5 or max_scale >= 30:
                    filtered_disasters.append(disaster)
                else:
                    filtered_count += 1
                    print(f"🚫 Filtered earthquake: M{magnitude}, 震度{max_intensity} (below threshold)")
            
            # 津波の場合は常に表示
            elif disaster_type == 'tsunami':
                filtered_disasters.append(disaster)
            
            # その他の災害の場合
            else:
                # 深刻度によるフィルタリング
                if severity in ['medium', 'high']:
                    filtered_disasters.append(disaster)
                elif severity == 'low':
                    # 低い深刻度でも一部の災害種別は表示
                    if disaster_type in ['flood', 'typhoon', 'landslide', 'volcano', 'wildfire']:
                        filtered_disasters.append(disaster)
                    else:
                        filtered_count += 1
                        print(f"🚫 Filtered low-severity disaster: {disaster.get('title', 'Unknown')[:30]}...")
                else:  # very_low や不明な深刻度
                    filtered_count += 1
                    print(f"🚫 Filtered very low disaster: {disaster.get('title', 'Unknown')[:30]}...")
        
        if filtered_count > 0:
            print(f"📊 Display filtering: {len(disasters)} -> {len(filtered_disasters)} disasters (filtered {filtered_count})")
        
        return filtered_disasters

    def fetch_official_disasters(self, query_params) -> List[Dict[Any, Any]]:
        """公的データソース（Tier 1）から災害情報を取得"""
        if not self.official_integrator:
            print("❌ Official data integrator not available")
            return []
        
        try:
            print("🏛️  Fetching from official sources (JMA + P2P)...")
            
            # 時間範囲の設定
            hours = int(query_params.get('hours', [72])[0])  # デフォルト3日間
            
            # 公的ソースからデータ取得
            official_disasters = self.official_integrator.get_latest_disasters(hours=hours)
            
            # フロントエンド用にデータ変換
            transformed_disasters = []
            for disaster in official_disasters:
                try:
                    transformed_data = self.transform_official_data(disaster)
                    transformed_disasters.append(transformed_data)
                except Exception as e:
                    print(f"❌ Transform error for official data: {e}")
                    # 変換エラーでもrawデータを保持
                    transformed_disasters.append(disaster)
            
            print(f"✅ Found {len(transformed_disasters)} disasters from official sources")
            return transformed_disasters
            
        except Exception as e:
            print(f"❌ Official sources query failed: {e}")
            return []
    
    def transform_official_data(self, official_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """公的データソースのデータをフロントエンド用に変換"""
        try:
            # 日時変換 - フロントエンドが期待するミリ秒エポック形式
            detected_at = official_data.get('detected_at')
            if isinstance(detected_at, str):
                try:
                    dt = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
                    reported_at = int(dt.timestamp() * 1000)  # ミリ秒エポック
                except:
                    reported_at = int(datetime.utcnow().timestamp() * 1000)
            elif hasattr(detected_at, 'timestamp'):
                reported_at = int(detected_at.timestamp() * 1000)
            else:
                reported_at = int(datetime.utcnow().timestamp() * 1000)
            
            # 位置情報の正規化
            location = official_data.get('location', {})
            lat = location.get('lat', 35.6762)
            lng = location.get('lng', 139.6503)
            area = location.get('admin', '不明')
            
            # フロントエンド用disaster_type → hazard マッピング
            disaster_type = official_data.get('type', 'other')
            hazard_mapping = {
                'earthquake': 'earthquake',
                'tsunami': 'tsunami', 
                'typhoon': 'typhoon',
                'flood': 'flood',
                'landslide': 'landslide',
                'volcano': 'other',  # volcanoはotherに
                'wildfire': 'wildfire',
                'snow': 'other',
                'other': 'other'
            }
            hazard = hazard_mapping.get(disaster_type, 'other')
            
            # 深刻度の正規化（文字列形式を維持）
            severity = official_data.get('severity', 'medium')
            if severity not in ['low', 'medium', 'high']:
                severity = 'medium'  # デフォルト値
            
            # アクティブ状態判定（6時間以内の公的データはアクティブ）
            current_time = int(datetime.utcnow().timestamp() * 1000)
            time_diff = current_time - reported_at
            is_active = time_diff < (6 * 60 * 60 * 1000)  # 6時間 = 6*60*60*1000ms
            
            # フロントエンド期待フォーマット（Incident型）に変換
            return {
                # Incident型必須フィールド
                'id': official_data.get('id', f"official_{int(reported_at/1000)}"),
                'title': official_data.get('title', '公的災害情報'),
                'lat': lat,
                'lng': lng,
                'severity': severity,  # 'low'|'medium'|'high' 文字列
                'reportedAt': reported_at,  # ミリ秒エポック
                'isActive': is_active,  # boolean
                'hazard': hazard,  # 'earthquake'|'typhoon'|'flood'|'landslide'|'tsunami'|'wildfire'|'other'
                'area': area,
                'description': official_data.get('description', official_data.get('summary', '詳細情報なし')),
                
                # 追加の互換性フィールド（レガシー）
                'type': disaster_type,
                'location': location,
                'detected_at': detected_at,
                'reported_at': reported_at,  # 両方の形式をサポート
                'confidence': official_data.get('confidence', 0.9),
                'source': [official_data.get('source', 'official')],
                'evidence': official_data.get('evidence', []),
                'status': 'active' if is_active else 'monitoring',
                'official_source': True,
                'data_source': official_data.get('source', 'official'),
                'earthquake_details': official_data.get('earthquake_details'),
                
                # Enhanced Fields（フロントエンドダッシュボード用）
                'bulletins_count': 1,
                'latest_bulletin_id': official_data.get('id', f"official_{int(reported_at/1000)}"),
                'affected_population': self._estimate_affected_population(severity, disaster_type),
                'risk_assessment': severity,
                'related_news_count': 1,
                'has_analysis': True,
                'has_collected_info': True
            }
            
        except Exception as e:
            print(f"❌ Official data transformation error: {e}")
            return official_data
    
    def _estimate_affected_population(self, severity: str, disaster_type: str) -> int:
        """深刻度と災害種別から影響人口を推定"""
        base_population = {
            'high': 10000,
            'medium': 1000, 
            'low': 100
        }.get(severity, 1000)
        
        # 災害種別による調整
        type_multiplier = {
            'earthquake': 2.0,
            'tsunami': 3.0,
            'typhoon': 1.5,
            'flood': 1.2,
            'landslide': 0.8,
            'wildfire': 0.5
        }.get(disaster_type, 1.0)
        
        return int(base_population * type_multiplier)

    def fetch_disasters_from_firestore(self, query_params) -> List[Dict[Any, Any]]:
        """Firestoreから災害データを取得"""
        if not self.db:
            print("❌ Firestore client not available")
            raise Exception("Firestore client not initialized. Please check your GCP credentials and configuration.")
        
        try:
            print("🔍 Querying Firestore for disasters...")
            
            # incidentsコレクションからデータを取得
            collection_ref = self.db.collection('incidents')
            
            # クエリパラメータによるフィルタリング
            query = collection_ref.order_by('detected_at', direction=firestore.Query.DESCENDING)
            
            # 件数制限
            limit = int(query_params.get('limit', [50])[0])
            query = query.limit(limit)
            
            docs = query.stream()
            disasters = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                print(f"🔍 Raw Firestore data for {doc.id}:")
                print(f"   Keys: {list(data.keys())}")
                print(f"   Title: {data.get('title', 'N/A')}")
                print(f"   Type: {data.get('type', 'N/A')}")
                print(f"   Severity: {data.get('severity', 'N/A')}")
                print(f"   Summary: {data.get('summary', 'N/A')[:50]}...")
                print(f"   Detected: {data.get('detected_at', 'N/A')}")
                
                # フロントエンド用にデータ変換
                try:
                    transformed_data = self.transform_firestore_data(data)
                    print(f"✅ Transformed data keys: {list(transformed_data.keys())}")
                    print(f"   Status: {transformed_data.get('status', 'N/A')}")
                    print(f"   Title: {transformed_data.get('title', 'N/A')[:50]}...")
                    disasters.append(transformed_data)
                except Exception as e:
                    print(f"❌ Transform error for {doc.id}: {e}")
                    # 変換エラーでもrawデータを保持
                    disasters.append(data)
            
            print(f"✅ Found {len(disasters)} disasters in Firestore")
            print(f"📋 Sample disaster data: {disasters[0] if disasters else 'None'}")
            
            return disasters
            
        except Exception as e:
            print(f"❌ Firestore query failed: {e}")
            raise Exception(f"Failed to query Firestore: {str(e)}")

    def fetch_disaster_detail_from_firestore(self, disaster_id: str) -> Optional[Dict[Any, Any]]:
        """Firestoreから災害詳細データを取得"""
        if not self.db:
            return None
            
        try:
            doc_ref = self.db.collection('incidents').document(disaster_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return self.transform_firestore_data(data)
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error fetching disaster detail: {e}")
            return None

    def transform_firestore_data(self, firestore_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """FirestoreデータをFrontend用に変換"""
        try:
            # 🔍 Enhanced Fields デバッグログ - 生データ確認
            event_id = firestore_data.get('event_id', firestore_data.get('id', 'unknown'))
            print(f"\n🔍 [ENHANCED FIELDS DEBUG] Processing disaster: {event_id}")
            print(f"📄 Raw Firestore Data Keys: {list(firestore_data.keys())}")
            
            # Enhanced Fields の元データ確認
            bulletins_raw = firestore_data.get('bulletins', [])
            analysis_results_raw = firestore_data.get('analysis_results', [])
            collected_info_raw = firestore_data.get('collected_info', [])
            
            print(f"📊 Raw Enhanced Data:")
            print(f"   bulletins: {bulletins_raw} (type: {type(bulletins_raw)})")
            print(f"   analysis_results: {analysis_results_raw} (type: {type(analysis_results_raw)})")
            print(f"   collected_info: {collected_info_raw} (type: {type(collected_info_raw)})")
            
            # 特別なフィールドの確認
            special_fields = ['last_bulletin_at', 'orchestration_started_at']
            for field in special_fields:
                if field in firestore_data:
                    print(f"   {field}: {firestore_data[field]} (type: {type(firestore_data[field])})")
                else:
                    print(f"   {field}: NOT FOUND")
            # 深刻度を文字列に変換（FE要件準拠）
            severity_value = firestore_data.get('severity', 0.5)
            if isinstance(severity_value, (int, float)):
                if severity_value >= 0.7:
                    severity = 'high'
                elif severity_value >= 0.4:
                    severity = 'medium'
                else:
                    severity = 'low'
            else:
                severity = str(severity_value).lower()
                # 文字列の場合も正規化
                if severity not in ['high', 'medium', 'low']:
                    severity = 'low'
            
            # 日付変換
            detected_at = firestore_data.get('detected_at')
            if hasattr(detected_at, 'timestamp'):
                reported_at = detected_at.isoformat()
            elif isinstance(detected_at, str):
                reported_at = detected_at
            else:
                reported_at = datetime.utcnow().isoformat()
            
            # ステータス判定ロジック
            # 深刻度が0.5以上かつ24時間以内の災害をactiveとする
            detected_at = firestore_data.get('detected_at')
            is_recent = False
            if detected_at:
                try:
                    if hasattr(detected_at, 'timestamp'):
                        detected_time = detected_at
                    else:
                        from datetime import datetime
                        detected_time = datetime.fromisoformat(str(detected_at).replace('Z', '+00:00'))
                    
                    from datetime import datetime, timezone, timedelta
                    time_diff = datetime.now(timezone.utc) - detected_time.replace(tzinfo=timezone.utc)
                    is_recent = time_diff < timedelta(hours=24)
                except Exception:
                    is_recent = True  # エラー時はactiveとする
            
            severity_value = firestore_data.get('severity', 0.0)
            is_active = is_recent and (severity_value >= 0.5)
            
            # 追加データの処理
            bulletins = firestore_data.get('bulletins', [])
            analysis_results = firestore_data.get('analysis_results', [])
            collected_info = firestore_data.get('collected_info', [])
            
            # 最新の公報情報を取得
            latest_bulletin_id = None
            if bulletins:
                latest_bulletin_id = bulletins[-1] if isinstance(bulletins, list) else bulletins
            
            # 分析結果から影響度を算出
            affected_population = 0
            risk_assessment = 'unknown'
            if analysis_results:
                # 最新の分析結果を使用
                latest_analysis = analysis_results[-1] if isinstance(analysis_results, list) else analysis_results
                if isinstance(latest_analysis, dict):
                    affected_population = latest_analysis.get('affected_population', 0)
                    risk_assessment = latest_analysis.get('risk_level', 'unknown')
            
            # 収集情報から関連ニュース数を算出
            related_news_count = len(collected_info) if isinstance(collected_info, list) else 0
            
            # 🔍 Enhanced Fields 変換結果デバッグ
            print(f"🔧 [ENHANCED FIELDS TRANSFORM] Computed values:")
            print(f"   latest_bulletin_id: {latest_bulletin_id}")
            print(f"   bulletins_count: {len(bulletins) if isinstance(bulletins, list) else (1 if bulletins else 0)}")
            print(f"   affected_population: {affected_population}")
            print(f"   risk_assessment: {risk_assessment}")
            print(f"   related_news_count: {related_news_count}")
            print(f"   has_analysis: {len(analysis_results) > 0 if isinstance(analysis_results, list) else bool(analysis_results)}")
            print(f"   has_collected_info: {len(collected_info) > 0 if isinstance(collected_info, list) else bool(collected_info)}")
            print(f"   status: {'active' if is_active else 'monitoring'}")
            
            return {
                'id': firestore_data.get('event_id', firestore_data.get('id', 'unknown')),
                'title': firestore_data.get('summary', '災害情報'),
                'description': firestore_data.get('summary', '詳細情報なし'),
                'type': firestore_data.get('type', 'other'),
                'severity': severity,
                'location': firestore_data.get('location', {'lat': 35.6762, 'lng': 139.6503, 'admin': '不明'}),
                'reported_at': reported_at,
                'confidence': firestore_data.get('confidence', 0.0),
                'source': firestore_data.get('source', ['System']),
                'evidence': firestore_data.get('evidence', []),
                'status': 'active' if is_active else 'monitoring',
                # 追加データ
                'bulletins_count': len(bulletins) if isinstance(bulletins, list) else (1 if bulletins else 0),
                'latest_bulletin_id': latest_bulletin_id,
                'last_bulletin_at': firestore_data.get('last_bulletin_at'),
                'affected_population': affected_population,
                'risk_assessment': risk_assessment,
                'related_news_count': related_news_count,
                'orchestration_started_at': firestore_data.get('orchestration_started_at'),
                # 詳細情報へのアクセス用
                'has_analysis': len(analysis_results) > 0 if isinstance(analysis_results, list) else bool(analysis_results),
                'has_collected_info': len(collected_info) > 0 if isinstance(collected_info, list) else bool(collected_info)
            }
            
        except Exception as e:
            print(f"❌ Data transformation error: {e}")
            return firestore_data

    def handle_disaster_analysis(self, disaster_id: str):
        """災害分析データ endpoint"""
        try:
            if not self.db:
                raise Exception("Firestore client not available")
            
            # analysis_results コレクションから取得
            analysis_ref = self.db.collection('analysis_results').where('event_id', '==', disaster_id)
            analyses = [doc.to_dict() for doc in analysis_ref.stream()]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'event_id': disaster_id,
                'analysis_results': analyses,
                'total': len(analyses),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching analysis data: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disaster_bulletins(self, disaster_id: str):
        """災害公報データ endpoint"""
        try:
            if not self.db:
                raise Exception("Firestore client not available")
            
            # bulletins コレクションから取得
            bulletins_ref = self.db.collection('bulletins').where('event_id', '==', disaster_id)
            bulletins = [doc.to_dict() for doc in bulletins_ref.stream()]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'event_id': disaster_id,
                'bulletins': bulletins,
                'total': len(bulletins),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching bulletins data: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disaster_collected_info(self, disaster_id: str):
        """災害収集情報 endpoint"""
        try:
            if not self.db:
                raise Exception("Firestore client not available")
            
            # collected_info コレクションから取得
            info_ref = self.db.collection('collected_info').where('event_id', '==', disaster_id)
            collected_info = [doc.to_dict() for doc in info_ref.stream()]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'event_id': disaster_id,
                'collected_info': collected_info,
                'total': len(collected_info),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching collected info: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_alerts(self, query_params):
        """Alert API エンドポイント（フロントエンド API仕様準拠）"""
        try:
            print("🚨 Handling alerts request...")
            
            # クエリパラメータ処理
            active_only = query_params.get('active', ['false'])[0].lower() == 'true'
            limit = int(query_params.get('limit', [50])[0])
            
            # 災害データから Alert を生成
            disasters = []
            if self.db:
                # Firestoreから災害データを取得
                firestore_disasters = self.fetch_disasters_from_firestore(query_params)
                disasters.extend(firestore_disasters)
            
            # 公的データソースからも取得
            if self.official_integrator:
                official_disasters = self.fetch_official_disasters(query_params)
                disasters.extend(official_disasters)
            
            # 重複削除
            disasters = self.deduplicate_disasters_api_level(disasters)
            
            # Alert形式に変換
            alerts = []
            for disaster in disasters:
                alert = self._disaster_to_alert(disaster)
                if alert:
                    # active フィルタ適用
                    if not active_only or self._is_alert_active(alert):
                        alerts.append(alert)
            
            # 日時降順でソートしてlimit適用
            alerts.sort(key=lambda x: x.get('startedAt', 0), reverse=True)
            alerts = alerts[:limit]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'alerts': alerts,
                'total': len(alerts),
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'filters': {
                    'active': active_only,
                    'limit': limit
                }
            }
            
            print(f"✅ Alerts response: {len(alerts)} alerts")
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error handling alerts: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_feeds(self, query_params):
        """Feed API エンドポイント（フロントエンド API仕様準拠）"""
        try:
            print("📰 Handling feeds request...")
            
            # クエリパラメータ処理
            incident_id = query_params.get('incidentId', [None])[0]
            limit = int(query_params.get('limit', [50])[0])
            
            # Feed データを生成（災害データベース）
            feeds = []
            
            # 災害データから Feed を生成
            disasters = []
            if self.db:
                firestore_disasters = self.fetch_disasters_from_firestore(query_params)
                disasters.extend(firestore_disasters)
            
            if self.official_integrator:
                official_disasters = self.fetch_official_disasters(query_params)
                disasters.extend(official_disasters)
            
            # Feed形式に変換
            for disaster in disasters:
                feed = self._disaster_to_feed(disaster)
                if feed:
                    # incidentId フィルタ適用
                    if not incident_id or feed.get('incidentId') == incident_id:
                        feeds.append(feed)
            
            # 日時降順でソートしてlimit適用
            feeds.sort(key=lambda x: x.get('publishedAt', 0), reverse=True)
            feeds = feeds[:limit]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'feeds': feeds,
                'total': len(feeds),
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'filters': {
                    'incidentId': incident_id,
                    'limit': limit
                }
            }
            
            print(f"✅ Feeds response: {len(feeds)} feeds")
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error handling feeds: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_incidents(self, query_params):
        """Incident API エンドポイント（フロントエンド API仕様準拠）"""
        try:
            print("🎯 Handling incidents request...")
            
            # クエリパラメータ処理
            since = query_params.get('since', [None])[0]
            limit = int(query_params.get('limit', [50])[0])
            
            # 災害データを取得
            disasters = []
            if self.db:
                firestore_disasters = self.fetch_disasters_from_firestore(query_params)
                disasters.extend(firestore_disasters)
            
            if self.official_integrator:
                official_disasters = self.fetch_official_disasters(query_params)
                disasters.extend(official_disasters)
            
            # 重複削除
            disasters = self.deduplicate_disasters_api_level(disasters)
            
            # 表示閾値でフィルタリング
            filtered_disasters = self.filter_by_display_threshold(disasters)
            
            # since フィルタ適用
            if since:
                try:
                    since_time = int(since)
                    filtered_disasters = [d for d in filtered_disasters 
                                        if d.get('reportedAt', 0) >= since_time]
                except ValueError:
                    print(f"⚠️ Invalid since parameter: {since}")
            
            # limit適用
            filtered_disasters = filtered_disasters[:limit]
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'incidents': filtered_disasters,
                'total': len(filtered_disasters),
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'filters': {
                    'since': since,
                    'limit': limit
                }
            }
            
            print(f"✅ Incidents response: {len(filtered_disasters)} incidents")
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error handling incidents: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def _disaster_to_alert(self, disaster: Dict[Any, Any]) -> Optional[Dict[str, Any]]:
        """災害データを Alert 形式に変換"""
        try:
            severity = disaster.get('severity', 'medium')
            disaster_type = disaster.get('type', disaster.get('hazard', 'other'))
            area = disaster.get('area', disaster.get('location', {}).get('admin', '不明地域'))
            
            # Alert level 判定
            alert_level = {
                'high': 'warning',
                'medium': 'watch', 
                'low': 'advisory'
            }.get(severity, 'info')
            
            # 深刻度が高い場合は emergency に昇格
            if severity == 'high' and disaster_type in ['earthquake', 'tsunami', 'typhoon']:
                alert_level = 'emergency'
            
            # 気象庁形式のタイトル生成
            alert_title = self._generate_weather_alert_title(disaster_type, alert_level, area)
            
            # 適切な要約と説明文を生成
            summary, description = self._generate_alert_content(disaster_type, severity, area, disaster)
            
            # 時刻変換
            reported_at = disaster.get('reportedAt', disaster.get('reported_at'))
            if isinstance(reported_at, str):
                try:
                    dt = datetime.fromisoformat(reported_at.replace('Z', '+00:00'))
                    started_at = int(dt.timestamp() * 1000)
                except:
                    started_at = int(datetime.utcnow().timestamp() * 1000)
            elif isinstance(reported_at, (int, float)):
                started_at = int(reported_at) if reported_at > 1000000000000 else int(reported_at * 1000)
            else:
                started_at = int(datetime.utcnow().timestamp() * 1000)
            
            return {
                'id': f"alert_{disaster.get('id', 'unknown')}",
                'title': alert_title,
                'level': alert_level,
                'hazard': disaster_type,
                'area': area,
                'startedAt': started_at,
                'updatedAt': started_at,
                'summary': summary,
                'description': description
            }
            
        except Exception as e:
            print(f"❌ Error converting disaster to alert: {e}")
            return None

    def _generate_weather_alert_title(self, disaster_type: str, alert_level: str, area: str) -> str:
        """気象庁形式のアラートタイトルを生成"""
        
        # 災害種別から警報名へのマッピング
        disaster_to_alert = {
            'earthquake': '地震情報',
            'tsunami': '津波警報',
            'typhoon': '台風情報',
            'flood': '大雨警報' if alert_level in ['warning', 'emergency'] else '大雨注意報',
            'landslide': '土砂災害警戒情報',
            'volcano': '火山情報',
            'wildfire': '乾燥注意報',
            'other': '気象情報'
        }
        
        # レベルに応じた調整
        if disaster_type == 'flood':
            if alert_level == 'emergency':
                alert_name = '大雨特別警報'
            elif alert_level == 'warning':
                alert_name = '大雨警報'
            elif alert_level == 'watch':
                alert_name = '洪水警報'
            else:
                alert_name = '大雨注意報'
        elif disaster_type == 'earthquake':
            if alert_level in ['warning', 'emergency']:
                alert_name = '緊急地震速報'
            else:
                alert_name = '地震情報'
        else:
            alert_name = disaster_to_alert.get(disaster_type, '気象情報')
        
        # 地域名を整理
        if area and area != '不明地域':
            # 県名、都名、府名、道名を統一
            if not any(suffix in area for suffix in ['県', '都', '府', '道', '地方', '地域']):
                area = f"{area}県"
            return f"{alert_name}（{area}）"
        else:
            return alert_name

    def _generate_alert_content(self, disaster_type: str, severity: str, area: str, disaster: Dict[Any, Any]) -> tuple[str, str]:
        """適切なアラート要約と説明文を生成"""
        
        # 災害種別に応じた基本テンプレート
        templates = {
            'flood': {
                'summary': f"{area}に大雨警報が発令されています。河川の氾濫や低地の浸水に警戒してください。",
                'description': f"前線の影響により、{area}では激しい雨が継続しています。河川の水位上昇や低地の浸水、土砂災害の危険性が高まっています。不要不急の外出は控え、安全な場所で待機してください。気象情報に注意し、避難指示が出た場合は速やかに避難してください。"
            },
            'earthquake': {
                'summary': f"{area}で地震が発生しました。余震に注意してください。",
                'description': f"{area}において地震が発生しました。現在のところ大きな被害の報告はありませんが、余震の可能性があるため引き続き注意が必要です。エレベーターの使用を控え、落下物に注意してください。非常用品の確認をお願いします。"
            },
            'typhoon': {
                'summary': f"強い台風が{area}に接近中です。暴風・大雨に厳重警戒してください。",
                'description': f"強い台風が{area}に接近しています。暴風と大雨が予想されます。外出は控え、窓ガラスから離れた安全な場所で待機してください。飛来物に注意し、停電に備えて懐中電灯や携帯ラジオを準備してください。"
            },
            'landslide': {
                'summary': f"{area}で土砂災害の危険度が高くなっています。",
                'description': f"大雨の影響により、{area}の山間部で土砂災害の危険度が急激に高まっています。がけ崩れや土石流の発生する可能性があります。危険な地域からの避難を検討してください。"
            },
            'tsunami': {
                'summary': f"{area}沿岸に津波警報が発表されています。直ちに高台に避難してください。",
                'description': f"{area}沿岸部に津波警報が発表されました。津波の到達が予想されます。沿岸部や川沿いにいる方は、直ちに高台や避難所に避難してください。津波は繰り返し来襲する可能性があります。"
            }
        }
        
        # デフォルトテンプレート
        default_template = {
            'summary': f"{area}で{disaster_type}に関する警戒が必要です。",
            'description': f"{area}で{disaster_type}による影響が予想されます。最新の気象情報に注意し、安全な行動を心がけてください。"
        }
        
        template = templates.get(disaster_type, default_template)
        
        # 深刻度に応じて内容を調整
        if severity == 'high':
            summary = template['summary'].replace('警戒', '厳重警戒').replace('注意', '警戒')
            description = template['description']
        elif severity == 'low':
            summary = template['summary'].replace('警報', '注意報').replace('警戒', '注意')
            description = template['description'].replace('警戒', '注意').replace('避難', '注意深い行動')
        else:
            summary = template['summary']
            description = template['description']
        
        return summary, description

    def _disaster_to_feed(self, disaster: Dict[Any, Any]) -> Optional[Dict[str, Any]]:
        """災害データを Feed 形式に変換"""
        try:
            # 時刻変換
            reported_at = disaster.get('reportedAt', disaster.get('reported_at'))
            if isinstance(reported_at, str):
                try:
                    dt = datetime.fromisoformat(reported_at.replace('Z', '+00:00'))
                    published_at = int(dt.timestamp() * 1000)
                except:
                    published_at = int(datetime.utcnow().timestamp() * 1000)
            elif isinstance(reported_at, (int, float)):
                published_at = int(reported_at) if reported_at > 1000000000000 else int(reported_at * 1000)
            else:
                published_at = int(datetime.utcnow().timestamp() * 1000)
            
            # ソース判定
            source = disaster.get('source', disaster.get('data_source', 'other'))
            if isinstance(source, list):
                source = source[0] if source else 'other'
            
            # ソースマッピング
            source_mapping = {
                'jma': 'jma',
                'p2p_earthquake': 'other',
                'official': 'jma',
                'firestore': 'other'
            }
            mapped_source = source_mapping.get(source, 'other')
            
            # ラベル生成
            labels = []
            severity = disaster.get('severity', 'medium')
            disaster_type = disaster.get('type', disaster.get('hazard', 'other'))
            
            if severity == 'high':
                labels.append('警報')
            elif severity == 'medium':
                labels.append('注意報')
            
            if disaster_type == 'earthquake':
                labels.append('地震')
            elif disaster_type == 'tsunami':
                labels.append('津波')
            elif disaster_type == 'typhoon':
                labels.append('台風')
            elif disaster_type == 'flood':
                labels.append('大雨')
            elif disaster_type == 'landslide':
                labels.append('土砂')
            
            return {
                'id': f"feed_{disaster.get('id', 'unknown')}",
                'incidentId': disaster.get('id'),
                'source': mapped_source,
                'title': disaster.get('title', '災害情報'),
                'summary': disaster.get('description', disaster.get('summary', '')),
                'url': f"https://example.com/disaster/{disaster.get('id', 'unknown')}",
                'publishedAt': published_at,
                'labels': labels,
                'area': disaster.get('area', disaster.get('location', {}).get('admin', '不明地域')),
                'hazard': disaster_type,
                'isAlertCandidate': severity in ['medium', 'high']
            }
            
        except Exception as e:
            print(f"❌ Error converting disaster to feed: {e}")
            return None

    def _is_alert_active(self, alert: Dict[str, Any]) -> bool:
        """Alert がアクティブかどうか判定"""
        try:
            started_at = alert.get('startedAt', 0)
            current_time = int(datetime.utcnow().timestamp() * 1000)
            
            # 24時間以内のものをアクティブとする
            time_diff = current_time - started_at
            return time_diff < (24 * 60 * 60 * 1000)  # 24時間 = 24*60*60*1000ms
            
        except Exception:
            return False

    def log_message(self, format, *args):
        """ログ出力をカスタマイズ"""
        pass  # アクセスログを無効化

    def handle_faq_by_disaster(self, disaster_id: str):
        """災害特化FAQ取得"""
        try:
            print(f"📄 FAQ Request for disaster: {disaster_id}")
            
            if not self.db:
                self.send_response(500)
                self.end_headers()
                response = {'error': 'Database not available'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # 災害情報を取得（既存の詳細取得メソッドを使用）
            disaster_data = self.fetch_disaster_detail_from_firestore(disaster_id)
            
            if not disaster_data:
                self.send_response(404)
                self.end_headers()
                response = {'error': f'Disaster {disaster_id} not found'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # FAQ データを取得/生成
            faq_ref = self.db.collection('faq_chat_logs').document(disaster_id)
            faq_doc = faq_ref.get()
            
            faqs = []
            if faq_doc.exists:
                faq_data = faq_doc.to_dict()
                stored_faqs = faq_data.get('faqs', [])
                
                for i, stored_faq in enumerate(stored_faqs):
                    faqs.append({
                        'id': f"{disaster_id}_faq_{i}",
                        'disaster_id': disaster_id,
                        'question': stored_faq.get('question', ''),
                        'answer': stored_faq.get('answer', ''),
                        'category': stored_faq.get('category', 'action_guide'),
                        'priority': stored_faq.get('priority', i + 1),
                        'created_at': faq_data.get('created_at', datetime.now().isoformat())
                    })
            else:
                # 基本的なFAQを生成
                faqs = self.generate_basic_faqs(disaster_id, disaster_data)
            
            response = {
                'disaster_id': disaster_id,
                'disaster_title': disaster_data.get('title', ''),
                'hazard_type': disaster_data.get('type', 'other'),
                'area': disaster_data.get('location', {}).get('admin', ''),
                'faqs': faqs,
                'last_updated': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ FAQ Error: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_faq_question(self, disaster_id: str, request_body: str):
        """FAQ質問処理"""
        try:
            print(f"❓ FAQ Question for disaster: {disaster_id}")
            
            if not self.db:
                self.send_response(500)
                self.end_headers()
                response = {'error': 'Database not available'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # リクエストボディをパース
            request_data = json.loads(request_body)
            question = request_data.get('question', '').strip()
            
            if not question:
                self.send_response(400)
                self.end_headers()
                response = {'error': 'Question is required'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # 災害情報を取得（既存の詳細取得メソッドを使用）
            disaster_data = self.fetch_disaster_detail_from_firestore(disaster_id)
            
            if not disaster_data:
                self.send_response(404)
                self.end_headers()
                response = {'error': f'Disaster {disaster_id} not found'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # 質問に対する回答を生成（Vertex AI LLMを使用）
            answer = self.run_async_llm_answer(disaster_data, question)
            
            # ユーザーインタラクションを保存
            self.save_user_interaction(disaster_id, question, answer)
            
            model_name = 'gemini-2.5-flash' if VERTEX_AI_AVAILABLE else 'basic-rules'
            response = {
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().isoformat(),
                'model_used': model_name
            }
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ FAQ Question Error: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_active_faqs(self):
        """アクティブ災害のFAQ一覧取得"""
        try:
            print("📄 Active FAQs Request")
            
            if not self.db:
                self.send_response(500)
                self.end_headers()
                response = {'error': 'Database not available'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # アクティブな災害を取得（incidentsコレクションから）
            disasters_ref = self.db.collection('incidents')
            query = disasters_ref.where('is_active', '==', True).limit(10)
            disasters = list(query.stream())
            
            active_faqs = []
            for disaster_doc in disasters:
                disaster_data = disaster_doc.to_dict()
                disaster_id = disaster_doc.id
                
                # FAQを取得
                faq_ref = self.db.collection('faq_chat_logs').document(disaster_id)
                faq_doc = faq_ref.get()
                
                faqs = []
                if faq_doc.exists:
                    faq_data = faq_doc.to_dict()
                    stored_faqs = faq_data.get('faqs', [])
                    
                    for i, stored_faq in enumerate(stored_faqs):
                        faqs.append({
                            'id': f"{disaster_id}_faq_{i}",
                            'disaster_id': disaster_id,
                            'question': stored_faq.get('question', ''),
                            'answer': stored_faq.get('answer', ''),
                            'category': stored_faq.get('category', 'action_guide'),
                            'priority': stored_faq.get('priority', i + 1),
                            'created_at': faq_data.get('created_at', datetime.now().isoformat())
                        })
                else:
                    # 基本的なFAQを生成
                    faqs = self.generate_basic_faqs(disaster_id, disaster_data)
                
                if faqs:
                    active_faqs.append({
                        'disaster_id': disaster_id,
                        'disaster_title': disaster_data.get('title', ''),
                        'hazard_type': disaster_data.get('type', 'other'),
                        'area': disaster_data.get('location', {}).get('admin', ''),
                        'faqs': faqs,
                        'last_updated': datetime.now().isoformat()
                    })
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(active_faqs, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Active FAQs Error: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def generate_basic_faqs(self, disaster_id: str, disaster_data: dict) -> list:
        """基本的なFAQを生成"""
        disaster_type = disaster_data.get('type', 'other')
        location = disaster_data.get('location', {}).get('admin', '該当地域')
        
        faq_templates = {
            'earthquake': [
                {
                    'question': f'{location}で地震が発生した際の基本的な行動は？',
                    'answer': '地震発生時は、まず身の安全を確保してください。机の下に潜り頭を守る、火の元を確認して消火する、出口を確保するなどの基本行動を取ってください。揺れが収まったら、余震に注意しながら避難の準備をしてください。',
                    'category': 'action_guide'
                },
                {
                    'question': '避難のタイミングはいつですか？',
                    'answer': '地震の場合、建物に亀裂や損傷が見られる場合は速やかに避難してください。津波警報が発表された場合は即座に高台へ避難してください。自治体から避難指示が出た場合も迅速に従ってください。',
                    'category': 'evacuation'
                },
                {
                    'question': '余震への備えはどうすれば良いですか？',
                    'answer': '大きな地震の後は余震が続く可能性があります。不安定な物の近くを避け、常に安全な場所を意識してください。非常用品を手の届く場所に準備し、家族との連絡方法を確認してください。',
                    'category': 'safety_tips'
                }
            ],
            'flood': [
                {
                    'question': f'{location}で洪水が発生した際の基本的な対応は？',
                    'answer': '洪水時は、まず高い場所に避難してください。水深が膝上になったら歩行は危険です。車での移動は避け、電気設備には近づかないでください。最新の気象情報と避難情報を確認し続けてください。',
                    'category': 'action_guide'
                },
                {
                    'question': '洪水時の避難タイミングは？',
                    'answer': '大雨警報が発表された時点で避難準備を始めてください。避難勧告が出る前の明るい時間帯に避難することが重要です。水位が膝下に達する前に避難を完了してください。',
                    'category': 'evacuation'
                },
                {
                    'question': '浸水した場所での注意点は？',
                    'answer': '浸水した電気設備には絶対に触れないでください。汚染された水でケガをしないよう注意し、長靴よりも運動靴を履いてください。マンホールの蓋が外れている可能性があるため、棒で足元を確認しながら移動してください。',
                    'category': 'safety_tips'
                }
            ]
        }
        
        templates = faq_templates.get(disaster_type, [
            {
                'question': f'{location}で災害が発生した際の基本的な対応は？',
                'answer': '災害発生時は、まず身の安全を確保し、最新の情報を収集してください。自治体の指示に従い、無理な行動は避けて安全な場所で待機してください。',
                'category': 'action_guide'
            }
        ])
        
        faqs = []
        for i, template in enumerate(templates):
            faqs.append({
                'id': f"{disaster_id}_basic_{i}",
                'disaster_id': disaster_id,
                'question': template['question'],
                'answer': template['answer'],
                'category': template['category'],
                'priority': i + 1,
                'created_at': datetime.now().isoformat()
            })
        
        return faqs

    def generate_basic_answer(self, disaster_data: dict, question: str) -> str:
        """基本的な回答を生成"""
        disaster_type = disaster_data.get('type', 'other')
        location = disaster_data.get('location', {}).get('admin', '該当地域')
        severity = disaster_data.get('severity', 'medium')
        
        question_lower = question.lower()
        
        # 質問のキーワードに基づいて回答を生成
        if '避難' in question or '逃げ' in question:
            if disaster_type == 'earthquake':
                return f'{location}では地震により避難が必要な場合があります。建物の安全性を確認し、必要に応じて指定避難所に向かってください。余震に注意しながら行動してください。'
            elif disaster_type == 'flood':
                return f'{location}では洪水により避難が必要です。高台や頑丈な建物の上階に避難してください。水深が深くなる前に避難を完了してください。'
            else:
                return f'{location}で災害が発生しています。自治体の避難指示に従い、安全な場所に避難してください。'
        
        elif '安全' in question or '注意' in question:
            return f'{location}で発生中の{self.get_disaster_type_japanese(disaster_type)}について、最新の気象情報と自治体からの情報を常に確認し、無理な外出は避けて安全な場所で待機してください。'
        
        elif '準備' in question or '用意' in question:
            return f'{disaster_type}に備えて、水・食料・懐中電灯・ラジオ・救急用品などの非常用品を準備してください。避難経路と避難所も事前に確認しておきましょう。'
        
        else:
            # 一般的な回答
            severity_text = '高い' if severity == 'high' else '中程度の' if severity == 'medium' else '比較的軽微な'
            return f'{location}で{severity_text}深刻度の{self.get_disaster_type_japanese(disaster_type)}が発生しています。最新の気象情報と避難情報を確認し、自治体の指示に従って適切な行動を取ってください。安全確保を最優先に行動しましょう。'

    def get_disaster_type_japanese(self, disaster_type: str) -> str:
        """災害種別を日本語に変換"""
        type_mapping = {
            'earthquake': '地震',
            'typhoon': '台風',
            'flood': '洪水',
            'landslide': '土砂災害',
            'tsunami': '津波',
            'wildfire': '山火事',
            'other': '災害'
        }
        return type_mapping.get(disaster_type, '災害')

    def save_user_interaction(self, disaster_id: str, question: str, answer: str):
        """ユーザーインタラクションをFirestoreに保存"""
        try:
            if not self.db:
                return
                
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
            faq_ref.set({
                'faqs': faq_doc.to_dict().get('faqs', []) if faq_doc.exists else [],
                'user_interactions': interactions,
                'created_at': faq_doc.to_dict().get('created_at', datetime.now().isoformat()) if faq_doc.exists else datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Failed to save user interaction: {e}")

    def run_async_llm_answer(self, disaster_data: dict, question: str) -> str:
        """非同期LLM回答生成を同期的に実行"""
        try:
            if not VERTEX_AI_AVAILABLE:
                print("⚠️ Vertex AI not available, using basic answer")
                return self.generate_basic_answer(disaster_data, question)
            
            # 非同期関数を同期的に実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.generate_llm_answer(disaster_data, question))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ LLM Answer generation failed: {e}")
            # フォールバックとして基本回答を使用
            return self.generate_basic_answer(disaster_data, question)

    def generate_llm_answer(self, disaster_data: dict, question: str) -> str:
        """Vertex AI LLMを使用して回答を生成"""
        try:
            print("🤖 Generating LLM answer using Vertex AI...")
            
            # 災害コンテキストを構築
            disaster_type = disaster_data.get('type', 'other')
            location = disaster_data.get('location', {}).get('admin', '該当地域')
            severity = disaster_data.get('severity', 'medium')
            title = disaster_data.get('title', '')
            description = disaster_data.get('description', '')
            
            # FAQコンテキストを取得
            faqs = self.generate_basic_faqs(disaster_data.get('id', ''), disaster_data)
            faq_context = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in faqs])
            
            # LLMプロンプトを構築
            prompt = f"""
あなたは災害対応の専門家として、被災者からの質問に親切で詳細な回答を提供してください。

現在の災害状況:
- 場所: {location}
- 災害種別: {self.get_disaster_type_japanese(disaster_type)}
- 深刻度: {severity}
- タイトル: {title}
- 詳細: {description}

参考FAQ:
{faq_context}

ユーザーの質問: {question}

回答する際の注意点:
- 具体的で実用的な情報を提供してください
- 安全を最優先に考慮してください
- 地域特有の情報があれば含めてください
- 緊急時の連絡先(119番、110番)を必要に応じて案内してください
- 自治体や気象庁の最新情報を確認するよう促してください

回答:
"""

            # Vertex AI LLMで回答生成（同期版クライアント使用）
            if not VERTEX_AI_AVAILABLE or not get_sync_vertex_ai_client:
                return self.generate_basic_answer(disaster_data, question)
            
            try:
                print(f"🔧 DEBUG: GOOGLE_CLOUD_PROJECT = {os.getenv('GOOGLE_CLOUD_PROJECT')}")
                print(f"🔧 DEBUG: USE_MOCK_LLM = {os.getenv('USE_MOCK_LLM')}")
                
                vertex_client = get_sync_vertex_ai_client()
                print(f"🔧 DEBUG: vertex_client.project_id = {vertex_client.project_id}")
                print(f"🔧 DEBUG: vertex_client.is_local_mode = {vertex_client.is_local_mode}")
                
                answer = vertex_client.answer_with_faq(
                    [{'question': faq['question'], 'answer': faq['answer']} for faq in faqs],
                    question  # ユーザーの質問をそのまま渡す
                )
            except Exception as e:
                print(f"❌ Sync Vertex AI client failed: {e}")
                import traceback
                print(f"❌ Full traceback: {traceback.format_exc()}")
                return self.generate_basic_answer(disaster_data, question)
            
            if answer and len(answer.strip()) > 10:
                print("✅ LLM answer generated successfully")
                return answer.strip()
            else:
                print("⚠️ LLM answer too short, using fallback")
                return self.generate_basic_answer(disaster_data, question)
                
        except Exception as e:
            print(f"❌ Vertex AI LLM generation failed: {e}")
            # フォールバックとして基本回答を使用
            return self.generate_basic_answer(disaster_data, question)

    async def generate_detailed_answer(self, disaster_data: dict, question: str, faqs: list) -> str:
        """ローカル環境向けの詳細回答生成"""
        try:
            disaster_type = disaster_data.get('type', 'other')
            location = disaster_data.get('location', {}).get('admin', '該当地域')
            severity = disaster_data.get('severity', 'medium')
            title = disaster_data.get('title', '')
            
            # 質問を分析してカテゴリー分け
            question_lower = question.lower()
            
            if '金沢' in question and '避難' in question and ('地域' in question or '場所' in question):
                # 金沢の具体的な避難場所についての質問
                return f"""金沢市にお住まいの方の避難についてお答えします。

**緊急避難場所：**
• 金沢市内の指定避難所：小中学校、公民館、体育館など
• 高台地域：東山、卯辰山、医王山方面
• 頑丈な建物：市役所、県庁、大型商業施設の上階

**洪水時の具体的な避難方針：**
1. **浅野川・犀川周辺の方**: 川から離れた高台へ速やかに移動
2. **市街地中心部の方**: 最寄りの3階建て以上の建物へ垂直避難
3. **郊外の方**: 指定避難所または高台の安全な場所へ

**避難のタイミング：**
• 避難準備情報発表時：避難準備開始
• 避難勧告発表時：速やかに避難開始
• 水位上昇を確認した時：即座に避難

金沢市の防災情報は市公式サイトやハザードマップで最新情報をご確認ください。緊急時は119番へお電話ください。"""

            elif '避難' in question:
                # 一般的な避難に関する質問
                return f"""{location}での避難について詳しくお答えします。

**基本的な避難方針：**
• 自治体の避難指示に従って行動
• 早めの避難を心がける（明るい時間帯が安全）
• 避難所への経路を事前に確認

**{self.get_disaster_type_japanese(disaster_type)}特有の注意点：**
{self._get_specific_evacuation_advice(disaster_type)}

**避難時の持ち物：**
• 非常用品（水、食料、薬、着替え）
• 重要書類（身分証明書、保険証等）
• 現金、携帯電話・充電器

**連絡先：**
• 緊急時：119番（消防）・110番（警察）
• 自治体防災情報を定期的に確認

安全を最優先に、無理をせず早めの行動を心がけてください。"""

            elif '安全' in question or '注意' in question:
                return f"""{location}での安全確保について詳しくお答えします。

**現在の状況への対応：**
• 深刻度：{severity}レベルの{self.get_disaster_type_japanese(disaster_type)}が発生中
• 継続的な情報収集が重要

**安全確保の基本：**
• 最新の気象情報・避難情報を定期的に確認
• 無理な外出は避け、安全な場所で待機
• 家族・近隣との連絡体制を確保

**{self.get_disaster_type_japanese(disaster_type)}特有の安全対策：**
{self._get_specific_safety_advice(disaster_type)}

**緊急時の判断基準：**
• 身の危険を感じた時は躊躇せず避難
• 自治体からの指示は最優先で従う
• 「まだ大丈夫」ではなく「早めの行動」を

最新情報は気象庁・自治体の公式情報をご確認ください。"""

            else:
                # その他の一般的な質問
                return f"""{location}の{self.get_disaster_type_japanese(disaster_type)}について、ご質問にお答えします。

**現在の状況：**
• 場所：{location}
• 災害種別：{self.get_disaster_type_japanese(disaster_type)}
• 深刻度：{severity}レベル

**基本的な対応：**
• 最新の気象情報と避難情報を継続的に確認
• 自治体からの指示に従った適切な行動
• 家族・近隣との安全確認と情報共有
• 無理な外出は避け、安全確保を最優先

**追加のアドバイス：**
{self._get_general_advice(disaster_type)}

**重要な連絡先：**
• 緊急時：119番（消防）・110番（警察）
• 気象庁、自治体の最新情報を確認

何か具体的なご不明点がございましたら、遠慮なくお尋ねください。安全を最優先に行動してください。"""

        except Exception as e:
            print(f"❌ Detailed answer generation failed: {e}")
            return self.generate_basic_answer(disaster_data, question)

    def _get_specific_evacuation_advice(self, disaster_type: str) -> str:
        """災害種別ごとの避難アドバイス"""
        advice_map = {
            'flood': '• 高台や3階以上の建物への避難\n• 車での移動は避ける（アンダーパス等危険）\n• 水深膝上では歩行禁止',
            'earthquake': '• 建物の安全性確認後に避難\n• 余震に注意しながら行動\n• 津波警報時は高台へ即座に避難',
            'typhoon': '• 暴風前に避難完了\n• 頑丈な建物内で窓から離れた場所\n• 外出は絶対に避ける'
        }
        return advice_map.get(disaster_type, '• 自治体の指示に従って安全な場所へ避難')

    def _get_specific_safety_advice(self, disaster_type: str) -> str:
        """災害種別ごとの安全アドバイス"""
        advice_map = {
            'flood': '• 浸水した電気設備には触れない\n• 汚染水での怪我に注意\n• 長靴より運動靴を着用',
            'earthquake': '• 余震への継続的な警戒\n• 火の元確認・ガス漏れ点検\n• 不安定な物から離れる',
            'typhoon': '• 飛散物からの身体保護\n• 停電・断水への備え\n• 河川・海岸への接近禁止'
        }
        return advice_map.get(disaster_type, '• 状況に応じた安全確保\n• 無理な行動は避ける')

    def _get_general_advice(self, disaster_type: str) -> str:
        """災害種別ごとの一般アドバイス"""
        advice_map = {
            'flood': '洪水は予想以上に急激に進行する場合があります。水位の変化に注意し、早めの判断を心がけてください。',
            'earthquake': '余震は長期間続く可能性があります。建物の安全性を定期的に確認し、備蓄品を確保してください。',
            'typhoon': '台風は進路予測が困難な場合があります。最新の気象情報を頻繁に確認し、計画的な行動を取ってください。'
        }
        return advice_map.get(disaster_type, '災害の状況は刻々と変化します。常に最新情報を確認し、柔軟な対応を心がけてください。')

def start_firestore_api_server():
    """Firestore連携APIサーバーを起動"""
    port = 8082
    
    print(f"""
🚨 災害情報システム - Firestore API Server 起動中...
====================================
Port: {port}
Firestore: {'Emulator' if os.getenv('FIRESTORE_EMULATOR_HOST') else 'Production'}
Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'test-disaster-response')}
====================================
    """)
    
    server = HTTPServer(('0.0.0.0', port), FirestoreAPIHandler)
    
    print(f"✅ Server started on http://localhost:{port}")
    print("🔗 Test endpoints:")
    print(f"   • http://localhost:{port}/")
    print(f"   • http://localhost:{port}/api/public/disasters")
    print(f"   • http://localhost:{port}/api/health")
    print("\n📋 Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopping...")
        server.shutdown()

if __name__ == "__main__":
    # 環境変数を設定ファイルから読み込み
    env_files = [
        "/workspace/disaster-response-system/.env",  # Linux/WSL
        ".env",  # 相対パス
        "../.env"  # 一つ上のディレクトリ
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📁 Loading environment from {env_file}")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # クォート削除
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
                        print(f"🔧 Set {key}={value}")
            break
    else:
        print("⚠️  No .env file found")
    
    print(f"🎯 Using project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}")
    start_firestore_api_server()