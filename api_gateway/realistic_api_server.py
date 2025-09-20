#!/usr/bin/env python3
"""
災害情報システム - リアルなデータ構造APIサーバー
実際のFirestore schema基づく災害データを提供
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class RealisticAPIHandler(BaseHTTPRequestHandler):
    """実データ構造を持つAPI ハンドラー"""
    
    def __init__(self, *args, **kwargs):
        # 実際のFirestore構造に基づく災害データを生成
        self.disaster_data = self.generate_realistic_disaster_data()
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
            
            # CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            
            if path == '/':
                self.handle_root()
            elif path == '/api/public/disasters':
                self.handle_disasters(query_params)
            elif path.startswith('/api/public/disasters/'):
                disaster_id = path.split('/')[-1]
                self.handle_disaster_detail(disaster_id)
            elif path == '/api/public/disasters/map-data':
                self.handle_map_data(query_params)
            elif path == '/api/health':
                self.handle_health()
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
        self.end_headers()
        
        response = {
            'service': '災害情報システム - リアルデータ構造 API',
            'version': '2.0.0',
            'data_source': 'realistic_mock_based_on_firestore_schema',
            'total_disasters': len(self.disaster_data),
            'last_updated': datetime.utcnow().isoformat(),
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
            # クエリパラメータによるフィルタリング
            filtered_disasters = self.filter_disasters(self.disaster_data, query_params)
            
            self.send_response(200)
            self.end_headers()
            
            response = {
                'disasters': filtered_disasters,
                'total': len(filtered_disasters),
                'available_total': len(self.disaster_data),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'realistic_mock_data'
            }
            
            print(f"✅ Disasters returned: {len(filtered_disasters)}/{len(self.disaster_data)} items")
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error fetching disasters: {e}")
            self.send_response(500)
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_disaster_detail(self, disaster_id: str):
        """災害詳細 endpoint"""
        try:
            disaster = next((d for d in self.disaster_data if d['id'] == disaster_id), None)
            
            if disaster:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(disaster, ensure_ascii=False, default=str).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                response = {'error': f'Disaster with ID {disaster_id} not found'}
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
            disasters = self.filter_disasters(self.disaster_data, query_params)
            
            # マップ用に座標データのみ抽出
            map_data = []
            for disaster in disasters:
                map_data.append({
                    'id': disaster['id'],
                    'title': disaster['title'],
                    'lat': disaster['location']['lat'],
                    'lng': disaster['location']['lng'],
                    'severity': disaster['severity'],
                    'type': disaster['type']
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
        self.send_response(200)
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'data_source': 'realistic_mock',
            'total_disasters': len(self.disaster_data),
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': '✅ Running'
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def filter_disasters(self, disasters: List[Dict], query_params: Dict) -> List[Dict]:
        """クエリパラメータに基づいてフィルタリング"""
        filtered = disasters.copy()
        
        # Severity フィルタ
        if 'severity' in query_params:
            severity = query_params['severity'][0]
            filtered = [d for d in filtered if d['severity'] == severity]
        
        # Type フィルタ
        if 'type' in query_params:
            disaster_type = query_params['type'][0]
            filtered = [d for d in filtered if d['type'] == disaster_type]
        
        # Prefecture フィルタ
        if 'prefecture' in query_params:
            prefecture = query_params['prefecture'][0]
            filtered = [d for d in filtered if prefecture in d['location']['admin']]
        
        # Limit
        limit = int(query_params.get('limit', [20])[0])
        return filtered[:limit]

    def generate_realistic_disaster_data(self) -> List[Dict[Any, Any]]:
        """実際のFirestore構造に基づくリアルなデータ生成"""
        
        disaster_types = [
            {'type': 'earthquake', 'icon': '🌍', 'titles': ['地震発生', '震度{}の地震観測', '地震警報発令']},
            {'type': 'flood', 'icon': '🌊', 'titles': ['河川氾濫', '冠水被害', '洪水警報発令', '大雨による浸水']},
            {'type': 'typhoon', 'icon': '🌀', 'titles': ['台風接近中', '台風{}号上陸', '強風警報発令']},
            {'type': 'landslide', 'icon': '⛰️', 'titles': ['土砂崩れ発生', '地すべり警戒', '斜面崩壊']},
            {'type': 'wildfire', 'icon': '🔥', 'titles': ['山林火災', '森林火災拡大', '火災警報']},
            {'type': 'snow', 'icon': '❄️', 'titles': ['大雪警報', '雪崩警戒', '豪雪被害']},
            {'type': 'other', 'icon': '⚠️', 'titles': ['異常気象', '緊急事態', '被害報告']}
        ]
        
        japanese_locations = [
            {'lat': 35.6762, 'lng': 139.6503, 'admin': '東京都千代田区'},
            {'lat': 35.6895, 'lng': 139.6917, 'admin': '東京都新宿区'},
            {'lat': 35.6586, 'lng': 139.7454, 'admin': '東京都江東区'},
            {'lat': 34.6937, 'lng': 135.5023, 'admin': '大阪府大阪市'},
            {'lat': 35.0116, 'lng': 135.7681, 'admin': '京都府京都市'},
            {'lat': 35.1815, 'lng': 136.9066, 'admin': '愛知県名古屋市'},
            {'lat': 33.5904, 'lng': 130.4017, 'admin': '福岡県福岡市'},
            {'lat': 43.0642, 'lng': 141.3469, 'admin': '北海道札幌市'},
            {'lat': 38.2682, 'lng': 140.8694, 'admin': '宮城県仙台市'},
            {'lat': 34.3853, 'lng': 132.4553, 'admin': '広島県広島市'},
            {'lat': 26.2124, 'lng': 127.6792, 'admin': '沖縄県那覇市'},
            {'lat': 36.5654, 'lng': 136.6562, 'admin': '石川県金沢市'},
            {'lat': 35.4437, 'lng': 133.0506, 'admin': '島根県松江市'},
            {'lat': 39.7186, 'lng': 141.1526, 'admin': '岩手県盛岡市'},
            {'lat': 32.7504, 'lng': 129.8776, 'admin': '長崎県長崎市'}
        ]
        
        evidence_sources = [
            'NHK NEWS WEB', 'Yahoo!ニュース', 'Twitter', 'Instagram',
            '気象庁', '消防庁', '地方自治体', 'ライブカメラ',
            '住民報告', 'センサーデータ', 'ドローン映像', '衛星画像'
        ]
        
        disasters = []
        
        # リアルなデータを15件生成
        for i in range(15):
            disaster_type = random.choice(disaster_types)
            location = random.choice(japanese_locations)
            severity_num = random.uniform(0.1, 1.0)
            
            # 深刻度を文字列に変換
            if severity_num >= 0.7:
                severity = 'high'
            elif severity_num >= 0.4:  
                severity = 'medium'
            else:
                severity = 'low'
            
            # タイトル生成
            title_template = random.choice(disaster_type['titles'])
            if '{}' in title_template:
                if disaster_type['type'] == 'earthquake':
                    title = title_template.format(random.randint(3, 6))
                elif disaster_type['type'] == 'typhoon':
                    title = title_template.format(random.randint(15, 25))
                else:
                    title = title_template
            else:
                title = title_template
            
            # 報告時刻（過去24時間以内）
            reported_at = datetime.utcnow() - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Evidence生成
            num_evidence = random.randint(1, 4)
            evidence = []
            for j in range(num_evidence):
                evidence.append({
                    'url': f'https://example.com/evidence/{i}_{j}',
                    'title': f'{random.choice(evidence_sources)}からの報告',
                    'source': random.choice(evidence_sources),
                    'timestamp': reported_at.isoformat(),
                    'hash': f'hash_{i}_{j}'
                })
            
            disaster = {
                'id': f'disaster_{2025}_{i+1:03d}',
                'event_id': f'EVT_{2025}{i+1:04d}',
                'title': f'{disaster_type["icon"]} {title}',
                'description': f'{location["admin"]}で{title}が発生。詳細情報を収集中。',
                'type': disaster_type['type'],
                'severity': severity,
                'location': location,
                'reported_at': reported_at.isoformat(),
                'detected_at': reported_at.isoformat(),
                'confidence': round(random.uniform(0.6, 0.95), 2),
                'source': random.sample(evidence_sources, random.randint(1, 3)),
                'evidence': evidence,
                'summary': f'{location["admin"]}において{disaster_type["type"]}による被害を確認。対応状況を監視中。',
                # Firestore追加フィールド
                'agent_analysis': {
                    'risk_level': severity,
                    'affected_population': random.randint(100, 50000),
                    'response_priority': random.choice(['urgent', 'high', 'medium', 'low']),
                    'estimated_damage': random.choice(['軽微', '中程度', '大規模'])
                },
                'status': random.choice(['active', 'monitoring', 'resolved']),
                'tags': random.sample(['緊急', '避難', '警戒', '注意', '情報収集'], random.randint(1, 3))
            }
            
            disasters.append(disaster)
        
        # 報告時刻順にソート（新しい順）
        disasters.sort(key=lambda x: x['reported_at'], reverse=True)
        
        return disasters

    def log_message(self, format, *args):
        """ログ出力をカスタマイズ"""
        pass  # アクセスログを無効化

def start_realistic_api_server():
    """リアルなデータ構造APIサーバーを起動"""
    port = 8081
    
    print(f"""
🚨 災害情報システム - リアルなデータ構造 API Server 起動中...
====================================
Port: {port}
Data Source: Realistic Mock (Based on Firestore Schema)
Total Disasters: 15件
Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
====================================
    """)
    
    server = HTTPServer(('0.0.0.0', port), RealisticAPIHandler)
    
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
    start_realistic_api_server()