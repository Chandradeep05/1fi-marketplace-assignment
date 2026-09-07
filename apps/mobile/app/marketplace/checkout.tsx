import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { colors, radius, spacing, typography } from '../../src/theme';
import { useMarketplaceStore } from '../../src/features/marketplace/state/useMarketplaceStore';
import { marketplaceApi } from '../../src/features/marketplace/api/marketplaceApi';
import { formatPaisa } from '../../src/features/marketplace/utils/formatMoney';
import { useQuoteExpiry } from '../../src/features/marketplace/hooks/useQuoteExpiry';
import { QuoteExpiredBanner } from '../../src/features/marketplace/components/QuoteExpiredBanner';
import { track } from '../../src/features/marketplace/analytics/events';
import { STRINGS } from '../../src/features/marketplace/constants/strings';

export default function CheckoutScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ planId?: string; variantId?: string }>();

  const {
    activeProduct,
    selectedVariantId,
    activeQuote,
    selectedPlanId,
    selectPlan,
    getOrCreateIdempotencyKey,
    setCheckoutSuccess,
    clearCheckout,
  } = useMarketplaceStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successIntentId, setSuccessIntentId] = useState<string | null>(null);

  // Dual-source plan resolution: route parameter has priority over store state
  // to guarantee the user's selected EMI plan on Product Detail survives navigation
  const effectivePlanId = params.planId || selectedPlanId;
  const effectiveVariantId = params.variantId || selectedVariantId;

  // Synchronize store if route parameter provided a more specific plan
  useEffect(() => {
    if (params.planId && params.planId !== selectedPlanId) {
      selectPlan(params.planId);
    }
  }, [params.planId, selectedPlanId]);

  const isQuoteExpired = useQuoteExpiry(activeQuote?.expires_at);

  // 1. Success guard MUST evaluate before session-check guard (Fixes demo-breaking bug)
  if (successIntentId) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successContainer}>
          <View style={styles.successBadge}>
            <Text style={styles.checkmark}>✓</Text>
          </View>
          <Text style={styles.successTitle}>{STRINGS.SUCCESS_TITLE}</Text>
          <Text style={styles.successSubtitle}>
            {STRINGS.SUCCESS_SUBTITLE}
          </Text>

          <View style={styles.intentCard}>
            <Text style={styles.intentLabel}>{STRINGS.INTENT_REFERENCE}</Text>
            <Text style={styles.intentId}>{successIntentId}</Text>
          </View>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => {
              clearCheckout();
              setSuccessIntentId(null);
              router.replace('/(tabs)/shop');
            }}
            activeOpacity={0.85}
          >
            <Text style={styles.buttonText}>{STRINGS.BACK_TO_MARKETPLACE}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // 2. Active session guard
  if (!activeProduct || !activeQuote || !effectivePlanId) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.errorTitle}>{STRINGS.NO_ACTIVE_SESSION_TITLE}</Text>
          <Text style={styles.errorSubtitle}>{STRINGS.NO_ACTIVE_SESSION_SUBTITLE}</Text>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => {
              clearCheckout();
              setSuccessIntentId(null);
              router.replace('/(tabs)/shop');
            }}
          >
            <Text style={styles.buttonText}>{STRINGS.RETURN_TO_SHOP}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const selectedPlan = activeQuote.plans.find((p) => p.plan_id === effectivePlanId);
  const selectedVariant = activeProduct.variants.find((v) => v.id === effectiveVariantId);
  const variantDescription = selectedVariant
    ? Object.values(selectedVariant.attributes).join(' · ')
    : '';

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    // Get fresh idempotency key for new transaction, or reuse key on network/UI retry
    const idempotencyKey = getOrCreateIdempotencyKey(activeQuote.quote_id, effectivePlanId);

    try {
      const res = await marketplaceApi.createCheckoutIntent(
        {
          quote_id: activeQuote.quote_id,
          plan_id: effectivePlanId,
        },
        idempotencyKey
      );

      setIsSubmitting(false);
      track('checkout_completed', {
        intent_id: res.intent_id,
        quote_id: activeQuote.quote_id,
        plan_id: effectivePlanId,
      });
      setCheckoutSuccess(res.intent_id);
      setSuccessIntentId(res.intent_id);
    } catch (err: any) {
      setIsSubmitting(false);
      const code = err?.error?.code;
      if (code === 'QUOTE_EXPIRED') {
        setErrorMessage(STRINGS.QUOTE_EXPIRED_ERROR);
      } else if (code === 'NO_ELIGIBLE_RULES') {
        setErrorMessage(STRINGS.NO_ELIGIBLE_RULES);
      } else if (code === 'INSUFFICIENT_LIMIT') {
        setErrorMessage(STRINGS.INSUFFICIENT_LIMIT);
      } else if (code === 'IDEMPOTENCY_CONFLICT') {
        setErrorMessage(STRINGS.IDEMPOTENCY_CONFLICT);
      } else {
        setErrorMessage(err?.error?.message || STRINGS.GENERIC_ERROR);
      }
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.heading}>{STRINGS.ORDER_SUMMARY}</Text>

        {isQuoteExpired && (
          <QuoteExpiredBanner onRefresh={() => router.back()} />
        )}

        <View style={styles.summaryCard}>
          <Text style={styles.brand}>{activeProduct.brand.name}</Text>
          <Text style={styles.productTitle}>{activeProduct.name}</Text>
          {variantDescription ? (
            <Text style={styles.variantDetails}>{variantDescription}</Text>
          ) : null}

          <View style={styles.divider} />

          <View style={styles.row}>
            <Text style={styles.rowLabel}>{STRINGS.PRODUCT_PRICE}</Text>
            <Text style={styles.rowValue}>{formatPaisa(activeQuote.product_price_paisa)}</Text>
          </View>

          {activeQuote.cashback_paisa > 0 && (
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: colors.success }]}>{STRINGS.FINANCING_CASHBACK}</Text>
              <Text style={[styles.rowValue, { color: colors.success }]}>
                - {formatPaisa(activeQuote.cashback_paisa)}
              </Text>
            </View>
          )}

          <View style={styles.row}>
            <Text style={styles.rowLabel}>{STRINGS.FINANCED_AMOUNT}</Text>
            <Text style={styles.rowValue}>
              {formatPaisa(activeQuote.financing_principal_paisa)}
            </Text>
          </View>

          <View style={styles.divider} />

          {selectedPlan && (
            <>
              <View style={styles.row}>
                <Text style={styles.rowLabel}>{STRINGS.EMI_TENURE}</Text>
                <Text style={styles.rowValue}>{selectedPlan.tenure_months} months</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>{STRINGS.MONTHLY_INSTALLMENT}</Text>
                <Text style={styles.rowValue}>
                  {formatPaisa(selectedPlan.monthly_emi_paisa)} / mo
                </Text>
              </View>

              {selectedPlan.monthly_emi_paisa !== selectedPlan.final_emi_paisa && (
                <View style={styles.row}>
                  <Text style={styles.rowLabel}>{STRINGS.FINAL_INSTALLMENT}</Text>
                  <Text style={styles.rowValue}>
                    {formatPaisa(selectedPlan.final_emi_paisa)}
                  </Text>
                </View>
              )}

              <View style={styles.row}>
                <Text style={styles.rowLabel}>{STRINGS.INTEREST_RATE}</Text>
                <Text style={styles.rowValue}>
                  {selectedPlan.is_no_cost
                    ? '0% (No-cost)'
                    : `${(selectedPlan.interest_rate_bps / 100).toFixed(1)}% p.a.`}
                </Text>
              </View>

              <View style={styles.divider} />

              <View style={[styles.row, styles.totalRow]}>
                <Text style={styles.totalLabel}>{STRINGS.TOTAL_PAYABLE}</Text>
                <Text style={styles.totalValue}>
                  {formatPaisa(selectedPlan.total_payable_paisa)}
                </Text>
              </View>
            </>
          )}
        </View>

        {errorMessage && (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>⚠️ {errorMessage}</Text>
          </View>
        )}

        <View style={styles.securityNote}>
          <Text style={styles.securityText}>
            {STRINGS.SECURITY_NOTE}
          </Text>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[
            styles.primaryButton,
            (isSubmitting || isQuoteExpired) && styles.disabledButton,
          ]}
          onPress={handleConfirm}
          disabled={isSubmitting || isQuoteExpired}
          activeOpacity={0.85}
        >
          {isSubmitting ? (
            <ActivityIndicator color={colors.textOnPrimary} />
          ) : (
            <Text style={styles.buttonText}>{STRINGS.CONFIRM_AND_PROCEED}</Text>
          )}
        </TouchableOpacity>
      </View>
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
    padding: spacing.xl,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: 100,
  },
  heading: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  summaryCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  brand: {
    ...typography.captionSmall,
    color: colors.textSecondary,
    textTransform: 'uppercase',
  },
  productTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginTop: 2,
  },
  variantDetails: {
    ...typography.caption,
    color: colors.primaryDark,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.md,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs + 2,
  },
  rowLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },
  rowValue: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  totalRow: {
    marginTop: spacing.xs,
  },
  totalLabel: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  totalValue: {
    ...typography.h2,
    color: colors.primary,
    fontWeight: '700',
  },
  errorCard: {
    backgroundColor: '#FEE2E2',
    padding: spacing.md,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.error,
    marginTop: spacing.md,
  },
  errorText: {
    ...typography.bodyMedium,
    color: colors.error,
  },
  securityNote: {
    marginTop: spacing.md,
    paddingHorizontal: spacing.sm,
  },
  securityText: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: spacing.md,
  },
  primaryButton: {
    backgroundColor: colors.primary,
    height: 52,
    borderRadius: radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabledButton: {
    opacity: 0.5,
  },
  buttonText: {
    ...typography.buttonLabel,
    color: colors.textOnPrimary,
  },
  errorTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  errorSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  successBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#DCFCE7',
    borderWidth: 2,
    borderColor: colors.success,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  checkmark: {
    fontSize: 36,
    color: colors.success,
    fontWeight: '700',
  },
  successTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  successSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  intentCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.xl,
    width: '100%',
  },
  intentLabel: {
    ...typography.captionSmall,
    color: colors.textSecondary,
    textTransform: 'uppercase',
  },
  intentId: {
    ...typography.h3,
    color: colors.primaryDark,
    marginTop: spacing.xs,
  },
});
