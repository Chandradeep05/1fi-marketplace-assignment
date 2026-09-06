# 1Fi Marketplace — API Specification

Base URL: `/api/v1`

All monetary amounts are represented as integer **paisa** (1 INR = 100 paisa).

---

## 1. Health Check

### `GET /api/v1/health`
Returns the status of the service.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 2. Categories

### `GET /api/v1/marketplace/categories`
Returns all active product categories.

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "smartphones",
      "name": "Smartphones",
      "icon": "phone-portrait",
      "sort_order": 0
    },
    {
      "id": "laptops",
      "name": "Laptops",
      "icon": "laptop",
      "sort_order": 1
    }
  ]
}
```

---

## 3. Eligibility

### `GET /api/v1/marketplace/eligibility`
Returns the available purchasing limit on the user's credit line.

**Response (200 OK):**
```json
{
  "data": {
    "total_limit_paisa": 20000000,
    "used_paisa": 5000000,
    "available_paisa": 15000000
  }
}
```

---

## 4. Products

### `GET /api/v1/marketplace/products`
Query parameters:
- `category` (optional, string)
- `search` (optional, string, max length 100)
- `page` (optional, integer, default 1)
- `limit` (optional, integer, default 20, max 100)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "iphone-17-pro",
      "name": "Apple iPhone 17 Pro",
      "brand": {
        "id": "apple",
        "name": "Apple",
        "logo_url": "https://..."
      },
      "category_id": "smartphones",
      "description": "The most powerful iPhone ever.",
      "base_price_paisa": 13490000,
      "mrp_paisa": 13990000,
      "is_available": true,
      "images": [
        {
          "id": "a1b2c3d4-...",
          "url": "https://...",
          "sort_order": 0
        }
      ],
      "variants": [
        {
          "id": "a0000000-0000-0000-0000-000000000001",
          "attributes": {
            "Storage": "256GB",
            "Color": "Black Titanium"
          },
          "price_paisa": 13490000,
          "available": true,
          "image_url": "https://..."
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "has_next_page": false
  }
}
```

### `GET /api/v1/marketplace/products/{product_id}`
Returns details and variants for a single product.

---

## 5. Quotes

### `POST /api/v1/marketplace/quotes`
Generates an immutable quote with frozen EMI plans valid for 10 minutes.

**Request Body:**
```json
{
  "product_id": "iphone-17-pro",
  "variant_id": "a0000000-0000-0000-0000-000000000001"
}
```

**Response (200 OK):**
```json
{
  "quote_id": "qt_01JXYZ87K62AB45...",
  "product_price_paisa": 13490000,
  "cashback_paisa": 800000,
  "financing_principal_paisa": 12690000,
  "expires_at": "2026-09-06T14:15:00Z",
  "plans": [
    {
      "plan_id": "36m",
      "tenure_months": 36,
      "monthly_emi_paisa": 352500,
      "final_emi_paisa": 352500,
      "interest_rate_bps": 0,
      "total_payable_paisa": 12690000,
      "is_no_cost": true,
      "recommended": true
    },
    {
      "plan_id": "60m",
      "tenure_months": 60,
      "monthly_emi_paisa": 260355,
      "final_emi_paisa": 260355,
      "interest_rate_bps": 850,
      "total_payable_paisa": 15621300,
      "is_no_cost": false,
      "recommended": false
    }
  ]
}
```

---

## 6. Checkout Intents

### `POST /api/v1/marketplace/checkout-intents`
Idempotently creates a checkout intent record against an unexpired quote.

**Headers:**
- `Idempotency-Key`: `<UUID>` (required)

**Request Body:**
```json
{
  "quote_id": "qt_01JXYZ87K62AB45...",
  "plan_id": "36m"
}
```

**Response (201 Created or 200 OK on idempotent replay):**
```json
{
  "intent_id": "ci_01ABCDEF78GHI...",
  "status": "received",
  "quote_id": "qt_01JXYZ87K62AB45...",
  "plan_id": "36m",
  "request_id": "req_0f1e2d3c4b5a"
}
```

---

## 7. Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "QUOTE_EXPIRED",
    "message": "This quote has expired. Please refresh your quote to proceed.",
    "request_id": "req_0f1e2d3c4b5a"
  }
}
```
