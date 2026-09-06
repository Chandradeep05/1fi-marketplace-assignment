import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Image,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors, radius, spacing, typography } from '../../../../../src/theme';
import { useProduct } from '../../../../../src/features/marketplace/hooks/useProduct';
import { useMarketplaceStore } from '../../../../../src/features/marketplace/state/useMarketplaceStore';
import { marketplaceApi } from '../../../../../src/features/marketplace/api/marketplaceApi';
import { VariantSelector } from '../../../../../src/features/marketplace/components/VariantSelector';
import { EmiPlanCard } from '../../../../../src/features/marketplace/components/EmiPlanCard';
import { StickyCTA } from '../../../../../src/features/marketplace/components/StickyCTA';
import { QuoteExpiredBanner } from '../../../../../src/features/marketplace/components/QuoteExpiredBanner';
import { EmiPlanSkeleton } from '../../../../../src/features/marketplace/components/Skeleton';
import { useQuoteExpiry } from '../../../../../src/features/marketplace/hooks/useQuoteExpiry';
import { formatPaisa, formatSavings } from '../../../../../src/features/marketplace/utils/formatMoney';
import { track } from '../../../../../src/features/marketplace/analytics/events';
import { STRINGS } from '../../../../../src/features/marketplace/constants/strings';
import { isMarketplaceEnabled } from '../../../../../src/features/marketplace/config/featureFlags';

export default function ProductDetailScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();

  useEffect(() => {
    if (!isMarketplaceEnabled) {
      router.replace('/(tabs)/shop');
    }
  }, []);

  const {
    selectedVariantId,
    selectedPlanId,
    activeQuote,
    selectVariant,
    selectPlan,
    setQuote,
    setActiveProduct,
  } = useMarketplaceStore();

  const { data: product, isLoading: isProductLoading, isError: isProductError } = useProduct(productId!);

  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState<string | null>(null);

  // Version guard ref to prevent race conditions on rapid variant selection
  const quoteGenerationRef = useRef<number>(0);

  const isExpired = useQuoteExpiry(activeQuote?.expires_at);

  // Set active product when loaded
  useEffect(() => {
    if (product) {
      setActiveProduct(product);
      // If selectedVariantId does not belong to this product's variants, reset and select first
      const currentVariantExists = product.variants?.some((v) => v.id === selectedVariantId);
      if (!currentVariantExists && product.variants?.length > 0) {
        const firstAvail = product.variants.find((v) => v.available) || product.variants[0];
        handleVariantSelect(firstAvail.id);
      }
    }
  }, [product, productId]);

  const fetchQuoteForVariant = async (variantId: string) => {
    const generation = ++quoteGenerationRef.current;

    track('quote_requested', { product_id: productId, variant_id: variantId });
    setQuote(null);
    selectPlan(null);
    setQuoteError(null);
    setQuoteLoading(true);

    try {
      const quote = await marketplaceApi.createQuote({
        product_id: productId!,
        variant_id: variantId,
      });

      // Guard: discard response if user already selected a different variant
      if (generation !== quoteGenerationRef.current) {
        return;
      }

      setQuote(quote);
      setQuoteLoading(false);

      // Auto-select recommended plan if available
      const recommendedPlan = quote.plans.find((p) => p.recommended) || quote.plans[0];
      if (recommendedPlan) {
        selectPlan(recommendedPlan.plan_id);
        track('plan_selected', { plan_id: recommendedPlan.plan_id, tenure_months: recommendedPlan.tenure_months });
      }
    } catch (err: any) {
      if (generation !== quoteGenerationRef.current) {
        return;
      }
      setQuoteLoading(false);
      setQuoteError(err?.error?.message || 'Unable to fetch EMI plans right now.');
    }
  };

  const handleVariantSelect = (variantId: string) => {
    selectVariant(variantId);
    fetchQuoteForVariant(variantId);
  };

  const handleSelectPlan = (planId: string, tenureMonths: number) => {
    selectPlan(planId);
    track('plan_selected', { plan_id: planId, tenure_months: tenureMonths });
  };

  const selectedPlan = activeQuote?.plans.find((p) => p.plan_id === selectedPlanId);
  const selectedVariant = product?.variants?.find((v) => v.id === selectedVariantId);
  const currentPrice = selectedVariant?.price_paisa || product?.base_price_paisa || 0;
  const savings = formatSavings(product?.mrp_paisa, currentPrice);

  const canProceed =
    !!selectedVariantId &&
    !!activeQuote &&
    !isExpired &&
    !!selectedPlanId &&
    !quoteLoading;

  const ctaLabel = selectedPlan
    ? `${formatPaisa(selectedPlan.monthly_emi_paisa)}/month   ${STRINGS.PROCEED_WITH_EMI}`
    : STRINGS.CTA_SELECT_PLAN_HINT;

  if (isProductLoading) {
    return (
      <SafeAreaView style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </SafeAreaView>
    );
  }

  if (isProductError || !product) {
    return (
      <SafeAreaView style={styles.centerContainer}>
        <Text style={styles.errorText}>{STRINGS.PRODUCT_UNAVAILABLE}</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>{STRINGS.BACK_BUTTON}</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const activeImage = selectedVariant?.image_url || product.images?.[0]?.url;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.navBar}>
        <TouchableOpacity onPress={() => router.back()} style={styles.navButton}>
          <Text style={styles.navButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.navTitle} numberOfLines={1}>
          {product.name}
        </Text>
        <View style={{ width: 44 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Gallery */}
        <View style={styles.galleryContainer}>
          {activeImage ? (
            <Image source={{ uri: activeImage }} style={styles.galleryImage} resizeMode="contain" />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Text style={{ fontSize: 60 }}>📦</Text>
            </View>
          )}
        </View>

        {/* Info Block */}
        <View style={styles.infoCard}>
          <Text style={styles.brandName}>{product.brand.name}</Text>
          <Text style={styles.productName}>{product.name}</Text>

          <View style={styles.priceRow}>
            <Text style={styles.price}>{formatPaisa(currentPrice)}</Text>
            {product.mrp_paisa && product.mrp_paisa > currentPrice && (
              <Text style={styles.mrp}>{formatPaisa(product.mrp_paisa)}</Text>
            )}
            {savings && (
              <View style={styles.savingsTag}>
                <Text style={styles.savingsTagText}>{savings}</Text>
              </View>
            )}
          </View>

          {activeQuote?.cashback_paisa ? (
            <View style={styles.cashbackBanner}>
              <Text style={styles.cashbackText}>
                🎉 Includes {formatPaisa(activeQuote.cashback_paisa)} instant financing discount
              </Text>
            </View>
          ) : null}

          {/* Variant Selector */}
          {product.variants && product.variants.length > 0 && (
            <VariantSelector
              variants={product.variants}
              selectedVariantId={selectedVariantId}
              onSelectVariant={handleVariantSelect}
            />
          )}

          {/* EMI Plan Section */}
          <View style={styles.emiSection}>
            <Text style={styles.sectionHeading}>Choose an EMI Plan</Text>
            <Text style={styles.sectionSubtitle}>
              Server-guaranteed rates frozen for 10 minutes. No hidden processing fees.
            </Text>

            {isExpired && (
              <QuoteExpiredBanner
                isLoading={quoteLoading}
                onRefresh={() => selectedVariantId && fetchQuoteForVariant(selectedVariantId)}
              />
            )}

            {quoteLoading ? (
              <EmiPlanSkeleton count={3} />
            ) : quoteError ? (
              <View style={styles.quoteErrorContainer}>
                <Text style={styles.quoteErrorText}>{quoteError}</Text>
                <TouchableOpacity
                  style={styles.quoteRetryButton}
                  onPress={() => selectedVariantId && fetchQuoteForVariant(selectedVariantId)}
                >
                  <Text style={styles.quoteRetryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : activeQuote?.plans && activeQuote.plans.length > 0 ? (
              activeQuote.plans.map((plan) => (
                <EmiPlanCard
                  key={plan.plan_id}
                  plan={plan}
                  isSelected={selectedPlanId === plan.plan_id}
                  onSelect={() => handleSelectPlan(plan.plan_id, plan.tenure_months)}
                  cashbackPaisa={activeQuote.cashback_paisa}
                />
              ))
            ) : (
              <Text style={styles.noPlansText}>
                {STRINGS.NO_ELIGIBLE_RULES}
              </Text>
            )}
          </View>
        </View>

        {/* Space reservation for sticky CTA */}
        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Sticky CTA above bottom nav */}
      <StickyCTA
        label={ctaLabel}
        disabled={!canProceed}
        onPress={() => {
          track('checkout_started', {
            quote_id: activeQuote?.quote_id,
            plan_id: selectedPlanId,
          });
          router.push('/marketplace/checkout' as any);
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  navBar: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  navButton: {
    paddingVertical: spacing.xs,
  },
  navButtonText: {
    ...typography.bodyMedium,
    color: colors.primary,
  },
  navTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    flex: 1,
    textAlign: 'center',
    marginHorizontal: spacing.sm,
  },
  scrollContent: {
    paddingBottom: spacing.xl,
  },
  galleryContainer: {
    height: 280,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
  },
  galleryImage: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.card,
    borderTopRightRadius: radius.card,
    marginTop: -spacing.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  brandName: {
    ...typography.captionSmall,
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  productName: {
    ...typography.h2,
    color: colors.textPrimary,
    marginTop: 2,
    marginBottom: spacing.xs,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.sm,
    marginVertical: spacing.xs,
  },
  price: {
    ...typography.displayBold,
    color: colors.textPrimary,
  },
  mrp: {
    ...typography.body,
    color: colors.textSecondary,
    textDecorationLine: 'line-through',
  },
  savingsTag: {
    backgroundColor: colors.success,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  savingsTagText: {
    ...typography.captionSmall,
    color: colors.textOnPrimary,
  },
  cashbackBanner: {
    backgroundColor: colors.primaryLight,
    padding: spacing.sm,
    borderRadius: radius.chip,
    marginTop: spacing.xs,
  },
  cashbackText: {
    ...typography.caption,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  emiSection: {
    marginTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.md,
  },
  sectionHeading: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  sectionSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: spacing.md,
  },
  quoteErrorContainer: {
    backgroundColor: '#FEE2E2',
    padding: spacing.md,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.error,
    alignItems: 'center',
  },
  quoteErrorText: {
    ...typography.body,
    color: colors.error,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  quoteRetryButton: {
    backgroundColor: colors.error,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.pill,
  },
  quoteRetryText: {
    ...typography.caption,
    color: colors.textOnPrimary,
    fontWeight: '700',
  },
  noPlansText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginVertical: spacing.md,
  },
  errorText: {
    ...typography.h3,
    color: colors.error,
    marginBottom: spacing.md,
  },
  backButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
  },
  backButtonText: {
    ...typography.buttonLabel,
    color: colors.textOnPrimary,
  },
});
