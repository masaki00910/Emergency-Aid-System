#!/usr/bin/env python3
"""
災害情報システム - 拡張モックAPIサーバー
実際のFirestore構造に基づくリアルなデータを提供
"""
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import uuid
import random

# リアルなFirestore構造に基づくモックデータ
def generate_realistic_disasters():
    """実際のFirestore構造に基づくリアルな災害データを生成"""
    
    disaster_types = [
        {'type': 'earthquake', 'icon': '🌍', 'titles': ['地震発生（震度{}）', '地震警報発令', '緊急地震速報']},
        {'type': 'flood', 'icon': '🌊', 'titles': ['河川氾濫警戒', '冠水被害発生', '大雨による浸水', '洪水警報']},
        {'type': 'typhoon', 'icon': '🌀', 'titles': ['台風{}号接近', '暴風雨警報', '強風による被害']},
        {'type': 'landslide', 'icon': '⛰️', 'titles': ['土砂崩れ発生', '地すべり警戒', '斜面崩壊の危険']},
        {'type': 'wildfire', 'icon': '🔥', 'titles': ['山林火災拡大', '森林火災警戒', '火災による避難']},
        {'type': 'snow', 'icon': '❄️', 'titles': ['大雪警報発令', '雪崩注意', '豪雪による交通障害']},
        {'type': 'other', 'icon': '⚠️', 'titles': ['異常気象発生', '緊急事態発生', '災害警戒情報']}
    ]
    
    japanese_locations = [
        {'lat': 35.6762, 'lng': 139.6503, 'admin': '東京都千代田区'},
        {'lat': 35.6895, 'lng': 139.6917, 'admin': '東京都新宿区'},
        {'lat': 35.6586, 'lng': 139.7454, 'admin': '東京都江東区'},
        {'lat': 34.6937, 'lng': 135.5023, 'admin': '大阪府大阪市北区'},
        {'lat': 35.0116, 'lng': 135.7681, 'admin': '京都府京都市中京区'},
        {'lat': 35.1815, 'lng': 136.9066, 'admin': '愛知県名古屋市中区'},
        {'lat': 33.5904, 'lng': 130.4017, 'admin': '福岡県福岡市博多区'},
        {'lat': 43.0642, 'lng': 141.3469, 'admin': '北海道札幌市中央区'},
        {'lat': 38.2682, 'lng': 140.8694, 'admin': '宮城県仙台市青葉区'},
        {'lat': 34.3853, 'lng': 132.4553, 'admin': '広島県広島市中区'},
        {'lat': 26.2124, 'lng': 127.6792, 'admin': '沖縄県那覇市'},
        {'lat': 36.5654, 'lng': 136.6562, 'admin': '石川県金沢市'},
        {'lat': 35.4437, 'lng': 133.0506, 'admin': '島根県松江市'},
        {'lat': 39.7186, 'lng': 141.1526, 'admin': '岩手県盛岡市'},
        {'lat': 32.7504, 'lng': 129.8776, 'admin': '長崎県長崎市'}
    ]
    
    evidence_sources = [
        'NHK NEWS WEB', 'Yahoo!ニュース', 'Twitter公式情報', 'Instagram報告',
        '気象庁', '消防庁', '地方自治体HP', '防災ライブカメラ',
        '住民からの報告', 'センサーデータ', 'ドローン映像', '衛星画像解析'
    ]
    
    disasters = []
    
    # リアルな災害データを12件生成
    for i in range(12):
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
            'id': f'disaster_2025_{i+1:03d}',
            'event_id': f'EVT_2025{i+1:04d}',
            'title': f'{disaster_type["icon"]} {title}',
            'description': f'{location["admin"]}で{title}が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。',
            'type': disaster_type['type'],
            'severity': severity,
            'location': location,
            'reported_at': reported_at.isoformat(),
            'detected_at': reported_at.isoformat(),
            'confidence': round(random.uniform(0.6, 0.95), 2),
            'source': random.sample(evidence_sources, random.randint(1, 3)),
            'evidence': evidence,
            'summary': f'{location["admin"]}において{disaster_type["type"]}による被害が確認されています。関係機関が対応中。',
            # Firestore実際のフィールド
            'agent_analysis': {
                'risk_level': severity,
                'affected_population': random.randint(500, 50000),
                'response_priority': random.choice(['urgent', 'high', 'medium', 'low']),
                'estimated_damage': random.choice(['軽微', '中程度', '甚大', '不明'])
            },
            'status': random.choice(['active', 'monitoring', 'resolved', 'investigating']),
            'tags': random.sample(['緊急対応', '避難指示', '警戒情報', '被害調査', '復旧作業'], random.randint(1, 3)),
            # Frontend用フィールド
            'is_active': random.choice([True, False]),
            'last_updated': (datetime.utcnow() - timedelta(minutes=random.randint(5, 120))).isoformat()
        }
        
        disasters.append(disaster)
    
    # 報告時刻順にソート（新しい順）
    disasters.sort(key=lambda x: x['reported_at'], reverse=True)
    
    return disasters

REALISTIC_DISASTERS = generate_realistic_disasters()

class EnhancedMockAPIHandler(http.server.SimpleHTTPRequestHandler):
    """拡張モックAPI ハンドラー"""
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        if path == '/':
            self.handle_root()
        elif path == '/api/public/disasters':
            self.handle_disasters(query_params)
        elif path.startswith('/api/public/disasters/'):
            disaster_id = path.split('/')[-1]
            self.handle_disaster_detail(disaster_id)
        elif path == '/api/health':
            self.handle_health()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': 'Endpoint not found', 'path': path}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """CORS preflight handling"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_root(self):
        """ルート endpoint - サーバー情報"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            'service': '災害情報システム - 拡張モックAPI',
            'version': '2.0.0',
            'data_source': 'enhanced_mock_with_firestore_structure',
            'total_disasters': len(REALISTIC_DISASTERS),
            'last_updated': datetime.utcnow().isoformat(),
            'features': [
                'Firestore構造準拠',
                'リアルタイムデータ更新',
                'エビデンス情報',
                'エージェント分析結果',
                'タグ・ステータス管理'
            ],
            'endpoints': [
                'GET / - サーバー情報',
                'GET /api/public/disasters - 災害一覧取得',
                'GET /api/public/disasters/{id} - 災害詳細取得',
                'GET /api/health - ヘルスチェック'
            ]
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
    
    def handle_disasters(self, query_params):
        """災害一覧 endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # フィルタリング処理（実装簡略化）
        filtered_disasters = REALISTIC_DISASTERS.copy()
        
        # Severity フィルタ
        if 'severity' in query_params:
            severity = query_params['severity'][0]
            filtered_disasters = [d for d in filtered_disasters if d['severity'] == severity]
        
        # Type フィルタ
        if 'type' in query_params:
            disaster_type = query_params['type'][0]
            filtered_disasters = [d for d in filtered_disasters if d['type'] == disaster_type]
        
        # Limit
        limit = int(query_params.get('limit', [20])[0])
        filtered_disasters = filtered_disasters[:limit]
        
        response = {
            'disasters': filtered_disasters,
            'total': len(filtered_disasters),
            'available_total': len(REALISTIC_DISASTERS),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'enhanced_mock_api',
            'data_structure': 'firestore_compatible'
        }
        
        print(f"🌐 API Request: /api/public/disasters - Returned {len(filtered_disasters)} disasters")
        self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
    
    def handle_disaster_detail(self, disaster_id):
        """災害詳細 endpoint"""
        disaster = next((d for d in REALISTIC_DISASTERS if d['id'] == disaster_id), None)
        
        if disaster:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(disaster, ensure_ascii=False, default=str).encode('utf-8'))
            print(f"🌐 API Request: /api/public/disasters/{disaster_id} - Found")
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'error': f'Disaster with ID {disaster_id} not found'}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print(f"🌐 API Request: /api/public/disasters/{disaster_id} - Not found")
    
    def handle_health(self):
        """ヘルスチェック endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'service': 'enhanced_mock_api',
            'total_disasters': len(REALISTIC_DISASTERS),
            'data_structure': 'firestore_compatible',
            'last_updated': datetime.utcnow().isoformat(),
            'uptime': '✅ Running'
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        print(f"🌐 API Request: /api/health - OK")

    def log_message(self, format, *args):
        """アクセスログを無効化"""
        pass

def main():
    """拡張モックAPIサーバーを起動"""
    PORT = 8081
    
    print(f"""
🚨 災害情報システム - 拡張モックAPI Server 起動中...
========================================
Port: {PORT}
Data Source: Enhanced Mock (Firestore構造準拠)
Total Disasters: {len(REALISTIC_DISASTERS)}件
Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
========================================
    """)
    
    with socketserver.TCPServer(("", PORT), EnhancedMockAPIHandler) as httpd:
        print(f"✅ Server started on http://localhost:{PORT}")
        print("🔗 Test endpoints:")
        print(f"   • http://localhost:{PORT}/")
        print(f"   • http://localhost:{PORT}/api/public/disasters")
        print(f"   • http://localhost:{PORT}/api/health")
        print("\n📋 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopping...")
            httpd.shutdown()

if __name__ == "__main__":
    main()