from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginationMeta(ApiModel):
    page: int
    size: int
    total: int
    total_pages: int


class ApiResponse(ApiModel, Generic[T]):
    status: str
    data: T | None = None
    message: str | None = None


class PriceResponse(ApiModel):
    product_name: str | None = None
    spec: str | None = None
    unit: str | None = None
    material_cost: Decimal
    labor_cost: Decimal
    expense_cost: Decimal
    published_date: date | None = None
    apply_condition: str | None = None


class ClassificationLevelResponse(ApiModel):
    level: int
    code: str
    name: str


class ItemResponse(ApiModel):
    qty_calc_ctycl_cd: str
    name: str
    spec: str | None = None
    unit: str | None = None
    unit_code: str | None = None
    cnstwk_div_cd: str
    cnstwk_div_nm: str | None = None
    classification: list[ClassificationLevelResponse] = Field(default_factory=list)
    price: PriceResponse | None = None
    created_at: datetime
    updated_at: datetime


class ItemListData(ApiModel):
    items: list[ItemResponse]
    pagination: PaginationMeta


class ClassificationNodeResponse(ApiModel):
    id: int
    level: int
    code: str
    name: str
    description: str | None = None
    has_children: bool
    created_at: datetime
    updated_at: datetime


class ClassificationListData(ApiModel):
    cnstwk_div_cd: str
    cnstwk_div_nm: str | None = None
    parent_code: str | None = None
    nodes: list[ClassificationNodeResponse]


class WorkDivisionResponse(ApiModel):
    code: str
    name: str
    created_at: datetime
    updated_at: datetime
