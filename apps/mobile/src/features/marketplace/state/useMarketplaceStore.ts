import { create } from 'zustand';
import { Product, Quote } from '@1fi/contracts';

interface MarketplaceState {
  selectedVariantId: string | null;
  selectedPlanId: string | null;
  activeQuote: Quote | null;
  activeProduct: Product | null;

  selectVariant: (variantId: string | null) => void;
  selectPlan: (planId: string | null) => void;
  setQuote: (quote: Quote | null) => void;
  setActiveProduct: (product: Product | null) => void;
  clearCheckout: () => void;
}

export const useMarketplaceStore = create<MarketplaceState>((set) => ({
  selectedVariantId: null,
  selectedPlanId: null,
  activeQuote: null,
  activeProduct: null,

  selectVariant: (variantId) => set({ selectedVariantId: variantId }),
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
        };
      }
      return { activeProduct: product };
    }),

  clearCheckout: () =>
    set({
      selectedVariantId: null,
      selectedPlanId: null,
      activeQuote: null,
      activeProduct: null,
    }),
}));
