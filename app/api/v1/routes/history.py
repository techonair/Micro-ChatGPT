from fastapi import APIRouter, Depends, Query

from app.api.deps import get_history_service
from app.schemas.common import ApiResponse, ok
from app.schemas.history import HistoryResponse
from app.services.history_service import HistoryService

router = APIRouter(tags=["history"])


@router.get("/history/{user_id}", response_model=ApiResponse[HistoryResponse])
async def history(
    user_id: str,
    session_id: str | None = Query(default=None),
    service: HistoryService = Depends(get_history_service),
) -> ApiResponse[HistoryResponse]:
    result = await service.get_history(user_id=user_id, session_id=session_id)
    return ok(result)
