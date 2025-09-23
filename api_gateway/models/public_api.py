from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class LocationModel(BaseModel):
    lat: float = Field(description="緯度")
    lng: float = Field(description="経度")
    admin: str = Field(description="行政区域名")

class DisasterModel(BaseModel):
    id: str = Field(description="災害ID")
    title: str = Field(description="災害タイトル")
    type: str = Field(description="災害種別")
    location: LocationModel
    severity: str = Field(description="重要度レベル (high/medium/low)")
    confidence: float = Field(ge=0.0, le=1.0, description="信頼度")
    is_active: bool = Field(description="アクティブ状態")
    reported_at: datetime = Field(description="報告日時")
    last_updated: datetime = Field(description="最終更新日時")
    description: str = Field(description="詳細説明")
    source: List[str] = Field(default=[], description="情報源")

class DisasterResponse(BaseModel):
    disasters: List[DisasterModel]
    total_count: int = Field(description="総件数")
    current_page: int = Field(description="現在のページ")
    total_pages: int = Field(description="総ページ数")
    per_page: int = Field(description="1ページあたりの件数")
    filters_applied: Dict[str, Any] = Field(description="適用されたフィルタ")
    last_updated: datetime = Field(description="データ最終更新時刻")

class MapMarker(BaseModel):
    id: str
    lat: float
    lng: float
    type: str
    severity: str
    title: str
    is_active: bool
    reported_at: Optional[datetime] = None

class MapBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float

class MapDataResponse(BaseModel):
    markers: List[MapMarker]
    bounds: MapBounds
    total_markers: int = Field(description="マーカー総数")
    last_updated: datetime

# WebSocket用メッセージモデル
class WebSocketMessage(BaseModel):
    type: str = Field(description="メッセージタイプ")
    data: Dict[str, Any] = Field(description="メッセージデータ")
    timestamp: datetime = Field(description="送信時刻")

class DisasterUpdateMessage(BaseModel):
    type: str = "disaster_update"
    action: str = Field(description="アクション: created/updated/resolved")
    data: DisasterModel = Field(description="災害データ")
    timestamp: datetime

class SubscriptionSettings(BaseModel):
    prefectures: Optional[List[str]] = Field(None, description="監視する都道府県")
    min_severity: Optional[str] = Field(None, description="最小重要度")
    disaster_types: Optional[List[str]] = Field(None, description="監視する災害種別")

# FAQ関連モデル
class FAQModel(BaseModel):
    id: str = Field(description="FAQ ID")
    disaster_id: str = Field(description="関連災害ID")
    question: str = Field(description="質問文")
    answer: str = Field(description="回答文")
    category: str = Field(description="カテゴリ")
    priority: int = Field(description="優先度")
    created_at: datetime = Field(description="作成日時")

class FAQResponse(BaseModel):
    disaster_id: str = Field(description="災害ID")
    disaster_title: str = Field(description="災害タイトル")
    hazard_type: str = Field(description="災害種別")
    area: str = Field(description="地域")
    faqs: List[FAQModel] = Field(description="FAQ一覧")
    last_updated: datetime = Field(description="最終更新日時")

class FAQQuestionRequest(BaseModel):
    question: str = Field(description="ユーザーの質問")

class FAQAnswerResponse(BaseModel):
    question: str = Field(description="質問文")
    answer: str = Field(description="AI回答")
    timestamp: datetime = Field(description="回答時刻")
    model_used: str = Field(description="使用したAIモデル")