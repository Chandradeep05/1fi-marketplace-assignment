import { apiClient } from '../../../lib/api';
import {
  CategoriesResponse,
  EligibilityResponse,
  ProductsResponse,
  Product,
  Quote,
  QuoteRequest,
  CheckoutIntentRequest,
  CheckoutIntentResponse,
} from '@1fi/contracts';

export const marketplaceApi = {
  async getCategories(): Promise<CategoriesResponse> {
    const res = await apiClient.get<CategoriesResponse>('/marketplace/categories');
    return res.data;
  },

  async getEligibility(): Promise<EligibilityResponse> {
    const res = await apiClient.get<EligibilityResponse>('/marketplace/eligibility');
    return res.data;
  },

  async getProducts(params?: {
    category?: string;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<ProductsResponse> {
    const res = await apiClient.get<ProductsResponse>('/marketplace/products', {
      params,
    });
    return res.data;
  },

  async getProduct(productId: string): Promise<Product> {
    const res = await apiClient.get<Product>(`/marketplace/products/${productId}`);
    return res.data;
  },

  async createQuote(req: QuoteRequest): Promise<Quote> {
    const res = await apiClient.post<Quote>('/marketplace/quotes', req);
    return res.data;
  },

  async createCheckoutIntent(
    req: CheckoutIntentRequest,
    idempotencyKey: string
  ): Promise<CheckoutIntentResponse> {
    const res = await apiClient.post<CheckoutIntentResponse>(
      '/marketplace/checkout-intents',
      req,
      {
        headers: {
          'Idempotency-Key': idempotencyKey,
        },
      }
    );
    return res.data;
  },
};
