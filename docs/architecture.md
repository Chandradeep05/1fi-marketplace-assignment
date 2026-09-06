# 1Fi Marketplace — Architecture Document

## System Overview

1Fi Marketplace is an in-app e-commerce shopping experience enabling users to deploy their pre-approved, mutual-fund-backed credit line against high-value consumer electronics and retail goods on flexible EMI terms.

---

## Domain Architecture

```
Marketplace Domain
├── Catalogue Service
│   ├── Products & Variant resolution
│   ├── Categories & Brands
│   └── Rich attributes (storage, color, specs)
│
├── Pricing & Commercial Rules Service
│   ├── Base prices & MRP tracking
│   ├── Instant financing cashback (ADR-003)
│   └── Net financing principal computation
│
├── EMI Calculation Engine (Stateless, Pure)
│   ├── Reducing-balance amortization
│   ├── Multi-tier tenures (3, 6, 12, 24, 36, 60 months)
│   ├── Exact integer paisa reconciliation (monthly * (n-1) + final == total)
│   ├── Uneven remainder absorption for odd tenures
│   └── Scope-priority rules (product > brand > category > global)
│
├── Eligibility Gateway (Protocol Boundary)
│   ├── Customer available credit limit checks
│   ├── Total obligation affordability filtering (ADR-009)
│   └── Insufficient limit error handling
│
└── Transactional Quote & Intent Service
    ├── 10-minute immutable frozen quotes (PostgreSQL authoritative)
    ├── Redis TTL index & fast lookup
    └── Idempotent checkout intent generation (SHA-256 payload hashing)
```

---

## Data Flow: The Server-Owned Quote Lifecycle

1. **Browsing:** Mobile client requests products (`GET /marketplace/products`) and filters by category or debounced search query.
2. **Product Selection:** User views Product Detail (`GET /marketplace/products/{id}`).
3. **Variant Selection:** User toggles variant (e.g. 256GB Black).
4. **Quote Request:** Client initiates `POST /marketplace/quotes` with `{ product_id, variant_id }`.
   - The client **never calculates or submits a price**.
   - Server validates variant availability.
   - Server applies active cashback.
   - Server fetches available credit limit.
   - Server computes eligible EMI plans.
   - Server records an immutable quote row in PostgreSQL with `expires_at = now() + 10m` and caches active status in Redis.
5. **EMI Selection:** Mobile client renders the frozen quote plans. The user selects a `plan_id` (e.g. `36m`).
6. **Checkout Intent:** User taps Proceed → reviews order summary → taps "Confirm & Proceed".
   - Client sends `POST /marketplace/checkout-intents` with `quote_id`, `plan_id`, and `Idempotency-Key`.
   - Server verifies:
     1. `Idempotency-Key` has not been used with a different payload.
     2. Quote has not expired (`expires_at > now()`).
     3. `plan_id` belongs to the frozen quote.
     4. Product variant is still available.
   - Server generates `intent_id` (`ci_...`) and commits to PostgreSQL.
   - Replaying with the same key returns the existing intent without creating duplicates.
