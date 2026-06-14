from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.responses import failure_response, success_response
from src.repository.catalog_repository import ClassificationRepository
from src.service.catalog_service import ClassificationService

router = APIRouter(prefix="/classification", tags=["classification"])


@router.get("")
def list_classification_nodes(
    cnstwk_div_cd: str = Query(description="Work division code"),
    parent_code: str | None = Query(
        default=None,
        description="Parent classification code; omit for level-1 nodes",
    ),
    parent_level: int | None = Query(
        default=None,
        ge=1,
        le=5,
        description="Disambiguate parent_code when needed",
    ),
    session: Session = Depends(get_db_session),
):
    service = ClassificationService(ClassificationRepository(session))
    try:
        data = service.list_nodes(
            cnstwk_div_cd=cnstwk_div_cd,
            parent_code=parent_code,
            parent_level=parent_level,
        )
    except LookupError as exc:
        return failure_response(str(exc))
    return success_response(data.model_dump(mode="json"))
