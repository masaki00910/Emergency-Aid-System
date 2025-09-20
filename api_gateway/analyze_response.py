#!/usr/bin/env python3
"""
API Response Analysis Tool - Enhanced Fields 調査
"""

import json
import requests

def analyze_api_response():
    try:
        # API レスポンスを取得
        response = requests.get('http://localhost:8082/api/public/disasters')
        data = response.json()
        
        print('=== Real API Response Analysis ===')
        print(f'Status Code: {response.status_code}')
        print(f'Total disasters: {data.get("total", 0)}')
        
        if data.get('disasters') and len(data['disasters']) > 0:
            disaster = data['disasters'][0]
            print(f'\n=== First Disaster Complete Data ===')
            
            # 基本フィールドの確認
            basic_fields = ['id', 'title', 'type', 'severity', 'reported_at', 'status']
            print('📝 Basic Fields:')
            for field in basic_fields:
                value = disaster.get(field, 'MISSING')
                print(f'   {field}: {value}')
            
            # Enhanced fieldsの詳細確認
            enhanced_fields = [
                'bulletins_count', 'latest_bulletin_id', 'last_bulletin_at',
                'affected_population', 'risk_assessment', 'related_news_count',
                'orchestration_started_at', 'has_analysis', 'has_collected_info'
            ]
            print(f'\n🔥 Enhanced Fields Status:')
            for field in enhanced_fields:
                value = disaster.get(field)
                status = '✅' if value is not None else '❌'
                print(f'   {status} {field}: {value}')
            
            # Location情報
            location = disaster.get('location', {})
            print(f'\n📍 Location Info:')
            print(f'   lat: {location.get("lat", "MISSING")}')
            print(f'   lng: {location.get("lng", "MISSING")}')
            print(f'   admin: {location.get("admin", "MISSING")}')
            
            # 元のFirestoreデータ構造の推測
            print(f'\n🗂️ All Available Fields:')
            all_fields = list(disaster.keys())
            for field in sorted(all_fields):
                if field not in basic_fields and field not in enhanced_fields and field != 'location':
                    value = disaster[field]
                    print(f'   - {field}: {value}')
            
            # Enhanced fields の問題分析
            missing_enhanced = [f for f in enhanced_fields if disaster.get(f) is None]
            if missing_enhanced:
                print(f'\n⚠️ Missing Enhanced Fields ({len(missing_enhanced)}/{len(enhanced_fields)}):')
                for field in missing_enhanced:
                    print(f'   ❌ {field}')
            else:
                print(f'\n✅ All Enhanced Fields Present!')
                
            # Raw JSON 出力（最初の災害データ）
            print(f'\n📄 Raw JSON of First Disaster:')
            print(json.dumps(disaster, indent=2, ensure_ascii=False, default=str))
                
        else:
            print('❌ No disasters found in response')
            
    except requests.exceptions.ConnectionError:
        print('❌ Cannot connect to API server at localhost:8082')
    except json.JSONDecodeError as e:
        print(f'❌ JSON Parse Error: {e}')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    analyze_api_response()