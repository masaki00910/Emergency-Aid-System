import os
import json
import random
from typing import Dict, Any, List
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class MockVertexAIClient:
    def __init__(self, project_id: str = "", location: str = ""):
        self.project_id = project_id
        self.location = location
        self.mock_responses = self._load_mock_responses()
    
    def _load_mock_responses(self) -> Dict[str, Any]:
        return {
            "disaster_analysis": {
                "earthquake": {
                    "is_disaster": True,
                    "disaster_type": "earthquake",
                    "location": {"lat": 35.6762, "lng": 139.6503, "admin": "東京都"},
                    "severity": random.uniform(0.3, 0.9),
                    "confidence": 0.85,
                    "summary": "震度5強の地震が発生。建物への被害や交通機関への影響が報告されています。",
                    "reasoning": "地震関連のキーワードが検出され、震度情報が含まれているため災害と判定。"
                },
                "flood": {
                    "is_disaster": True,
                    "disaster_type": "flood", 
                    "location": {"lat": 35.4437, "lng": 139.6380, "admin": "神奈川県横浜市"},
                    "severity": random.uniform(0.4, 0.8),
                    "confidence": 0.80,
                    "summary": "大雨による河川氾濫が発生。避難指示が発令されています。",
                    "reasoning": "洪水・河川氾濫の情報が含まれており、避難指示が出ているため高い深刻度で判定。"
                },
                "typhoon": {
                    "is_disaster": True,
                    "disaster_type": "typhoon",
                    "location": {"lat": 26.2124, "lng": 127.6792, "admin": "沖縄県"},
                    "severity": random.uniform(0.5, 0.9),
                    "confidence": 0.90,
                    "summary": "大型台風が接近中。暴風警報が発表されています。",
                    "reasoning": "台風の接近と警報発表により、高い信頼度で災害と判定。"
                },
                "no_disaster": {
                    "is_disaster": False,
                    "disaster_type": "other",
                    "location": {"lat": 35.6762, "lng": 139.6503, "admin": "不明"},
                    "severity": 0.1,
                    "confidence": 0.3,
                    "summary": "災害情報は検出されませんでした。",
                    "reasoning": "災害に関連するキーワードが見つからないため、災害ではないと判定。"
                }
            },
            "impact_assessment": {
                "earthquake": {
                    "impact_assessment": {
                        "human_impact": {
                            "estimated_affected_population": 250000,
                            "vulnerability_areas": ["木造密集地域", "液状化危険地域"],
                            "evacuation_recommendations": ["高層ビルからの避難", "津波警報地域からの避難"]
                        },
                        "infrastructure_impact": {
                            "transportation": "JR山手線・京浜東北線運転見合わせ。首都高速一部通行止め。",
                            "utilities": "東京電力管内で約5万世帯停電。ガス供給に影響なし。", 
                            "facilities": "羽田空港滑走路点検中。病院・学校に軽微な被害。"
                        },
                        "economic_impact": {
                            "estimated_damage": "約50億円",
                            "affected_industries": ["交通・運輸", "製造業", "小売業"],
                            "recovery_timeline": "交通機関は24時間以内に復旧見込み"
                        }
                    },
                    "response_recommendations": {
                        "immediate_actions": ["余震への警戒", "建物安全確認", "避難所開設"],
                        "resource_allocation": ["救急車両増配備", "避難所職員派遣", "非常食配布"],
                        "coordination_points": ["消防庁", "警視庁", "東京都災害対策本部"]
                    },
                    "information_gaps": ["建物被害の詳細調査", "ライフライン復旧見込み"],
                    "confidence_level": 0.8,
                    "sources_used": ["気象庁", "東京都", "NHK"]
                }
            },
            "web_content": {
                "headline": "【緊急】東京都内で震度5強の地震発生",
                "summary": "本日午後2時頃、東京都内を震源とする地震が発生しました。現在、交通機関への影響や停電が報告されています。",
                "details": {
                    "current_situation": "震度5強の地震により、首都圏の交通機関が運転を見合わせています。", 
                    "affected_areas": ["東京23区", "多摩地域", "神奈川県東部"],
                    "safety_instructions": ["余震に注意", "エレベーター使用禁止", "火の元確認"],
                    "evacuation_info": "現在、避難指示は発令されていません。建物の安全確認後、通常生活を継続してください。",
                    "traffic_info": "JR各線運転見合わせ中。復旧見込みは午後6時頃。",
                    "utility_status": "東京電力管内で約5万世帯停電中。復旧作業進行中。"
                },
                "updates": [
                    {"timestamp": "14:30", "content": "震度5強の地震発生"},
                    {"timestamp": "14:45", "content": "JR各線運転見合わせ"},
                    {"timestamp": "15:00", "content": "停電約5万世帯に拡大"}
                ],
                "map_data": {
                    "center": {"lat": 35.6762, "lng": 139.6503},
                    "markers": [
                        {"lat": 35.6762, "lng": 139.6503, "type": "incident", "title": "震源地", "description": "震度5強"},
                        {"lat": 35.6812, "lng": 139.7671, "type": "evacuation", "title": "避難所", "description": "墨田区体育館"}
                    ]
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    async def generate_disaster_analysis(self, content: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MOCK] Disaster analysis for content: {content[:100]}...")
        
        # コンテンツから災害タイプを推測
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["地震", "震度", "earthquake"]):
            response = self.mock_responses["disaster_analysis"]["earthquake"].copy()
        elif any(keyword in content_lower for keyword in ["洪水", "氾濫", "flood", "大雨"]):
            response = self.mock_responses["disaster_analysis"]["flood"].copy()
        elif any(keyword in content_lower for keyword in ["台風", "typhoon", "暴風"]):
            response = self.mock_responses["disaster_analysis"]["typhoon"].copy()
        else:
            response = self.mock_responses["disaster_analysis"]["no_disaster"].copy()
        
        # ランダム要素追加
        if response["is_disaster"]:
            response["severity"] = random.uniform(0.3, 0.9)
            response["confidence"] = random.uniform(0.7, 0.95)
        
        return response
    
    async def generate_impact_assessment(self, disaster_type: str, location: Dict[str, Any], context: str) -> Dict[str, Any]:
        logger.info(f"[MOCK] Impact assessment for {disaster_type} at {location.get('admin', 'unknown')}")
        
        if disaster_type in self.mock_responses["impact_assessment"]:
            response = self.mock_responses["impact_assessment"][disaster_type].copy()
        else:
            response = self.mock_responses["impact_assessment"]["earthquake"].copy()
            response["impact_assessment"]["human_impact"]["estimated_affected_population"] = random.randint(1000, 500000)
        
        return response
    
    async def generate_web_content(self, disaster_type: str, location: Dict[str, Any], severity: float) -> Dict[str, Any]:
        logger.info(f"[MOCK] Web content generation for {disaster_type}")
        
        content = self.mock_responses["web_content"].copy()
        
        # 災害タイプに応じてカスタマイズ
        if disaster_type == "flood":
            content["headline"] = f"【緊急】{location.get('admin', '地域')}で洪水発生"
            content["summary"] = "大雨による河川氾濫が発生しています。避難指示に従ってください。"
        elif disaster_type == "typhoon":
            content["headline"] = f"【警報】{location.get('admin', '地域')}に台風接近"
            content["summary"] = "大型台風が接近中です。暴風に厳重に警戒してください。"
        
        content["details"]["current_situation"] = f"{disaster_type}による被害が{location.get('admin', '地域')}で発生しています。"
        
        return content
    
    async def generate_mobile_content(self, disaster_type: str, location: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MOCK] Mobile content generation for {disaster_type}")
        
        return {
            "alert_title": f"{location.get('admin', '地域')}で{disaster_type}発生",
            "alert_body": "詳細は災害情報サイトを確認してください。安全な場所に避難してください。",
            "action_required": "避難・安全確保",
            "severity_color": "red" if disaster_type in ["earthquake", "flood"] else "orange",
            "push_notification": {
                "title": "緊急災害情報",
                "body": f"{location.get('admin', '地域')}で{disaster_type}が発生しました"
            }
        }
    
    @property
    def llm_gemini_pro(self):
        return self
    
    @property 
    def llm_gemini_flash(self):
        return self
    
    @property
    def embeddings(self):
        return self
    
    async def ainvoke(self, prompt: str) -> str:
        logger.info(f"[MOCK] LLM invoked with prompt: {prompt[:100]}...")
        
        # プロンプトから処理タイプを判定
        if "災害情報分析" in prompt or "disaster analysis" in prompt.lower():
            if "地震" in prompt or "earthquake" in prompt.lower():
                return json.dumps(self.mock_responses["disaster_analysis"]["earthquake"], ensure_ascii=False)
            elif "洪水" in prompt or "flood" in prompt.lower():
                return json.dumps(self.mock_responses["disaster_analysis"]["flood"], ensure_ascii=False)
            else:
                return json.dumps(self.mock_responses["disaster_analysis"]["no_disaster"], ensure_ascii=False)
        
        elif "影響評価" in prompt or "impact assessment" in prompt.lower():
            return json.dumps(self.mock_responses["impact_assessment"]["earthquake"], ensure_ascii=False)
        
        elif "Webサイト" in prompt or "web content" in prompt.lower():
            return json.dumps(self.mock_responses["web_content"], ensure_ascii=False)
        
        else:
            return json.dumps({"message": "モック応答", "timestamp": datetime.utcnow().isoformat()}, ensure_ascii=False)
    
    async def aembed_query(self, text: str) -> List[float]:
        logger.info(f"[MOCK] Embedding query: {text[:50]}...")
        # ダミーエンベディング (768次元)
        return [random.uniform(-1, 1) for _ in range(768)]


def create_mock_vertex_ai_client(project_id: str = "", location: str = "") -> MockVertexAIClient:
    return MockVertexAIClient(project_id, location)