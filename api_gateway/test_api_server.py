#!/usr/bin/env python3
"""
Test API Server with Mock Data - demonstrates enhanced fields implementation
This server shows the priority medium fixes with additional Firestore data fields
"""

import json
import http.server
import socketserver
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
import os

# Mock Firestore data with enhanced fields
MOCK_DISASTERS = [
    {
        'id': 'test-incident-001',
        'event_id': 'test-incident-001',
        'summary': '東京都千代田区で震度5弱の地震が発生しました。',
        'type': 'earthquake',
        'severity': 0.85,
        'location': {'lat': 35.6762, 'lng': 139.6503, 'admin': '東京都千代田区'},
        'detected_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        'confidence': 0.89,
        'source': ['detection_agent'],
        'evidence': [
            {
                'url': 'https://example.com/evidence/1',
                'title': '地震情報',
                'source': 'detection_agent',
                'timestamp': '2025-01-15 09:30:00',
                'hash': 'hash_001'
            }
        ],
        # Enhanced fields from bulletins collection
        'bulletins': ['bulletin_001', 'bulletin_002'],
        'last_bulletin_at': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        
        # Enhanced fields from analysis_results collection  
        'analysis_results': [
            {
                'affected_population': 125000,
                'risk_level': 'high',
                'analysis_timestamp': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            }
        ],
        
        # Enhanced fields from collected_info collection
        'collected_info': [
            {'type': 'news', 'source': 'NHK', 'timestamp': datetime.now(timezone.utc).isoformat()},
            {'type': 'social', 'source': 'Twitter', 'timestamp': datetime.now(timezone.utc).isoformat()},
            {'type': 'sensor', 'source': 'JMA', 'timestamp': datetime.now(timezone.utc).isoformat()}
        ],
        
        'orchestration_started_at': (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    },
    {
        'id': 'test-incident-002', 
        'event_id': 'test-incident-002',
        'summary': '神奈川県横浜市で河川氾濫の危険性が高まっています。',
        'type': 'flood',
        'severity': 0.65,
        'location': {'lat': 35.4437, 'lng': 139.638, 'admin': '神奈川県横浜市'},
        'detected_at': (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
        'confidence': 0.76,
        'source': ['detection_agent'],
        'evidence': [
            {
                'url': 'https://example.com/evidence/2',
                'title': '河川情報',
                'source': 'detection_agent', 
                'timestamp': '2025-01-15 07:45:00',
                'hash': 'hash_002'
            }
        ],
        # Enhanced fields
        'bulletins': ['bulletin_003'],
        'last_bulletin_at': (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
        'analysis_results': [
            {
                'affected_population': 45000,
                'risk_level': 'medium',
                'analysis_timestamp': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            }
        ],
        'collected_info': [
            {'type': 'news', 'source': 'NHK', 'timestamp': datetime.now(timezone.utc).isoformat()},
            {'type': 'social', 'source': 'Twitter', 'timestamp': datetime.now(timezone.utc).isoformat()}
        ],
        'orchestration_started_at': (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    },
    {
        'id': 'test-incident-003',
        'event_id': 'test-incident-003', 
        'summary': '沖縄県那覇市に台風19号が接近中です。',
        'type': 'typhoon',
        'severity': 0.93,
        'location': {'lat': 26.2125, 'lng': 127.6792, 'admin': '沖縄県那覇市'},
        'detected_at': (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),
        'confidence': 0.93,
        'source': ['detection_agent'],
        'evidence': [
            {
                'url': 'https://example.com/evidence/3',
                'title': '台風情報',
                'source': 'detection_agent',
                'timestamp': '2025-01-15 06:15:00', 
                'hash': 'hash_003'
            }
        ],
        # Enhanced fields - older incident shows inactive status
        'bulletins': [],
        'last_bulletin_at': None,
        'analysis_results': [
            {
                'affected_population': 200000,
                'risk_level': 'very_high',
                'analysis_timestamp': (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
            }
        ],
        'collected_info': [
            {'type': 'news', 'source': 'Weather Channel', 'timestamp': datetime.now(timezone.utc).isoformat()}
        ],
        'orchestration_started_at': (datetime.now(timezone.utc) - timedelta(hours=32)).isoformat()
    }
]

def transform_firestore_data(firestore_data):
    """Transform mock Firestore data to frontend format with enhanced fields"""
    try:
        # Severity conversion
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

        # Date conversion
        detected_at = firestore_data.get('detected_at')
        if isinstance(detected_at, str):
            reported_at = detected_at
        else:
            reported_at = datetime.utcnow().isoformat()
        
        # Status determination logic (24 hours + severity >= 0.5)
        is_recent = False
        if detected_at:
            try:
                detected_time = datetime.fromisoformat(str(detected_at).replace('Z', '+00:00'))
                time_diff = datetime.now(timezone.utc) - detected_time.replace(tzinfo=timezone.utc)
                is_recent = time_diff < timedelta(hours=24)
            except Exception:
                is_recent = True

        is_active = is_recent and (severity_value >= 0.5)
        
        # Enhanced data processing
        bulletins = firestore_data.get('bulletins', [])
        analysis_results = firestore_data.get('analysis_results', [])
        collected_info = firestore_data.get('collected_info', [])
        
        # Latest bulletin info
        latest_bulletin_id = None
        if bulletins:
            latest_bulletin_id = bulletins[-1] if isinstance(bulletins, list) else bulletins
        
        # Analysis results processing
        affected_population = 0
        risk_assessment = 'unknown'
        if analysis_results:
            latest_analysis = analysis_results[-1] if isinstance(analysis_results, list) else analysis_results
            if isinstance(latest_analysis, dict):
                affected_population = latest_analysis.get('affected_population', 0)
                risk_assessment = latest_analysis.get('risk_level', 'unknown')
        
        # Related news count
        related_news_count = len(collected_info) if isinstance(collected_info, list) else 0
        
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
            
            # **ENHANCED FIELDS - Priority Medium Implementation**
            'bulletins_count': len(bulletins) if isinstance(bulletins, list) else (1 if bulletins else 0),
            'latest_bulletin_id': latest_bulletin_id,
            'last_bulletin_at': firestore_data.get('last_bulletin_at'),
            'affected_population': affected_population,
            'risk_assessment': risk_assessment,
            'related_news_count': related_news_count,
            'orchestration_started_at': firestore_data.get('orchestration_started_at'),
            
            # Detailed information access flags
            'has_analysis': len(analysis_results) > 0 if isinstance(analysis_results, list) else bool(analysis_results),
            'has_collected_info': len(collected_info) > 0 if isinstance(collected_info, list) else bool(collected_info)
        }
        
    except Exception as e:
        print(f"❌ Data transformation error: {e}")
        return {
            'id': firestore_data.get('event_id', 'error'),
            'title': '災害情報',
            'description': '詳細情報なし',
            'type': 'other',
            'severity': 'medium',
            'location': {'lat': 35.6762, 'lng': 139.6503, 'admin': '不明'},
            'reported_at': datetime.utcnow().isoformat(),
            'confidence': 0.0,
            'source': ['System'],
            'evidence': [],
            'status': 'monitoring'
        }

class TestAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        print(f"📥 Request: {path}")
        
        # CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        if path == '/api/public/disasters':
            # Transform mock data to show enhanced fields
            transformed_disasters = [transform_firestore_data(disaster) for disaster in MOCK_DISASTERS]
            
            response = {
                'disasters': transformed_disasters,
                'total': len(transformed_disasters),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'mock_data_with_enhanced_fields'
            }
            
            print(f"✅ Returning {len(transformed_disasters)} disasters with enhanced fields")
            print(f"🔍 Sample enhanced fields from first disaster:")
            if transformed_disasters:
                sample = transformed_disasters[0]
                print(f"   - bulletins_count: {sample.get('bulletins_count')}")
                print(f"   - affected_population: {sample.get('affected_population')}")
                print(f"   - risk_assessment: {sample.get('risk_assessment')}")
                print(f"   - status: {sample.get('status')}")
                print(f"   - has_analysis: {sample.get('has_analysis')}")
            
        elif path.startswith('/api/public/disasters/') and path.endswith('/analysis'):
            disaster_id = path.split('/')[-2]
            disaster = next((d for d in MOCK_DISASTERS if d['id'] == disaster_id), None)
            
            if disaster:
                analysis_results = disaster.get('analysis_results', [])
                response = {
                    'event_id': disaster_id,
                    'analysis_results': analysis_results,
                    'total': len(analysis_results),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                response = {'error': 'Disaster not found'}
                
        elif path.startswith('/api/public/disasters/') and path.endswith('/bulletins'):
            disaster_id = path.split('/')[-2]
            disaster = next((d for d in MOCK_DISASTERS if d['id'] == disaster_id), None)
            
            if disaster:
                bulletins = disaster.get('bulletins', [])
                response = {
                    'event_id': disaster_id, 
                    'bulletins': bulletins,
                    'total': len(bulletins),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                response = {'error': 'Disaster not found'}
                
        elif path.startswith('/api/public/disasters/') and path.endswith('/collected_info'):
            disaster_id = path.split('/')[-2]
            disaster = next((d for d in MOCK_DISASTERS if d['id'] == disaster_id), None)
            
            if disaster:
                collected_info = disaster.get('collected_info', [])
                response = {
                    'event_id': disaster_id,
                    'collected_info': collected_info,
                    'total': len(collected_info),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                response = {'error': 'Disaster not found'}
                
        elif path == '/health':
            response = {
                'status': 'healthy',
                'mode': 'test_api_with_enhanced_fields',
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            response = {'error': 'Endpoint not found'}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    PORT = 8083  # Different port to avoid conflicts
    print(f"🚀 Test API Server with Enhanced Fields starting on port {PORT}")
    print("📋 Features demonstrated:")
    print("   ✅ Priority Medium fixes implemented")
    print("   ✅ Enhanced fields: bulletins_count, affected_population, risk_assessment")
    print("   ✅ Status determination logic (24h + severity >= 0.5)")
    print("   ✅ Additional endpoints: /analysis, /bulletins, /collected_info")
    print(f"📡 Test with: curl http://localhost:{PORT}/api/public/disasters")
    
    with socketserver.TCPServer(("", PORT), TestAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")