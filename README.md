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

To run the automated test suite verifying money math, remainder absorption, and eligibility filters:

```bash
# Run backend test suite
cd services/api
python -m pytest tests/unit/test_emi_calculator.py -v
```

### Verified Test Cases:
- **No-cost Even Division:** ₹1,26,900 / 36 months = ₹3,525/month exactly. Total reconciles to 12,690,000 paisa.
- **No-cost Uneven Division (Remainder Absorption Proof):** ₹9,991 / 7 months = 142,728 paisa/month × 6 + 142,732 final installment = 999,100 paisa exactly.
- **Interest-Bearing Reducing Balance:** 850 bps (8.5% p.a.) on ₹1,26,900 over 60 months = ₹2,603.55/month, total ₹1,56,213.
- **Eligibility Cap Filtering:** High-tenure plans whose total payable exceeds the approved credit line are excluded.
- **Domain Guards:** Rejection of negative amounts or cashbacks exceeding product price.

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

## 📱 Design Fidelity

Extracted directly from live 1Fi app screenshots:
- **Colors:** Primary `#7C3AED`, Light `#EDE9FE`, Dark `#5B21B6`, Background `#F5F5F7`.
- **Cards:** 20px radius, 1px thin border (`#E8E7ED`), zero drop shadows.
- **Navigation:** Floating rounded bottom navigation card with sticky CTA sitting above it.
- **Accessibility:** Color is never the sole indicator of selection; 44×44pt minimum touch targets.

---

## 🔒 Statement of Independence
*1Fi's internal codebase was not available (`github.com/1fi` has 0 public repositories, confirmed directly). This Marketplace was designed independently from the assignment brief, the provided app screenshots, and 1fi.in's public product experience.*
