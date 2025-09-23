from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from typing import List
import logging

from models.public_api import FAQResponse, FAQQuestionRequest, FAQAnswerResponse
from services.faq_service import faq_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public/faq", tags=["FAQ"])

@router.get(
    "/{disaster_id}",
    response_model=FAQResponse,
    summary="災害特化FAQ取得",
    description="指定された災害IDに関連するFAQを取得します。"
)
async def get_disaster_faqs(
    disaster_id: str = Path(..., description="災害ID")
) -> FAQResponse:
    """災害特化FAQを取得"""
    try:
        logger.info(f"Getting FAQs for disaster: {disaster_id}")
        
        faq_response = await faq_service.get_faqs_by_disaster(disaster_id)
        
        if not faq_response:
            raise HTTPException(
                status_code=404,
                detail=f"災害ID {disaster_id} に関連するFAQが見つかりません"
            )
        
        logger.info(f"Successfully retrieved {len(faq_response.faqs)} FAQs for disaster {disaster_id}")
        return faq_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting FAQs for disaster {disaster_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="FAQ取得中にエラーが発生しました"
        )

@router.post(
    "/{disaster_id}/ask",
    response_model=FAQAnswerResponse,
    summary="災害関連質問",
    description="指定された災害に関する質問をAIに投げかけ、回答を取得します。"
)
async def ask_disaster_question(
    disaster_id: str = Path(..., description="災害ID"),
    question_request: FAQQuestionRequest = Body(..., description="質問リクエスト")
) -> FAQAnswerResponse:
    """災害に関する質問をAIに投げかける"""
    try:
        logger.info(f"Processing question for disaster {disaster_id}: {question_request.question}")
        
        if not question_request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="質問文が空です"
            )
        
        answer_response = await faq_service.answer_question(
            disaster_id, 
            question_request.question
        )
        
        logger.info(f"Successfully generated answer for disaster {disaster_id}")
        return answer_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question for disaster {disaster_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="質問回答中にエラーが発生しました"
        )

@router.get(
    "/active",
    response_model=List[FAQResponse],
    summary="アクティブ災害FAQ一覧",
    description="現在アクティブな災害に関連するFAQ一覧を取得します。"
)
async def get_active_faqs() -> List[FAQResponse]:
    """アクティブな災害のFAQ一覧を取得"""
    try:
        logger.info("Getting FAQs for all active disasters")
        
        # DisasterServiceを使ってアクティブな災害を取得
        from services.disaster_service import DisasterService
        
        disaster_service_instance = DisasterService()
        
        # アクティブな災害を取得（タプル形式で返される）
        disasters_data, total_count = await disaster_service_instance.get_disasters(
            is_active=True,
            limit=10  # 最大10件
        )
        
        active_faqs = []
        for disaster in disasters_data:
            disaster_id = disaster.get('id')
            if disaster_id:
                faq_response = await faq_service.get_faqs_by_disaster(disaster_id)
                if faq_response:
                    active_faqs.append(faq_response)
        
        logger.info(f"Successfully retrieved FAQs for {len(active_faqs)} active disasters")
        return active_faqs
        
    except Exception as e:
        logger.error(f"Error getting active FAQs: {e}")
        raise HTTPException(
            status_code=500,
            detail="アクティブFAQ取得中にエラーが発生しました"
        )