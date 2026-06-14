from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.db.models import ClassificationNode, MarketPrice, QuantityItem, Unit, WorkDivision


@dataclass
class ItemSearchFilters:
    cnstwk_div_cd: str | None = None
    lvl1_code: str | None = None
    lvl2_code: str | None = None
    lvl3_code: str | None = None
    lvl4_code: str | None = None
    lvl5_code: str | None = None
    keyword: str | None = None
    page: int = 1
    size: int = 20


class ItemRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[QuantityItem]]:
        return (
            select(QuantityItem)
            .options(
                joinedload(QuantityItem.work_division),
                joinedload(QuantityItem.unit),
                joinedload(QuantityItem.market_price).joinedload(MarketPrice.unit),
            )
            .order_by(QuantityItem.qty_calc_ctycl_cd)
        )

    def _apply_filters(
        self,
        query: Select[tuple[QuantityItem]],
        filters: ItemSearchFilters,
    ) -> Select[tuple[QuantityItem]]:
        if filters.cnstwk_div_cd:
            query = query.where(QuantityItem.work_division_cd == filters.cnstwk_div_cd)
        if filters.lvl1_code:
            query = query.where(QuantityItem.lvl1_code == filters.lvl1_code)
        if filters.lvl2_code:
            query = query.where(QuantityItem.lvl2_code == filters.lvl2_code)
        if filters.lvl3_code:
            query = query.where(QuantityItem.lvl3_code == filters.lvl3_code)
        if filters.lvl4_code:
            query = query.where(QuantityItem.lvl4_code == filters.lvl4_code)
        if filters.lvl5_code:
            query = query.where(QuantityItem.lvl5_code == filters.lvl5_code)
        if filters.keyword:
            escaped = (
                filters.keyword.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            query = query.where(QuantityItem.name.ilike(f"%{escaped}%", escape="\\"))
        return query

    def count(self, filters: ItemSearchFilters) -> int:
        query = select(func.count()).select_from(QuantityItem)
        if filters.cnstwk_div_cd:
            query = query.where(QuantityItem.work_division_cd == filters.cnstwk_div_cd)
        if filters.lvl1_code:
            query = query.where(QuantityItem.lvl1_code == filters.lvl1_code)
        if filters.lvl2_code:
            query = query.where(QuantityItem.lvl2_code == filters.lvl2_code)
        if filters.lvl3_code:
            query = query.where(QuantityItem.lvl3_code == filters.lvl3_code)
        if filters.lvl4_code:
            query = query.where(QuantityItem.lvl4_code == filters.lvl4_code)
        if filters.lvl5_code:
            query = query.where(QuantityItem.lvl5_code == filters.lvl5_code)
        if filters.keyword:
            escaped = (
                filters.keyword.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            query = query.where(QuantityItem.name.ilike(f"%{escaped}%", escape="\\"))
        return self._session.scalar(query) or 0

    def search(self, filters: ItemSearchFilters) -> list[QuantityItem]:
        offset = (filters.page - 1) * filters.size
        query = self._apply_filters(self._base_query(), filters)
        return list(self._session.scalars(query.offset(offset).limit(filters.size)).unique())

    def get_by_code(self, qty_calc_ctycl_cd: str) -> QuantityItem | None:
        query = self._base_query().where(QuantityItem.qty_calc_ctycl_cd == qty_calc_ctycl_cd)
        return self._session.scalars(query).unique().first()

    def get_classification_nodes_for_items(
        self,
        items: list[QuantityItem],
    ) -> dict[str, list[ClassificationNode]]:
        if not items:
            return {}

        node_keys: set[tuple[str, int, str]] = set()
        item_level_codes: dict[str, list[tuple[int, str]]] = {}

        for item in items:
            level_codes: list[tuple[int, str]] = []
            for level in range(1, 6):
                code = getattr(item, f"lvl{level}_code")
                if code:
                    node_keys.add((item.work_division_cd, level, code))
                    level_codes.append((level, code))
            item_level_codes[item.qty_calc_ctycl_cd] = level_codes

        if not node_keys:
            return {item.qty_calc_ctycl_cd: [] for item in items}

        conditions = [
            and_(
                ClassificationNode.work_division_cd == division,
                ClassificationNode.level == level,
                ClassificationNode.code == code,
            )
            for division, level, code in node_keys
        ]
        nodes = list(self._session.scalars(select(ClassificationNode).where(or_(*conditions))))
        node_map = {
            (node.work_division_cd, node.level, node.code): node for node in nodes
        }

        result: dict[str, list[ClassificationNode]] = {}
        for item in items:
            path: list[ClassificationNode] = []
            for level, code in item_level_codes.get(item.qty_calc_ctycl_cd, []):
                node = node_map.get((item.work_division_cd, level, code))
                if node:
                    path.append(node)
            result[item.qty_calc_ctycl_cd] = path
        return result

    def get_classification_nodes_for_item(
        self,
        item: QuantityItem,
    ) -> list[ClassificationNode]:
        return self.get_classification_nodes_for_items([item]).get(item.qty_calc_ctycl_cd, [])


class ClassificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_work_division(self, code: str) -> WorkDivision | None:
        return self._session.get(WorkDivision, code)

    def list_work_divisions(self) -> list[WorkDivision]:
        return list(self._session.scalars(select(WorkDivision).order_by(WorkDivision.code)))

    def find_node(
        self,
        cnstwk_div_cd: str,
        code: str,
        level: int | None = None,
    ) -> ClassificationNode | None:
        query = select(ClassificationNode).where(
            ClassificationNode.work_division_cd == cnstwk_div_cd,
            ClassificationNode.code == code,
        )
        if level is not None:
            query = query.where(ClassificationNode.level == level)
        return self._session.scalars(query.order_by(ClassificationNode.level.desc())).first()

    def list_root_nodes(self, cnstwk_div_cd: str) -> list[ClassificationNode]:
        query = (
            select(ClassificationNode)
            .where(
                ClassificationNode.work_division_cd == cnstwk_div_cd,
                ClassificationNode.level == 1,
            )
            .order_by(ClassificationNode.code)
        )
        return list(self._session.scalars(query))

    def list_child_nodes(self, parent_id: int) -> list[ClassificationNode]:
        query = (
            select(ClassificationNode)
            .where(ClassificationNode.parent_id == parent_id)
            .order_by(ClassificationNode.code)
        )
        return list(self._session.scalars(query))

    def has_children(self, node_id: int) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(ClassificationNode)
            .where(ClassificationNode.parent_id == node_id),
        )
        return bool(count)

    def batch_has_children(self, node_ids: list[int]) -> dict[int, bool]:
        if not node_ids:
            return {}
        rows = self._session.execute(
            select(ClassificationNode.parent_id, func.count())
            .where(ClassificationNode.parent_id.in_(node_ids))
            .group_by(ClassificationNode.parent_id),
        )
        child_counts = {parent_id: count for parent_id, count in rows}
        return {node_id: child_counts.get(node_id, 0) > 0 for node_id in node_ids}
