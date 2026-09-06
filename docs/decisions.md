# 1Fi Marketplace — Architecture Decision Records (ADRs)

This document records the key architectural and domain decisions governing the 1Fi Marketplace implementation.

---

## ADR-001: Quote Storage Authority
- **Status:** Accepted
- **Context:** Quotes expire after 10 minutes. Both Redis and PostgreSQL are available.
- **Decision:** PostgreSQL is the durable, authoritative source of truth. The `expires_at` column in PostgreSQL is authoritative. Redis is used as an active index / cache for low-latency pre-checks, but any checkout intent creation validates `expires_at > now()` directly against PostgreSQL.
- **Consequences:** If Redis restarts, loses keys, or evicts data, quote validity and financial correctness remain uncompromised.

---

## ADR-002: Recommended Plan Selection Logic
- **Status:** Accepted
- **Context:** The system needs a deterministic, objective rule to flag a plan as `recommended: true`.
- **Decision:** The longest no-cost tenure plan is marked `recommended: true`. If no no-cost plan exists, the shortest tenure plan is marked `recommended: true`.
- **Consequences:** Maximizes customer affordability without incurring interest. This is a configurable commercial policy.

---

## ADR-003: Cashback Treated as Immediate Financing Adjustment
- **Status:** Accepted
- **Context:** Real 1Fi listings display "Cashback ₹8,000" alongside an EMI tenure where the total payable reflects the net price (`₹1,34,900 - ₹8,00,000 = ₹1,26,900`).
- **Decision:** Cashback is modeled as an upfront discount to the financed principal:
  `financing_principal_paisa = product_price_paisa - cashback_paisa`
  Interest and EMI installments are computed against `financing_principal_paisa`.
- **Consequences:** Aligns with the app's visual presentation. If a future partner lender requires lending against full MSRP with cashback disbursed post-settlement, only the domain pricing service formula requires updating.

---

## ADR-004: Processing Fee Excluded from Initial Scope
- **Status:** Accepted
- **Context:** PRD v1 mentioned a processing fee, but live 1fi.in product listings show zero processing fees on mutual fund credit line purchases.
- **Decision:** `processing_fee_paisa` is omitted from the initial contract.
- **Consequences:** Avoids fabricating arbitrary fees not observed in live 1Fi reference surfaces.

---

## ADR-005: Idempotency Key Scoping
- **Status:** Accepted
- **Context:** Checkout intent creation requires an `Idempotency-Key` header.
- **Decision:** For this reference implementation without user login, `idempotency_key` is globally unique in `checkout_intents`.
- **Consequences:** Marked with `TODO(auth)`: once real customer authentication is added, the unique constraint must become `UNIQUE(customer_id, idempotency_key)`.

---

## ADR-006: Identifiers Strategy
- **Status:** Accepted
- **Context:** Consistent ID format across entities.
- **Decision:**
  - Categories, Brands, Products: URL-safe slug strings (e.g. `smartphones`, `apple`, `iphone-17-pro`).
  - Variants, Images, Offers, Rules: UUID v4.
  - Quotes: `qt_` prefix + ULID.
  - Checkout Intents: `ci_` prefix + ULID.
- **Consequences:** Log traces and URLs are readable and clearly distinguishable by entity type.

---

## ADR-007: EMI Tenure Scope Resolution Priority
- **Status:** Accepted
- **Context:** Live 1Fi app screenshots show merchant/brand-level tenure limits (e.g., "Apple Premium Reseller — No-cost EMIs up to 24 months" vs. "Air India — up to 18 months").
- **Decision:** `emi_plan_rules` supports scope dimensions: `product_id`, `brand_id`, `category_id`, and global (all NULL). Priority resolution order:
  `product > brand > category > global`
  For any tenure bucket (e.g. 24m), the most specific matching rule wins.
- **Consequences:** Faithfully represents merchant-specific promotion rules without hardcoding them in client code.

---

## ADR-008: Checkout Intent Creation Does Not Reserve Inventory
- **Status:** Accepted
- **Context:** When creating a checkout intent, variant availability is re-validated.
- **Decision:** Checkout intent records user commitment and plan selection. It does not perform a hard inventory decrement or locking reservation, because payment settlement and merchant fulfillment are integration boundaries.
- **Consequences:** Availability is verified at intent creation time (`available = true`), but full stock reservation remains deferred to fulfillment.

---

## ADR-009: Eligibility Filtering on Total Payable Amount
- **Status:** Accepted
- **Context:** The customer has an available credit line limit (e.g. ₹1,50,000).
- **Decision:** Plans whose `total_payable_paisa` exceeds `available_limit_paisa` are filtered out of the quote. If all plans exceed the limit, the quote returns an empty plan set with reason `EmptyReason.INSUFFICIENT_LIMIT` (resulting in `422 INSUFFICIENT_LIMIT`).
- **Consequences:** Prevents users from being quoted plans they cannot service under their approved credit line.
