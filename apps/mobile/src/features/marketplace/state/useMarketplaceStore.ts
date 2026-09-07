import { create } from 'zustand';
import { Product, Quote } from '@1fi/contracts';
import { createIdempotencyKey } from '../utils/idempotency';

interface MarketplaceState {
  selectedVariantId: string | null;
  selectedPlanId: string | null;
  activeQuote: Quote | null;
  activeProduct: Product | null;

  // Checkout idempotency & session lifecycle
  checkoutIdempotencyKey: string | null;
  checkoutSessionToken: string | null;
  lastCheckoutIntentId: string | null;

  selectVariant: (variantId: string | null) => void;
  selectPlan: (planId: string | null) => void;
  setQuote: (quote: Quote | null) => void;
  setActiveProduct: (product: Product | null) => void;
  getOrCreateIdempotencyKey: (quoteId: string, planId: string) => string;
  setCheckoutSuccess: (intentId: string) => void;
  clearCheckout: () => void;
}

export const useMarketplaceStore = create<MarketplaceState>((set, get) => ({
  selectedVariantId: null,
  selectedPlanId: null,
  activeQuote: null,
  activeProduct: null,

  checkoutIdempotencyKey: null,
  checkoutSessionToken: null,
  lastCheckoutIntentId: null,

  selectVariant: (variantId) =>
    set((state) => {
      // Invalidate quote and plan if variant actually changes
      if (state.selectedVariantId !== variantId) {
        return {
          selectedVariantId: variantId,
          selectedPlanId: null,
          activeQuote: null,
          checkoutIdempotencyKey: null,
          checkoutSessionToken: null,
        };
      }
      return { selectedVariantId: variantId };
    }),

  selectPlan: (planId) => set({ selectedPlanId: planId }),
  setQuote: (quote) => set({ activeQuote: quote }),
  setActiveProduct: (product) =>
    set((state) => {
      if (!product || state.activeProduct?.id !== product.id) {
        return {
          activeProduct: product,
          selectedVariantId: null,
          selectedPlanId: null,
          activeQuote: null,
          checkoutIdempotencyKey: null,
          checkoutSessionToken: null,
          lastCheckoutIntentId: null,
        };
      }
      return { activeProduct: product };
    }),

  getOrCreateIdempotencyKey: (quoteId: string, planId: string) => {
    const sessionToken = `${quoteId}:${planId}`;
    const state = get();
    // If we have an active key for this logical transaction (same quote + same plan)
    // that has NOT yet completed, reuse it for retries / network re-submits!
    if (
      state.checkoutSessionToken === sessionToken &&
      state.checkoutIdempotencyKey &&
      !state.lastCheckoutIntentId
    ) {
      return state.checkoutIdempotencyKey;
    }
    // A fresh transaction gets a brand new idempotency key
    const newKey = createIdempotencyKey();
    set({
      checkoutSessionToken: sessionToken,
      checkoutIdempotencyKey: newKey,
      lastCheckoutIntentId: null,
    });
    return newKey;
  },

  setCheckoutSuccess: (intentId: string) =>
    set({
      lastCheckoutIntentId: intentId,
      // Session is completed: clear active session key so subsequent new checkouts generate a fresh key
      checkoutIdempotencyKey: null,
      checkoutSessionToken: null,
    }),

  clearCheckout: () =>
    set({
      selectedVariantId: null,
      selectedPlanId: null,
      activeQuote: null,
      activeProduct: null,
      checkoutIdempotencyKey: null,
      checkoutSessionToken: null,
      lastCheckoutIntentId: null,
    }),
}));
