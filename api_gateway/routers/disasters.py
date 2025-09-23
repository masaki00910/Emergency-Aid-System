from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from models.public_api import DisasterResponse, DisasterModel, MapDataResponse, MapMarker, MapBounds
from services.disaster_service import DisasterService

router = APIRouter()
disaster_service = DisasterService()

@router.get("/disasters", response_model=DisasterResponse)
async def get_disasters(
    # ページネーション
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),

    # フィルタリング
    prefecture: Optional[str] = Query(None, description="都道府県名"),
    disaster_type: Optional[str] = Query(None, description="災害種別 (earthquake/flood/typhoon/landslide/wildfire/snow/other)"),
    severity: Optional[str] = Query(None, description="重要度 (high/medium/low)"),
    is_active: Optional[bool] = Query(None, description="アクティブ状態"),

    # 時間範囲
    since: Optional[datetime] = Query(None, description="この時刻以降の災害"),
    until: Optional[datetime] = Query(None, description="この時刻以前の災害"),
    recent_only: bool = Query(True, description="24時間以内のみ表示（パフォーマンス向上）"),

    # ソート
    sort_by: str = Query("detected_at", description="ソート項目"),
    order: str = Query("desc", regex="^(asc|desc)$", description="ソート順")
):
    """
    災害一覧を取得

    このエンドポイントは既存のFirestoreデータを取得し、
    フロントエンド向けに整形して返します。
    """
    try:
        # データ取得
        disasters, total_count = await disaster_service.get_disasters(
            page=page,
            limit=limit,
            prefecture=prefecture,
            disaster_type=disaster_type,
            severity=severity,
            is_active=is_active,
            since=since,
            until=until,
            sort_by=sort_by,
            order=order,
            recent_only=recent_only
        )

        # フィルター情報
        filters_applied = {
            "prefecture": prefecture,
            "disaster_type": disaster_type,
            "severity": severity,
            "is_active": is_active,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "recent_only": recent_only,
            "sort_by": sort_by,
            "order": order
        }

        # レスポンス構築
        return DisasterResponse(
            disasters=disasters,
            total_count=total_count,
            current_page=page,
            total_pages=(total_count + limit - 1) // limit if total_count > 0 else 0,
            per_page=limit,
            filters_applied=filters_applied,
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"災害情報取得エラー: {str(e)}")

@router.get("/disasters/{disaster_id}", response_model=DisasterModel)
async def get_disaster_detail(disaster_id: str):
    """
    災害詳細情報を取得

    指定されたIDの災害情報の詳細を返します。
    """
    try:
        disaster = await disaster_service.get_disaster_by_id(disaster_id)
        if not disaster:
            raise HTTPException(status_code=404, detail="災害情報が見つかりません")

        return disaster

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"災害詳細取得エラー: {str(e)}")

@router.get("/disasters/map-data", response_model=MapDataResponse)
async def get_map_data(
    # 地図範囲
    north: Optional[float] = Query(None, description="北緯", ge=-90, le=90),
    south: Optional[float] = Query(None, description="南緯", ge=-90, le=90),
    east: Optional[float] = Query(None, description="東経", ge=-180, le=180),
    west: Optional[float] = Query(None, description="西経", ge=-180, le=180),

    # フィルタ
    disaster_type: Optional[str] = Query(None, description="災害種別"),
    severity: Optional[str] = Query(None, description="重要度 (high/medium/low)"),
    is_active: Optional[bool] = Query(True, description="アクティブのみ表示")
):
    """
    マップ表示用の軽量化された災害データを取得

    大量のマーカーを効率的に表示するため、
    必要最小限の情報のみを返します。
    """
    try:
        # 地図範囲フィルタ
        bounds = None
        if all([north, south, east, west]):
            # 範囲の妥当性チェック
            if north <= south or east <= west:
                raise HTTPException(status_code=400, detail="無効な地図範囲が指定されました")
            
            bounds = {
                "north": north, "south": south,
                "east": east, "west": west
            }

        # マップデータ取得
        markers = await disaster_service.get_map_markers(
            bounds=bounds,
            disaster_type=disaster_type,
            severity=severity,
            is_active=is_active
        )

        # 全体の境界計算
        if markers:
            lats = [m["lat"] for m in markers]
            lngs = [m["lng"] for m in markers]
            computed_bounds = MapBounds(
                north=max(lats),
                south=min(lats),
                east=max(lngs),
                west=min(lngs)
            )
        else:
            computed_bounds = MapBounds(
                north=bounds['north'] if bounds else 45.0,
                south=bounds['south'] if bounds else 30.0,
                east=bounds['east'] if bounds else 150.0,
                west=bounds['west'] if bounds else 130.0
            )

        return MapDataResponse(
            markers=markers,
            bounds=computed_bounds,
            total_markers=len(markers),
            last_updated=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マップデータ取得エラー: {str(e)}")

@router.get("/disasters/stats")
async def get_disaster_stats():
    """
    災害統計情報を取得（簡易版）
    """
    try:
        # 基本統計を取得
        disasters, total_count = await disaster_service.get_disasters(
            limit=1000,  # 統計用に多めに取得
            is_active=True
        )
        
        # 種別別集計
        type_counts = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        
        for disaster in disasters:
            # 種別集計
            disaster_type = disaster.get('type', 'other')
            type_counts[disaster_type] = type_counts.get(disaster_type, 0) + 1
            
            # 重要度集計
            severity = disaster.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            "total_active_disasters": len(disasters),
            "disaster_by_type": type_counts,
            "disaster_by_severity": severity_counts,
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計データ取得エラー: {str(e)}")

@router.get("/disasters/debug")
async def get_firestore_debug():
    """
    Firestoreデータ構造のデバッグ情報取得
    """
    try:
        # 直接Firestoreからデータを取得してデバッグ
        db = disaster_service.db
        
        # 全件数確認
        all_disasters = list(db.collection('disasters').limit(10).stream())
        
        debug_info = {
            "total_documents_sampled": len(all_disasters),
            "sample_documents": []
        }
        
        for i, doc in enumerate(all_disasters[:3]):
            data = doc.to_dict()
            sample_doc = {
                "document_id": doc.id,
                "keys": list(data.keys()),
                "detected_at": str(data.get('detected_at', 'NOT_FOUND')),
                "detected_at_type": str(type(data.get('detected_at', None))),
                "created_at": str(data.get('created_at', 'NOT_FOUND')),
                "timestamp": str(data.get('timestamp', 'NOT_FOUND')),
                "has_detected_at_field": 'detected_at' in data,
                "sample_data": {k: str(v)[:100] for k, v in data.items() if k in ['title', 'type', 'severity', 'is_active']}
            }
            debug_info["sample_documents"].append(sample_doc)
        
        # フィルタなしクエリのテスト
        unfiltered_disasters = list(db.collection('disasters').limit(5).stream())
        debug_info["unfiltered_count"] = len(unfiltered_disasters)
        
        return debug_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"デバッグ情報取得エラー: {str(e)}")