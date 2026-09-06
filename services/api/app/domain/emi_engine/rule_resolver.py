from typing import List, Dict
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import EmiPlanRule as EmiPlanRuleModel
from app.domain.emi_engine.models import EmiPlanRule


async def resolve_rules_for_product(
    db: AsyncSession,
    product_id: str,
    brand_id: str,
    category_id: str,
) -> List[EmiPlanRule]:
    """
    Fetches rules scoped to this product. Priority: product > brand > category > global.
    For each tenure bucket, only the most specific matching rule is chosen.
    """
    stmt = select(EmiPlanRuleModel).where(
        or_(
            EmiPlanRuleModel.product_id == product_id,
            EmiPlanRuleModel.brand_id == brand_id,
            EmiPlanRuleModel.category_id == category_id,
            and_(
                EmiPlanRuleModel.product_id.is_(None),
                EmiPlanRuleModel.brand_id.is_(None),
                EmiPlanRuleModel.category_id.is_(None),
            ),
        )
    )
    result = await db.execute(stmt)
    all_rules = result.scalars().all()

    PRIORITY = {"product": 0, "brand": 1, "category": 2, "global": 3}

    def scope_priority(rule: EmiPlanRuleModel) -> int:
        if rule.product_id:
            return PRIORITY["product"]
        if rule.brand_id:
            return PRIORITY["brand"]
        if rule.category_id:
            return PRIORITY["category"]
        return PRIORITY["global"]

    tenure_best: Dict[int, EmiPlanRuleModel] = {}
    for rule in all_rules:
        t = rule.tenure_months
        if t not in tenure_best or scope_priority(rule) < scope_priority(tenure_best[t]):
            tenure_best[t] = rule

    return [
        EmiPlanRule(
            tenure_months=r.tenure_months,
            interest_rate_bps=r.interest_rate_bps,
            min_amount_paisa=r.min_amount_paisa,
            max_amount_paisa=r.max_amount_paisa,
        )
        for r in sorted(tenure_best.values(), key=lambda r: r.tenure_months)
    ]
