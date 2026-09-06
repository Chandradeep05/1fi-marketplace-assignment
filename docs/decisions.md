# 1Fi Marketplace — Architecture Decision Records (ADRs)

This document records the canonical architectural and domain decisions governing the 1Fi Marketplace implementation.

---

## ADR-001: Quote Storage Authority & Immutability
- **Status:** Accepted
- **Context:** Quotes expire after 10 minutes. Both Redis and PostgreSQL are available.
- **Decision:** PostgreSQL is the durable, authoritative source of truth. The `expires_at` column in PostgreSQL is authoritative. Redis is used as an active index / cache for low-latency pre-checks, but any checkout intent creation validates `expires_at > now()` directly against PostgreSQL. Quote immutability is strictly enforced by service/API design: quotes have no update endpoints or mutation workflows after creation.
- **Consequences:** If Redis restarts, loses keys, or evicts data, quote validity and financial correctness remain uncompromised. Administrative database access is not restricted by triggers.

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

## ADR-008: Checkout Intent Inventory Boundary & Quote Reuse
- **Status:** Accepted
- **Context:** When creating a checkout intent, variant availability is re-validated with row-level locking (`with_for_update()`).
- **Decision:** Checkout intent records user commitment and plan selection. It does not perform a hard inventory decrement or locking reservation, because payment settlement and merchant fulfillment are external integration boundaries. Furthermore, quotes are immutable 10-minute frozen price proposals and are not single-use; separate checkout submissions with distinct idempotency keys referencing the same quote are permitted.
- **Consequences:** Closes the TOCTOU availability staleness race. Full physical stock decrement is deferred to merchant fulfillment integrations.

---

## ADR-009: Eligibility Filtering on Total Repayment Obligation
- **Status:** Accepted
- **Context:** The customer has an available credit line limit (e.g. ₹1,50,000).
- **Decision:** Plans whose `total_payable_paisa` exceeds `available_limit_paisa` are filtered out of the quote. If all plans exceed the limit, the quote returns an empty plan set with reason `EmptyReason.INSUFFICIENT_LIMIT` (resulting in `422 INSUFFICIENT_LIMIT`). If no configured rules match the amount, it returns `EmptyReason.NO_ELIGIBLE_RULES` (resulting in `422 NO_ELIGIBLE_RULES`).
- **Consequences:** In this reference implementation, eligibility evaluates total repayment obligation (`total_payable_paisa <= available_limit_paisa`) rather than principal exposure alone, ensuring borrower debt-service affordability across the entire tenure. This represents a reference-product policy rather than an assertion of universal lending underwriting methodology.

---

## ADR-010: Deterministic Commercial Offer Precedence
- **Status:** Accepted
- **Context:** Multiple commercial promotions (offers/cashback) may match a product concurrently across product, category, and global scopes.
- **Decision:** Commercial offers are resolved with strict deterministic precedence:
  1. Scope specificity: `Product-specific (0) > Category-specific (1) > Global active (2)`
  2. Highest `cashback_paisa DESC` within the winning scope
  3. Most recently launched `valid_from DESC`
  4. UUID `id ASC` deterministic tie-breaker
- **Consequences:** Guarantees that specific merchant product concessions always override general category discounts, with completely predictable tie-breaking.

---

## ADR-011: Edge Rate-Limit Availability Strategy
- **Status:** Accepted
- **Context:** Distributed sliding-window rate limiters use Redis. In the event of a Redis connectivity outage or restart, requests must be handled predictably.
- **Decision:** The rate limiter fails open for edge availability: when Redis is unreachable, a structured warning log is emitted and requests are permitted to proceed.
- **Consequences:** Prioritizes system availability over strict abuse prevention during infrastructure hiccups in this reference implementation. Production hardening would incorporate in-process token buckets as secondary fallback.
