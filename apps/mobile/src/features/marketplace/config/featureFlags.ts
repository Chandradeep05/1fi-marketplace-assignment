/**
 * 1Fi Marketplace — Feature Flags
 * Governs conditional availability of marketplace surfaces.
 */

export const isMarketplaceEnabled: boolean =
  process.env.EXPO_PUBLIC_MARKETPLACE_ENABLED !== 'false';
