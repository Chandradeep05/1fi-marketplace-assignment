/**
 * 1Fi Marketplace — Canonical Shared Types
 * All monetary amounts are represented as integer paisa (1 Rupee = 100 Paisa).
 */

export type Paisa = number;

export interface Category {
  id: string;
  name: string;
  icon: string;
  sort_order: number;
}

export interface Brand {
  id: string;
  name: string;
  logo_url: string | null;
}

export interface ProductImage {
  id: string;
  url: string;
  sort_order: number;
}

export interface ProductVariant {
  id: string;
  attributes: Record<string, string>;
  price_paisa: Paisa;
  available: boolean;
  image_url?: string | null;
}

export interface Product {
  id: string;
  name: string;
  brand: Brand;
  category_id: string;
  description: string;
  base_price_paisa: Paisa;
  mrp_paisa?: Paisa | null;
  is_available: boolean;
  images: ProductImage[];
  variants: ProductVariant[];
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  has_next_page: boolean;
}

export interface ProductsResponse {
  data: Product[];
  pagination: Pagination;
}

export interface CategoriesResponse {
  data: Category[];
}

export interface EligibilityData {
  total_limit_paisa: Paisa;
  used_paisa: Paisa;
  available_paisa: Paisa;
}

export interface EligibilityResponse {
  data: EligibilityData;
}

export interface EmiPlan {
  plan_id: string;
  tenure_months: number;
  monthly_emi_paisa: Paisa;
  final_emi_paisa: Paisa;
  interest_rate_bps: number;
  total_payable_paisa: Paisa;
  is_no_cost: boolean;
  recommended: boolean;
}

export interface Quote {
  quote_id: string;
  product_price_paisa: Paisa;
  cashback_paisa: Paisa;
  financing_principal_paisa: Paisa;
  expires_at: string;
  plans: EmiPlan[];
}

export interface QuoteRequest {
  product_id: string;
  variant_id: string;
}

export interface CheckoutIntentRequest {
  quote_id: string;
  plan_id: string;
}

export interface CheckoutIntentResponse {
  intent_id: string;
  status: 'received' | 'processing' | 'completed' | 'failed';
  quote_id: string;
  plan_id: string;
  request_id?: string;
}

export type ErrorCode =
  | 'PRODUCT_NOT_FOUND'
  | 'VARIANT_NOT_FOUND'
  | 'VARIANT_UNAVAILABLE'
  | 'QUOTE_NOT_FOUND'
  | 'QUOTE_EXPIRED'
  | 'PLAN_NOT_IN_QUOTE'
  | 'INSUFFICIENT_LIMIT'
  | 'NO_ELIGIBLE_RULES'
  | 'ELIGIBILITY_UNAVAILABLE'
  | 'MISSING_IDEMPOTENCY_KEY'
  | 'IDEMPOTENCY_CONFLICT'
  | 'RATE_LIMITED'
  | 'VALIDATION_ERROR'
  | 'INTERNAL_ERROR';

export interface APIError {
  error: {
    code: ErrorCode;
    message: string;
    request_id?: string;
  };
}
