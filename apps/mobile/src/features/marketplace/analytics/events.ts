/**
 * 1Fi Marketplace — Analytics & Telemetry
 * Production-ready event registry and provider hook.
 */

export type MarketplaceEvent =
  | 'marketplace_opened'
  | 'product_viewed'
  | 'quote_requested'
  | 'plan_selected'
  | 'checkout_started'
  | 'checkout_completed';

export type AnalyticsProvider = (
  event: MarketplaceEvent,
  properties?: Record<string, unknown>
) => void;

let _activeProvider: AnalyticsProvider = (event, props) => {
  if (__DEV__) {
    // Development console log trace
    console.log(`[Analytics] ${event}`, props || {});
  }
};

export const registerAnalyticsProvider = (provider: AnalyticsProvider): void => {
  _activeProvider = provider;
};

export const track = (
  event: MarketplaceEvent,
  properties?: Record<string, unknown>
): void => {
  try {
    _activeProvider(event, properties);
  } catch (err) {
    console.warn('[Analytics Error]', err);
  }
};
