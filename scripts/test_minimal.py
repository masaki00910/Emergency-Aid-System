#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

print("=== 災害対応システム 最小テスト ===")

# 環境変数設定
os.environ['USE_MOCK_LLM'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-disaster-response'

print("✅ 環境変数設定完了")

# パス設定テスト
sys.path.append('/workspace/disaster-response-system')

try:
    # モックLLMクライアント単体テスト
    sys.path.append('/workspace/disaster-response-system/shared/utils')
    from mock_llm_client import create_mock_vertex_ai_client
    
    print("✅ モックLLMクライアント読み込み成功")
    
    # モッククライアント作成
    mock_client = create_mock_vertex_ai_client()
    
    # 災害分析テスト
    print("\n=== 災害分析テスト ===")
    
    # 地震テスト
    content = "東京都内で震度5強の地震が発生しました。建物への被害が報告されています。"
    
    import asyncio
    
    async def test_analysis():
        analysis = await mock_client.generate_disaster_analysis(
            content=content,
            source_info={"source": "test", "timestamp": datetime.now().isoformat()}
        )
        return analysis
    
    analysis_result = asyncio.run(test_analysis())
    
    print(f"災害判定: {analysis_result.get('is_disaster')}")
    print(f"災害種別: {analysis_result.get('disaster_type')}")
    print(f"深刻度: {analysis_result.get('severity')}")
    print(f"要約: {analysis_result.get('summary')}")
    
    print("✅ 災害分析テスト成功")
    
    # 影響評価テスト
    print("\n=== 影響評価テスト ===")
    
    async def test_impact():
        impact = await mock_client.generate_impact_assessment(
            disaster_type="earthquake",
            location={"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
            context=""
        )
        return impact
    
    impact_result = asyncio.run(test_impact())
    
    print(f"推定影響人口: {impact_result.get('impact_assessment', {}).get('human_impact', {}).get('estimated_affected_population')}")
    print(f"即座に必要な対応: {impact_result.get('response_recommendations', {}).get('immediate_actions')}")
    
    print("✅ 影響評価テスト成功")
    
    # Webコンテンツ生成テスト
    print("\n=== Webコンテンツ生成テスト ===")
    
    async def test_web_content():
        content = await mock_client.generate_web_content(
            disaster_type="earthquake",
            location={"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
            severity=0.7
        )
        return content
    
    web_result = asyncio.run(test_web_content())
    
    print(f"見出し: {web_result.get('headline')}")
    print(f"概要: {web_result.get('summary')}")
    
    print("✅ Webコンテンツ生成テスト成功")
    
    print("\n=== 全テスト完了 ===")
    print("✅ モックLLM機能が正常に動作しています")
    print("\n次のステップ:")
    print("1. エミュレータ起動: ./scripts/setup_emulators.sh")
    print("2. Agent起動: cd agents/detection && python3 main.py")
    print("3. テスト実行: curl -X POST http://localhost:8080/detect")

except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("依存関係が不足している可能性があります")
    
except Exception as e:
    print(f"❌ テストエラー: {e}")
    print("予期しないエラーが発生しました")