from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.responses import failure_response, success_response
from src.db.models import ClassificationNode, MarketPrice, QuantityItem, WorkDivision
from src.repository.catalog_repository import ClassificationRepository
from src.service.catalog_service import ClassificationService

router = APIRouter(tags=["system"])


@router.get("/health")
def health(session: Session = Depends(get_db_session)):
    session.execute(text("SELECT 1"))
    return success_response({"message": "ok"})


@router.get("/ready")
def ready(session: Session = Depends(get_db_session)):
    counts = {
        "work_divisions": session.scalar(select(func.count()).select_from(WorkDivision)) or 0,
        "classification_nodes": session.scalar(
            select(func.count()).select_from(ClassificationNode),
        )
        or 0,
        "quantity_items": session.scalar(select(func.count()).select_from(QuantityItem)) or 0,
        "market_prices": session.scalar(select(func.count()).select_from(MarketPrice)) or 0,
    }
    loaded = counts["quantity_items"] > 0
    if loaded:
        return success_response(counts, message="database loaded")
    return failure_response("database empty — run make setup", data=counts)


@router.get("/work_division")
def list_work_divisions(session: Session = Depends(get_db_session)):
    service = ClassificationService(ClassificationRepository(session))
    divisions = service.list_work_divisions()
    return success_response([division.model_dump(mode="json") for division in divisions])
