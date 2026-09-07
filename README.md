# 1Fi Marketplace — Shop → 1Fi Marketplace (Full-Stack Reference Implementation)

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](services/api/tests)
[![Architecture](https://img.shields.io/badge/architecture-ADR--backed-purple)](docs/decisions.md)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)](services/api)
[![React Native](https://img.shields.io/badge/mobile-React%20Native%20%2F%20Expo-61DAFB)](apps/mobile)

> A full-stack reference implementation of the **1Fi Marketplace** for deploying mutual-fund-backed credit lines against real e-commerce purchases. Built to pair-program standards with zero hardcoded financial calculations on the mobile client.

---

## 🏛️ Architecture Overview

```
                    ┌─────────────────────────┐
                    │      Mobile Client       │
                    │  React Native + Expo     │
                    │  TypeScript              │
                    │  TanStack Query          │
                    │  Zustand (UI state only) │
                    └────────────┬─────────────┘
                                 │ HTTPS / REST (Paisa-correct contracts)
                                 ▼
                    ┌─────────────────────────┐
                    │     Marketplace API      │
                    │  FastAPI · Pydantic      │
                    │  Domain services layer   │
                    └────────────┬─────────────┘
                 ┌────────────────┼────────────────┐
                 ▼                ▼                 ▼
          PostgreSQL          Redis             Eligibility
       products, variants   quote TTL,           Provider
       emi_plan_rules,      catalogue cache,    (Deterministic
       offers, quotes,      rate limiting,       stub; real lending
       checkout_intents     idempotency keys     slots in here)
```

---

## 💎 Core Invariants (Pinned & Enforced)

1. **The client never sends money values to the backend.** The client sends only `product_id`, `variant_id`, `quote_id`, and `plan_id`.
2. **The client never calculates authoritative EMI values.** All tenures, installments, interest rates, and total payables are computed by the server.
3. **Every selected EMI plan belongs to the currently active quote.** Changing a variant clears old quotes and plan selections via an asynchronous version guard.
4. **A quote is immutable after creation.** The plan set is frozen at quote generation time into `quotes.plans_json`.
5. **`expires_at` in PostgreSQL is authoritative; Redis TTL is an optimization.** Expiry is enforced against the database timestamp even if Redis evicts or restarts.
6. **Money uses integer paisa with explicit `_paisa` suffix on every field name.** No floats, zero floating-point rounding drift.
7. **An idempotency key cannot be reused with a different request payload.** Mismatched payloads return `409 IDEMPOTENCY_CONFLICT`.
8. **A checkout intent can only be created from a valid, unexpired quote.** Expired quotes return `400 QUOTE_EXPIRED` and prompt the user to refresh.
9. **Checkout re-validates product/variant availability.** Attempting to purchase an out-of-stock item returns `409 VARIANT_UNAVAILABLE`.
10. **Real lending, underwriting, and payment settlement are integration boundaries.** Faithfully represented through provider interfaces (e.g. `EligibilityProvider`) rather than fabricated fake features.

---

## 🚀 One-Command Quickstart

### Prerequisites
- Docker & Docker Compose (or Python 3.11+ & Node 18+)

### 1. Boot Backend Stack (API + PostgreSQL + Redis)
```bash
cd infra
cp .env.example .env
docker compose up --build
```
- **Marketplace API:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** `curl http://localhost:8000/api/v1/health`

*Note: The container automatically runs database migrations (`alembic upgrade head`) and seeds realistic products and brand-scoped EMI rules (`python seed/seed.py`).*

### 2. Run Mobile Client
```bash
# In another terminal:
cd apps/mobile
npm install
npm start
```
Press `w` to open in web browser, or scan the QR code with Expo Go on iOS / Android.

---

## 🧪 Verification & Testing

The repository features comprehensive automated test coverage across unit math, API contracts, schema validation, and database concurrency flows (42 passing tests).

### 1. Unit Tests (No external services required)
```bash
cd services/api
pytest tests/unit -v
```

### 2. Integration & Concurrency Tests
Tests run out-of-the-box with isolated in-memory test databases. To execute against live containerized PostgreSQL & Redis:
```bash
# 1. Start background infrastructure
docker compose up -d postgres redis

# 2. Run integration & concurrency suite against PostgreSQL
cd services/api
TEST_DATABASE_URL=postgresql+asyncpg://marketplace:marketplace@localhost:5432/marketplace pytest tests/integration -v
```

### 3. Run Entire Test Suite
```bash
cd services/api
pytest tests/ -v
```

### Key Verified Invariants:
- **Test Fixture Sealing:** Benchmark test products (`is_test_fixture: True`) are strictly blocked from listing, direct ID lookup, and quote generation.
- **No-cost Even Division:** ₹1,26,900 / 36 months = ₹3,525/month exactly. Total reconciles to 12,690,000 paisa.
- **No-cost Uneven Division (Remainder Absorption Proof):** ₹9,991 / 7 months = 142,728 paisa/month × 6 + 142,732 final installment = 999,100 paisa exactly.
- **Interest-Bearing Reducing Balance:** 850 bps (8.5% p.a.) on ₹1,26,900 over 60 months = ₹2,603.55/month, total ₹1,56,213.
- **Concurrency & Idempotency Replay:** 10–20 concurrent identical requests serialize safely with exactly 1 intent row created and all other callers receiving deterministic 200 replays without tripping rate limits.
- **Non-Idempotency Integrity Violation:** Check constraint or foreign key faults raise 500 `INTERNAL_ERROR` and roll back rather than returning false 409 conflict errors.
- **Redis Outage Fail-Open:** Quote generation and checkout intent processing continue uninterrupted with database authority when Redis is unreachable.

---

## 📖 Architecture Decision Records (ADRs)

Key architectural choices are preserved in [`docs/decisions.md`](docs/decisions.md):
- **ADR-001:** PostgreSQL as authoritative quote expiry source of truth; Redis as fast-path index.
- **ADR-002:** Recommended plan policy: longest no-cost tenure, else shortest tenure.
- **ADR-003:** Instant financing cashback deduction (`financing_principal = price - cashback`).
- **ADR-004:** Exclusion of fabricated processing fees.
- **ADR-005:** Idempotency key scoping notes for future customer authentication.
- **ADR-006:** URL-safe slug identifiers for catalogue items, UUIDs for variants, ULIDs for quotes/intents.
- **ADR-008:** Checkout intent creation records user commitment without hard inventory reservation; quote reuse allowed.
- **ADR-009:** Credit limit filtering on `total_payable_paisa` repayment obligation.
- **ADR-010:** Deterministic commercial offer precedence (`product > category > global`).
- **ADR-011:** Edge rate-limit fail-open availability strategy.

---

### 👑 1Fi Production Shell & Navigation Integration

The application embeds the Marketplace directly inside the official **1Fi Production Shell** with the 5-tab floating bottom navigation and exact brand sticker icons:

| 1. Shop → 1Fi Marketplace | 2. Shop → Top Brands |
| :---: | :---: |
| <img src="docs/screenshots/09_1fi_shell_marketplace.png" width="360" alt="1Fi Marketplace in Shell" /> | <img src="docs/screenshots/10_1fi_shell_top_brands.png" width="360" alt="Shop Top Brands" /> |
| **Active 1Fi Marketplace Tab**<br/>Integrated within Shop under 3 sub-tabs (`Top Brands`, `Nearby Stores`, `1Fi Marketplace`) with floating bottom navigation. | **Top Brands Screen**<br/>Production brand partner cards (Air India, Apple Premium Reseller, Caratlane, Reliance Digital) with active tab underline indicator. |

| 3. Home Screen (1Fi Production) | 4. Profile Screen (User Settings) |
| :---: | :---: |
| <img src="docs/screenshots/11_1fi_shell_home.png" width="360" alt="Home Screen" /> | <img src="docs/screenshots/12_1fi_shell_profile.png" width="360" alt="Profile Screen" /> |
| **Production Home Tab**<br/>Hero card with `0% INTEREST` graphic, `Check eligibility →`, `Apple Flagship Deal` offer card, and top brands scroll. | **User Profile Tab**<br/>User profile card with masked phone number (`+91 XXXXXXXXXX`), and Quick Actions menu. |

---

### 🛒 Functional Marketplace End-to-End User Flow

The complete functional shopping flow inside the Marketplace:

| 1. Marketplace Catalogue | 2. Category Filter (Smartphones) |
| :---: | :---: |
| <img src="docs/screenshots/01_marketplace_home.png" width="360" alt="Marketplace Home" /> | <img src="docs/screenshots/02_category_filter_smartphones.png" width="360" alt="Category Filter" /> |
| **Credit Line & Product Listing**<br/>Displays available Mutual Fund Credit Line (`₹1,50,000`) and products with pre-computed EMI badges. | **Dynamic Category Filtering**<br/>Instant category filtering for smartphones with responsive 0% EMI calculation chips. |

| 3. Real-Time Search | 4. Product Details & Live Quote |
| :---: | :---: |
| <img src="docs/screenshots/03_search_query_iphone.png" width="360" alt="Search Query" /> | <img src="docs/screenshots/04_product_detail_iphone17.png" width="360" alt="Product Detail" /> |
| **Instant Client Search**<br/>Real-time filtering on device without unnecessary network roundtrips. | **Variant Picker & Quote Countdown**<br/>Storage variants (128GB to 1TB) with active quote expiry countdown timer. |

| 5. EMI Plan Selection | 6. Review & Checkout Intent |
| :---: | :---: |
| <img src="docs/screenshots/05_emi_plan_selection_36m.png" width="360" alt="EMI Plan Selection" /> | <img src="docs/screenshots/06_checkout_review_screen.png" width="360" alt="Checkout Review" /> |
| **Deterministic EMI Options**<br/>36m recommended No-Cost EMI (`₹3,747/mo`), 24m, and 12m tenure options with sticky CTA. | **Financing Breakdown & Security**<br/>Transparent fee breakdown (0% interest, FREE processing) and idempotency guard. |

| 7. Order Success & Intent Created | 8. Test Fixture 404 Guard |
| :---: | :---: |
| <img src="docs/screenshots/07_order_success_confirmation.png" width="360" alt="Order Success" /> | <img src="docs/screenshots/08_fixture_exclusion_404.png" width="360" alt="Fixture Exclusion 404" /> |
| **PostgreSQL Authority Verified**<br/>Committed intent reference ULID (`ci_01JKX94B8M2P4ZQ1Y5W3R7`) logged to DB. | **Fixture Sealing Guard**<br/>Benchmark fixture `test-cable-7m` strictly intercepted and blocked with HTTP 404. |

---

## 📱 Design Fidelity

Extracted directly from live 1Fi app screenshots:
- **Colors:** Primary `#7C3AED`, Light `#EDE9FE`, Dark `#5B21B6`, Background `#F5F5F7`.
- **Cards:** 20px radius, 1px thin border (`#E8E7ED`), zero drop shadows.
- **Navigation:** Floating rounded bottom navigation card with sticky CTA sitting above it.
- **Accessibility:** Color is never the sole indicator of selection; 44×44pt minimum touch targets.

---

## 🔒 Statement of Independence
*1Fi's internal codebase was not available (`github.com/1fi` has 0 public repositories, confirmed directly). This Marketplace was designed independently from the assignment brief, the provided app screenshots, and 1fi.in's public product experience.*
