from __future__ import annotations

import math

from src.api.schemas import (
    ClassificationLevelResponse,
    ClassificationListData,
    ClassificationNodeResponse,
    ItemListData,
    ItemResponse,
    PaginationMeta,
    PriceResponse,
    WorkDivisionResponse,
)
from src.db.models import ClassificationNode, MarketPrice, QuantityItem
from src.repository.catalog_repository import (
    ClassificationRepository,
    ItemRepository,
    ItemSearchFilters,
)


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def search_items(self, filters: ItemSearchFilters) -> ItemListData:
        if filters.page < 1:
            raise ValueError("page must be >= 1")
        if filters.size < 1 or filters.size > 100:
            raise ValueError("size must be between 1 and 100")

        total = self._repository.count(filters)
        items = self._repository.search(filters)
        classification_map = self._repository.get_classification_nodes_for_items(items)
        total_pages = math.ceil(total / filters.size) if total else 0

        return ItemListData(
            items=[
                self._to_item_response(item, classification_map.get(item.qty_calc_ctycl_cd, []))
                for item in items
            ],
            pagination=PaginationMeta(
                page=filters.page,
                size=filters.size,
                total=total,
                total_pages=total_pages,
            ),
        )

    def get_item(self, qty_calc_ctycl_cd: str) -> ItemResponse | None:
        item = self._repository.get_by_code(qty_calc_ctycl_cd)
        if item is None:
            return None
        nodes = self._repository.get_classification_nodes_for_item(item)
        return self._to_item_response(item, nodes)

    def _to_item_response(
        self,
        item: QuantityItem,
        nodes: list[ClassificationNode],
    ) -> ItemResponse:
        return ItemResponse(
            qty_calc_ctycl_cd=item.qty_calc_ctycl_cd,
            name=item.name,
            spec=item.spec,
            unit=item.raw_unit,
            unit_code=item.unit.code if item.unit else None,
            cnstwk_div_cd=item.work_division_cd,
            cnstwk_div_nm=item.work_division.name if item.work_division else None,
            classification=[
                ClassificationLevelResponse(level=node.level, code=node.code, name=node.name)
                for node in nodes
            ],
            price=self._to_price_response(item.market_price),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _to_price_response(price: MarketPrice | None) -> PriceResponse | None:
        if price is None:
            return None
        return PriceResponse(
            product_name=price.product_name,
            spec=price.spec,
            unit=price.raw_unit,
            material_cost=price.material_cost,
            labor_cost=price.labor_cost,
            expense_cost=price.expense_cost,
            published_date=price.published_date,
            apply_condition=price.apply_condition,
        )


class ClassificationService:
    def __init__(self, repository: ClassificationRepository) -> None:
        self._repository = repository

    def list_work_divisions(self) -> list[WorkDivisionResponse]:
        return [
            WorkDivisionResponse(
                code=division.code,
                name=division.name,
                created_at=division.created_at,
                updated_at=division.updated_at,
            )
            for division in self._repository.list_work_divisions()
        ]

    def list_nodes(
        self,
        cnstwk_div_cd: str,
        parent_code: str | None = None,
        parent_level: int | None = None,
    ) -> ClassificationListData:
        division = self._repository.get_work_division(cnstwk_div_cd)
        if division is None:
            raise LookupError(f"Unknown work division code: {cnstwk_div_cd}")

        if parent_code:
            parent = self._repository.find_node(
                cnstwk_div_cd=cnstwk_div_cd,
                code=parent_code,
                level=parent_level,
            )
            if parent is None:
                raise LookupError(
                    f"Unknown classification code '{parent_code}' for division '{cnstwk_div_cd}'",
                )
            nodes = self._repository.list_child_nodes(parent.id)
        else:
            nodes = self._repository.list_root_nodes(cnstwk_div_cd)

        has_children_map = self._repository.batch_has_children([node.id for node in nodes])
        return ClassificationListData(
            cnstwk_div_cd=cnstwk_div_cd,
            cnstwk_div_nm=division.name,
            parent_code=parent_code,
            nodes=[
                self._to_node_response(node, has_children_map.get(node.id, False))
                for node in nodes
            ],
        )

    @staticmethod
    def _to_node_response(
        node: ClassificationNode,
        has_children: bool,
    ) -> ClassificationNodeResponse:
        return ClassificationNodeResponse(
            id=node.id,
            level=node.level,
            code=node.code,
            name=node.name,
            description=node.description,
            has_children=has_children,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
