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
                'GET /api/health - ヘルスチェック'
            ]
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disasters(self, query_params):
        """災害一覧 endpoint"""
        try:
            disasters = self.fetch_disasters_from_firestore(query_params)
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {
                'disasters': disasters,
                'total': len(disasters),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'firestore' if self.db else 'fallback'
            }
            
            print(f"✅ Disasters fetched: {len(disasters)} items")
            print(f"📤 Response structure: {{'disasters': {len(disasters)} items, 'total': {len(disasters)}, 'source': '{response['source']}'}}")
            if disasters:
                print(f"📋 First disaster keys: {list(disasters[0].keys())}")
                print(f"📋 First disaster title: {disasters[0].get('title', 'N/A')}")
            
            response_json = json.dumps(response, ensure_ascii=False, default=str)
            print(f"📤 Response JSON length: {len(response_json)} characters")
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching disasters: {e}")
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
            # 深刻度を文字列に変換
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

    def log_message(self, format, *args):
        """ログ出力をカスタマイズ"""
        pass  # アクセスログを無効化

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