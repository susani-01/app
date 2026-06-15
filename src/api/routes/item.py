from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.responses import failure_response, success_response
from src.repository.catalog_repository import ItemRepository, ItemSearchFilters
from src.service.catalog_service import ItemService

router = APIRouter(prefix="/api/v1/items", tags=["items"])


@router.get("")
def search_items(
    cnstwk_div_cd: str | None = Query(default=None, description="Work division code"),
    lvl1_code: str | None = Query(default=None),
    lvl2_code: str | None = Query(default=None),
    lvl3_code: str | None = Query(default=None),
    lvl4_code: str | None = Query(default=None),
    lvl5_code: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Keyword search on item name"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db_session),
):
    service = ItemService(ItemRepository(session))
    filters = ItemSearchFilters(
        cnstwk_div_cd=cnstwk_div_cd,
        lvl1_code=lvl1_code,
        lvl2_code=lvl2_code,
        lvl3_code=lvl3_code,
        lvl4_code=lvl4_code,
        lvl5_code=lvl5_code,
        keyword=q,
        page=page,
        size=size,
    )
    try:
        data = service.search_items(filters)
    except ValueError as exc:
        return failure_response(str(exc))
    return success_response(data.model_dump(mode="json"))


@router.get("/{id}")
def get_item(
    id: str,
    session: Session = Depends(get_db_session),
):
    service = ItemService(ItemRepository(session))
    item = service.get_item(id)
    if item is None:
        return failure_response(f"Item not found: {id}")
    return success_response(item.model_dump(mode="json"))
