from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class DisasterType(str, Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    TYPHOON = "typhoon"
    LANDSLIDE = "landslide"
    WILDFIRE = "wildfire"
    SNOW = "snow"
    OTHER = "other"


class Location(BaseModel):
    lat: float
    lng: float
    admin: str = Field(description="行政区域名")


class Evidence(BaseModel):
    url: str
    title: Optional[str] = None
    source: str
    timestamp: datetime
    hash: str = Field(description="重複排除用ハッシュ")


class DisasterEvent(BaseModel):
    event_id: str
    detected_at: datetime
    source: List[str]
    type: DisasterType
    location: Location
    severity: float = Field(ge=0.0, le=1.0, description="深刻度 0.0-1.0")
    confidence: float = Field(ge=0.0, le=1.0, description="信頼度 0.0-1.0")
    summary: str
    evidence: List[Evidence]


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AgentTask(BaseModel):
    task_id: str
    event_id: str
    agent: str
    status: TaskStatus = TaskStatus.PENDING
    payload: dict
    created_at: datetime
    updated_at: Optional[datetime] = None
    result_ref: Optional[str] = None


class AgentResult(BaseModel):
    task_id: str
    agent: str
    status: TaskStatus
    result: dict
    updated_at: datetime
    errors: Optional[List[str]] = None