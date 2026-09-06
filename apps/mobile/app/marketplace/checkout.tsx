import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { colors, radius, spacing, typography } from '../../src/theme';
import { useMarketplaceStore } from '../../src/features/marketplace/state/useMarketplaceStore';
import { marketplaceApi } from '../../src/features/marketplace/api/marketplaceApi';
import { createIdempotencyKey } from '../../src/features/marketplace/utils/idempotency';
import { formatPaisa } from '../../src/features/marketplace/utils/formatMoney';

export default function CheckoutScreen() {
  const router = useRouter();

  const {
    activeProduct,
    selectedVariantId,
    activeQuote,
    selectedPlanId,
    clearCheckout,
  } = useMarketplaceStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successIntentId, setSuccessIntentId] = useState<string | null>(null);

  // One idempotency key per checkout session. Reused on retry so double-tap is idempotent!
  const idempotencyKeyRef = useRef<string>(createIdempotencyKey());

  if (!activeProduct || !activeQuote || !selectedPlanId) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.errorTitle}>No active checkout session</Text>
          <Text style={styles.errorSubtitle}>Please select a product and EMI plan first.</Text>
          <TouchableOpacity style={styles.primaryButton} onPress={() => router.replace('/(tabs)/shop')}>
            <Text style={styles.buttonText}>Return to Shop</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const selectedPlan = activeQuote.plans.find((p) => p.plan_id === selectedPlanId);
  const selectedVariant = activeProduct.variants.find((v) => v.id === selectedVariantId);
  const variantDescription = selectedVariant
    ? Object.values(selectedVariant.attributes).join(' · ')
    : '';

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const res = await marketplaceApi.createCheckoutIntent(
        {
          quote_id: activeQuote.quote_id,
          plan_id: selectedPlanId,
        },
        idempotencyKeyRef.current
      );

      setIsSubmitting(false);
      setSuccessIntentId(res.intent_id);
      clearCheckout();
    } catch (err: any) {
      setIsSubmitting(false);
      setErrorMessage(err?.error?.message || 'Failed to submit checkout intent. Please try again.');
    }
  };

  if (successIntentId) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successContainer}>
          <View style={styles.successBadge}>
            <Text style={styles.checkmark}>✓</Text>
          </View>
          <Text style={styles.successTitle}>Your request has been noted!</Text>
          <Text style={styles.successSubtitle}>
            Your mutual-fund backed credit line EMI reservation has been logged.
          </Text>

          <View style={styles.intentCard}>
            <Text style={styles.intentLabel}>Intent Reference</Text>
            <Text style={styles.intentId}>{successIntentId}</Text>
          </View>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.replace('/(tabs)/shop')}
            activeOpacity={0.85}
          >
            <Text style={styles.buttonText}>Back to Marketplace</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.heading}>Order Summary</Text>

        <View style={styles.summaryCard}>
          <Text style={styles.brand}>{activeProduct.brand.name}</Text>
          <Text style={styles.productTitle}>{activeProduct.name}</Text>
          {variantDescription ? (
            <Text style={styles.variantDetails}>{variantDescription}</Text>
          ) : null}

          <View style={styles.divider} />

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Product Price</Text>
            <Text style={styles.rowValue}>{formatPaisa(activeQuote.product_price_paisa)}</Text>
          </View>

          {activeQuote.cashback_paisa > 0 && (
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: colors.success }]}>Financing Cashback</Text>
              <Text style={[styles.rowValue, { color: colors.success }]}>
                - {formatPaisa(activeQuote.cashback_paisa)}
              </Text>
            </View>
          )}

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Financed Amount</Text>
            <Text style={styles.rowValue}>
              {formatPaisa(activeQuote.financing_principal_paisa)}
            </Text>
          </View>

          <View style={styles.divider} />

          {selectedPlan && (
            <>
              <View style={styles.row}>
                <Text style={styles.rowLabel}>EMI Tenure</Text>
                <Text style={styles.rowValue}>{selectedPlan.tenure_months} months</Text>
              </View>

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Monthly Installment</Text>
                <Text style={styles.rowValue}>
                  {formatPaisa(selectedPlan.monthly_emi_paisa)} / mo
                </Text>
              </View>

              {selectedPlan.monthly_emi_paisa !== selectedPlan.final_emi_paisa && (
                <View style={styles.row}>
                  <Text style={styles.rowLabel}>Final Installment</Text>
                  <Text style={styles.rowValue}>
                    {formatPaisa(selectedPlan.final_emi_paisa)}
                  </Text>
                </View>
              )}

              <View style={styles.row}>
                <Text style={styles.rowLabel}>Interest Rate</Text>
                <Text style={styles.rowValue}>
                  {selectedPlan.is_no_cost
                    ? '0% (No-cost)'
                    : `${(selectedPlan.interest_rate_bps / 100).toFixed(1)}% p.a.`}
                </Text>
              </View>

              <View style={styles.divider} />

              <View style={[styles.row, styles.totalRow]}>
                <Text style={styles.totalLabel}>Total Payable</Text>
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
            🔒 Protected by idempotent submission. Your credit line will not be charged twice.
          </Text>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.primaryButton, isSubmitting && styles.disabledButton]}
          onPress={handleConfirm}
          disabled={isSubmitting}
          activeOpacity={0.85}
        >
          {isSubmitting ? (
            <ActivityIndicator color={colors.textOnPrimary} />
          ) : (
            <Text style={styles.buttonText}>Confirm & Proceed →</Text>
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
    opacity: 0.7,
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
