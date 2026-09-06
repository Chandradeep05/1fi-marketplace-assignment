"""Initial marketplace schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-06 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Categories
    op.create_table(
        'categories',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # Brands
    op.create_table(
        'brands',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
    )

    # Products
    op.create_table(
        'products',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('brand_id', sa.String(), sa.ForeignKey('brands.id'), nullable=False),
        sa.Column('category_id', sa.String(), sa.ForeignKey('categories.id'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('base_price_paisa', sa.Integer(), nullable=False),
        sa.Column('mrp_paisa', sa.Integer(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('base_price_paisa > 0', name='chk_product_base_price_positive'),
        sa.CheckConstraint('mrp_paisa IS NULL OR mrp_paisa >= base_price_paisa', name='chk_product_mrp_gte_base'),
    )
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_brand', 'products', ['brand_id'])
    op.create_index('idx_products_created_id', 'products', ['created_at', 'id'])

    # Product Images
    op.create_table(
        'product_images',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # Product Variants
    op.create_table(
        'product_variants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attributes', JSONB, nullable=False),
        sa.Column('price_paisa', sa.Integer(), nullable=False),
        sa.Column('available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('price_paisa > 0', name='chk_variant_price_positive'),
    )
    op.create_index('idx_variants_product', 'product_variants', ['product_id'])

    # Offers
    op.create_table(
        'offers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('category_id', sa.String(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('cashback_paisa', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discount_pct_bps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('cashback_paisa >= 0', name='chk_offer_cashback_non_negative'),
    )

    # EMI Plan Rules
    op.create_table(
        'emi_plan_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenure_months', sa.Integer(), nullable=False),
        sa.Column('interest_rate_bps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_amount_paisa', sa.Integer(), nullable=False),
        sa.Column('max_amount_paisa', sa.Integer(), nullable=True),
        sa.Column('is_no_cost', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('brand_id', sa.String(), sa.ForeignKey('brands.id'), nullable=True),
        sa.Column('category_id', sa.String(), sa.ForeignKey('categories.id'), nullable=True),
        sa.CheckConstraint(
            """
            (product_id IS NOT NULL AND brand_id IS NULL AND category_id IS NULL) OR
            (product_id IS NULL AND brand_id IS NOT NULL AND category_id IS NULL) OR
            (product_id IS NULL AND brand_id IS NULL AND category_id IS NOT NULL) OR
            (product_id IS NULL AND brand_id IS NULL AND category_id IS NULL)
            """,
            name='chk_single_scope'
        ),
        sa.CheckConstraint('tenure_months > 0', name='chk_emi_rule_tenure_positive'),
        sa.CheckConstraint('interest_rate_bps >= 0', name='chk_emi_rule_interest_non_negative'),
        sa.CheckConstraint('min_amount_paisa >= 0', name='chk_emi_rule_min_amount_non_negative'),
        sa.CheckConstraint('max_amount_paisa IS NULL OR max_amount_paisa >= min_amount_paisa', name='chk_emi_rule_max_gte_min'),
    )
    op.create_index('idx_emi_rules_scope', 'emi_plan_rules', ['product_id', 'brand_id', 'category_id'])

    # Quotes
    op.create_table(
        'quotes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('variant_id', UUID(as_uuid=True), sa.ForeignKey('product_variants.id'), nullable=False),
        sa.Column('price_paisa', sa.Integer(), nullable=False),
        sa.Column('cashback_paisa', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('plans_json', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('price_paisa > 0', name='chk_quote_price_positive'),
        sa.CheckConstraint('cashback_paisa >= 0 AND cashback_paisa < price_paisa', name='chk_quote_cashback_valid'),
    )
    op.create_index('idx_quotes_expires_at', 'quotes', ['expires_at'])

    # Checkout Intents
    op.create_table(
        'checkout_intents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('quote_id', sa.String(), sa.ForeignKey('quotes.id'), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='received'),
        sa.Column('idempotency_key', sa.String(), unique=True, nullable=False),
        sa.Column('request_hash', sa.String(), nullable=False),
        sa.Column('response_json', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('received', 'processing', 'completed', 'failed')", name='chk_checkout_intent_status')
    )
    op.create_index('idx_intents_quote', 'checkout_intents', ['quote_id'])


def downgrade() -> None:
    op.drop_table('checkout_intents')
    op.drop_table('quotes')
    op.drop_table('emi_plan_rules')
    op.drop_table('offers')
    op.drop_table('product_variants')
    op.drop_table('product_images')
    op.drop_table('products')
    op.drop_table('brands')
    op.drop_table('categories')
