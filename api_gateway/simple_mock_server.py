#!/usr/bin/env python3
"""
シンプルなモックAPIサーバー
Python標準ライブラリのみを使用してテスト用APIを提供
"""
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import uuid

# リアルなFirestore構造に基づくモックデータ
MOCK_DISASTERS = [
    {
        "id": "disaster_2025_001",
        "event_id": "EVT_20250001",
        "title": "🌍 地震発生（震度5弱）",
        "description": "東京都千代田区で地震発生（震度5弱）が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。",
        "type": "earthquake",
        "severity": "high",
        "location": {
            "lat": 35.6762,
            "lng": 139.6503,
            "admin": "東京都千代田区"
        },
        "reported_at": "2025-01-15T09:30:00Z",
        "detected_at": "2025-01-15T09:30:00Z",
        "confidence": 0.89,
        "source": ["気象庁", "NHK NEWS WEB", "Twitter公式情報"],
        "evidence": [
            {
                "url": "https://example.com/evidence/0_0",
                "title": "気象庁からの報告",
                "source": "気象庁",
                "timestamp": "2025-01-15T09:30:00Z",
                "hash": "hash_0_0"
            }
        ],
        "summary": "東京都千代田区においてearthquakeによる被害が確認されています。関係機関が対応中。",
        "agent_analysis": {
            "risk_level": "high",
            "affected_population": 15000,
            "response_priority": "urgent",
            "estimated_damage": "中程度"
        },
        "status": "active",
        "tags": ["緊急対応", "避難指示", "被害調査"],
        "is_active": True,
        "last_updated": "2025-01-15T09:35:00Z"
    },
    {
        "id": "disaster_2025_002",
        "event_id": "EVT_20250002",
        "title": "🌊 河川氾濫警戒",
        "description": "神奈川県横浜市で河川氾濫警戒が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。",
        "type": "flood",
        "severity": "medium",
        "location": {
            "lat": 35.4437,
            "lng": 139.6380,
            "admin": "神奈川県横浜市"
        },
        "reported_at": "2025-01-15T07:45:00Z",
        "detected_at": "2025-01-15T07:45:00Z",
        "confidence": 0.76,
        "source": ["気象庁", "Yahoo!ニュース"],
        "evidence": [
            {
                "url": "https://example.com/evidence/1_0",
                "title": "Yahoo!ニュースからの報告",
                "source": "Yahoo!ニュース",
                "timestamp": "2025-01-15T07:45:00Z",
                "hash": "hash_1_0"
            }
        ],
        "summary": "神奈川県横浜市においてfloodによる被害が確認されています。関係機関が対応中。",
        "agent_analysis": {
            "risk_level": "medium",
            "affected_population": 8500,
            "response_priority": "high",
            "estimated_damage": "軽微"
        },
        "status": "monitoring",
        "tags": ["警戒情報", "被害調査"],
        "is_active": True,
        "last_updated": "2025-01-15T08:20:00Z"
    },
    {
        "id": "disaster_2025_003",
        "event_id": "EVT_20250003",
        "title": "🌀 台風19号接近",
        "description": "沖縄県那覇市で台風19号接近が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。",
        "type": "typhoon",
        "severity": "high",
        "location": {
            "lat": 26.2125,
            "lng": 127.6792,
            "admin": "沖縄県那覇市"
        },
        "reported_at": "2025-01-15T06:15:00Z",
        "detected_at": "2025-01-15T06:15:00Z",
        "confidence": 0.93,
        "source": ["気象庁", "沖縄タイムス", "センサーデータ"],
        "evidence": [
            {
                "url": "https://example.com/evidence/2_0",
                "title": "センサーデータからの報告",
                "source": "センサーデータ",
                "timestamp": "2025-01-15T06:15:00Z",
                "hash": "hash_2_0"
            },
            {
                "url": "https://example.com/evidence/2_1",
                "title": "衛星画像解析からの報告",
                "source": "衛星画像解析",
                "timestamp": "2025-01-15T06:15:00Z",
                "hash": "hash_2_1"
            }
        ],
        "summary": "沖縄県那覇市においてtyphoonによる被害が確認されています。関係機関が対応中。",
        "agent_analysis": {
            "risk_level": "high",
            "affected_population": 25000,
            "response_priority": "urgent",
            "estimated_damage": "甚大"
        },
        "status": "active",
        "tags": ["緊急対応", "避難指示", "警戒情報"],
        "is_active": True,
        "last_updated": "2025-01-15T06:50:00Z"
    },
    {
        "id": "disaster_2025_004",
        "event_id": "EVT_20250004",
        "title": "⛰️ 土砂崩れ発生",
        "description": "広島県広島市中区で土砂崩れ発生が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。",
        "type": "landslide",
        "severity": "medium",
        "location": {
            "lat": 34.3853,
            "lng": 132.4553,
            "admin": "広島県広島市中区"
        },
        "reported_at": "2025-01-15T04:20:00Z",
        "detected_at": "2025-01-15T04:20:00Z",
        "confidence": 0.81,
        "source": ["消防庁", "住民からの報告"],
        "evidence": [
            {
                "url": "https://example.com/evidence/3_0",
                "title": "住民からの報告からの報告",
                "source": "住民からの報告",
                "timestamp": "2025-01-15T04:20:00Z",
                "hash": "hash_3_0"
            }
        ],
        "summary": "広島県広島市中区においてlandslideによる被害が確認されています。関係機関が対応中。",
        "agent_analysis": {
            "risk_level": "medium",
            "affected_population": 3200,
            "response_priority": "medium",
            "estimated_damage": "中程度"
        },
        "status": "investigating",
        "tags": ["被害調査", "復旧作業"],
        "is_active": True,
        "last_updated": "2025-01-15T05:10:00Z"
    },
    {
        "id": "disaster_2025_005",
        "event_id": "EVT_20250005",
        "title": "❄️ 大雪警報発令",
        "description": "北海道札幌市中央区で大雪警報発令が発生。被害状況を調査中です。住民の皆様は安全確保をお願いします。",
        "type": "snow",
        "severity": "low",
        "location": {
            "lat": 43.0642,
            "lng": 141.3469,
            "admin": "北海道札幌市中央区"
        },
        "reported_at": "2025-01-14T22:30:00Z",
        "detected_at": "2025-01-14T22:30:00Z",
        "confidence": 0.67,
        "source": ["気象庁"],
        "evidence": [
            {
                "url": "https://example.com/evidence/4_0",
                "title": "気象庁からの報告",
                "source": "気象庁",
                "timestamp": "2025-01-14T22:30:00Z",
                "hash": "hash_4_0"
            }
        ],
        "summary": "北海道札幌市中央区においてsnowによる被害が確認されています。関係機関が対応中。",
        "agent_analysis": {
            "risk_level": "low",
            "affected_population": 1800,
            "response_priority": "low",
            "estimated_damage": "軽微"
        },
        "status": "resolved",
        "tags": ["情報収集"],
        "is_active": False,
        "last_updated": "2025-01-14T23:45:00Z"
    }
]

class MockAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        print(f"📡 {datetime.now().strftime('%H:%M:%S')} GET {path}")
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # ルーティング
        if path == '/':
            response = {
                "service": "災害情報システム - リアルなFirestore構造対応API",
                "version": "2.0.0",
                "status": "healthy",
                "data_source": "firestore_structure_mock",
                "total_disasters": len(MOCK_DISASTERS),
                "timestamp": datetime.utcnow().isoformat(),
                "features": [
                    "Firestore構造準拠データ",
                    "エビデンス情報",
                    "エージェント分析結果",
                    "リアルタイムタイムスタンプ",
                    "タグ・ステータス管理"
                ],
                "endpoints": {
                    "disasters": "/api/public/disasters",
                    "disaster_detail": "/api/public/disasters/{id}",
                    "map_data": "/api/public/disasters/map-data",
                    "stats": "/api/public/disasters/stats"
                }
            }
        
        elif path == '/api/public/disasters':
            # フィルタリング
            page = int(query_params.get('page', [1])[0])
            limit = int(query_params.get('limit', [20])[0])
            severity = query_params.get('severity', [None])[0]
            
            filtered_disasters = MOCK_DISASTERS
            if severity:
                filtered_disasters = [d for d in MOCK_DISASTERS if d['severity'] == severity]
            
            # ページネーション
            start = (page - 1) * limit
            end = start + limit
            paginated = filtered_disasters[start:end]
            
            response = {
                "disasters": paginated,
                "total_count": len(filtered_disasters),
                "current_page": page,
                "total_pages": (len(filtered_disasters) + limit - 1) // limit,
                "per_page": limit,
                "filters_applied": {
                    "severity": severity,
                    "page": page,
                    "limit": limit
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        
        elif path == '/api/public/disasters/map-data':
            # マップデータ（特別なエンドポイントを先に処理）
            markers = []
            for disaster in MOCK_DISASTERS:
                markers.append({
                    "id": disaster["id"],
                    "lat": disaster["location"]["lat"], 
                    "lng": disaster["location"]["lng"],
                    "type": disaster["type"],
                    "severity": disaster["severity"],
                    "title": disaster["title"],
                    "is_active": disaster["is_active"],
                    "reported_at": disaster["reported_at"]
                })
            
            # 境界計算
            if markers:
                lats = [m["lat"] for m in markers]
                lngs = [m["lng"] for m in markers]
                bounds = {
                    "north": max(lats),
                    "south": min(lats),
                    "east": max(lngs),
                    "west": min(lngs)
                }
            else:
                bounds = {"north": 45.0, "south": 30.0, "east": 150.0, "west": 130.0}
            
            response = {
                "markers": markers,
                "bounds": bounds,
                "total_markers": len(markers),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        elif path == '/api/public/disasters/stats':
            # 統計データ（特別なエンドポイントを先に処理）
            type_counts = {}
            severity_counts = {"high": 0, "medium": 0, "low": 0}
            
            for disaster in MOCK_DISASTERS:
                # 種別集計
                disaster_type = disaster['type']
                type_counts[disaster_type] = type_counts.get(disaster_type, 0) + 1
                
                # 重要度集計
                severity = disaster['severity']
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            response = {
                "total_active_disasters": len(MOCK_DISASTERS),
                "disaster_by_type": type_counts,
                "disaster_by_severity": severity_counts,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        elif path.startswith('/api/public/disasters/') and len(path.split('/')) == 5:
            # 災害詳細取得（一般的なIDベースのパス）
            disaster_id = path.split('/')[-1]
            disaster = next((d for d in MOCK_DISASTERS if d['id'] == disaster_id), None)
            
            if disaster:
                response = disaster
            else:
                self.send_response(404)
                response = {"error": "災害情報が見つかりません"}
        
        
        else:
            self.send_response(404)
            response = {"error": "エンドポイントが見つかりません"}
        
        # JSON レスポンス送信
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # ログを簡素化
        pass

def start_mock_server(port=8081):
    """モックAPIサーバーを起動"""
    with socketserver.TCPServer(("", port), MockAPIHandler) as httpd:
        print(f"🚀 Mock API Server starting on port {port}")
        print(f"📡 API Base URL: http://localhost:{port}")
        print(f"📖 API Documentation: http://localhost:{port}/")
        print(f"🔍 Disasters API: http://localhost:{port}/api/public/disasters")
        print(f"🗺️  Map Data: http://localhost:{port}/api/public/disasters/map-data")
        print(f"📊 Stats: http://localhost:{port}/api/public/disasters/stats")
        print(f"✋ Stop: Ctrl+C")
        print("=" * 60)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Mock server stopped")

if __name__ == "__main__":
    start_mock_server()