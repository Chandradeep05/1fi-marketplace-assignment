"""Audit remediation schema updates

Revision ID: 0002_audit_remediation
Revises: 0001_initial_schema
Create Date: 2026-09-06 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_audit_remediation'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_test_fixture to products
    op.add_column(
        'products',
        sa.Column('is_test_fixture', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )

    # 2. Drop discount_pct_bps from offers
    op.drop_column('offers', 'discount_pct_bps')

    # 3. Add offer scope integrity check constraint
    op.create_check_constraint(
        'chk_offer_scope',
        'offers',
        """
        (product_id IS NOT NULL AND category_id IS NULL) OR
        (product_id IS NULL AND category_id IS NOT NULL) OR
        (product_id IS NULL AND category_id IS NULL)
        """
    )

    # 4. Add EMI rule no-cost consistency check constraint
    op.create_check_constraint(
        'chk_emi_rule_no_cost_consistency',
        'emi_plan_rules',
        "(interest_rate_bps = 0 AND is_no_cost = TRUE) OR (interest_rate_bps > 0 AND is_no_cost = FALSE)"
    )


def downgrade() -> None:
    op.drop_constraint('chk_emi_rule_no_cost_consistency', 'emi_plan_rules', type_='check')
    op.drop_constraint('chk_offer_scope', 'offers', type_='check')
    op.add_column('offers', sa.Column('discount_pct_bps', sa.Integer(), nullable=False, server_default='0'))
    op.drop_column('products', 'is_test_fixture')
