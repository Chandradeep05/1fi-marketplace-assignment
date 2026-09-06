/**
 * 1Fi Marketplace — Feature Flags
 * Governs conditional availability of marketplace surfaces.
 * Fail-closed policy: only explicit 'true' enables the feature.
 */

export function parseFeatureFlag(raw?: string | null): boolean {
  return raw?.trim().toLowerCase() === 'true';
}

export const isMarketplaceEnabled: boolean =
  parseFeatureFlag(process.env.EXPO_PUBLIC_MARKETPLACE_ENABLED);
