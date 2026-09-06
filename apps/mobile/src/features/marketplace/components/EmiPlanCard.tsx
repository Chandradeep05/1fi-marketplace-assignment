import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { EmiPlan } from '@1fi/contracts';
import { colors, radius, spacing, typography } from '../../../theme';
import { formatPaisa } from '../utils/formatMoney';

interface EmiPlanCardProps {
  plan: EmiPlan;
  isSelected: boolean;
  onSelect: () => void;
  cashbackPaisa?: number;
}

export const EmiPlanCard: React.FC<EmiPlanCardProps> = ({
  plan,
  isSelected,
  onSelect,
  cashbackPaisa = 0,
}) => {
  const hasRemainder = plan.monthly_emi_paisa !== plan.final_emi_paisa;
  const emiText = `${formatPaisa(plan.monthly_emi_paisa)} / month`;

  const accessibilityLabel = `${plan.tenure_months} months plan, ${emiText}, Total payable ${formatPaisa(
    plan.total_payable_paisa
  )}${plan.is_no_cost ? ', No-cost EMI' : ''}${plan.recommended ? ', Recommended' : ''}${
    isSelected ? ', Selected' : ''
  }`;

  return (
    <TouchableOpacity
      style={[styles.card, isSelected && styles.selectedCard]}
      onPress={onSelect}
      activeOpacity={0.85}
      accessibilityRole="radio"
      accessibilityState={{ selected: isSelected }}
      accessibilityLabel={accessibilityLabel}
    >
      <View style={styles.headerRow}>
        <View style={styles.radioRow}>
          <View style={[styles.radioCircle, isSelected && styles.selectedRadioCircle]}>
            {isSelected && <Text style={styles.checkmarkIcon}>✓</Text>}
          </View>
          <Text style={[styles.tenureText, isSelected && styles.selectedTenureText]}>
            {plan.tenure_months} months
          </Text>
        </View>

        {plan.recommended && (
          <View style={styles.recommendedBadge}>
            <Text style={styles.recommendedText}>Recommended</Text>
          </View>
        )}
      </View>

      <View style={styles.amountContainer}>
        <Text style={[styles.monthlyEmi, isSelected && styles.selectedMonthlyEmi]}>
          {emiText}
        </Text>
        {hasRemainder && (
          <Text style={styles.remainderText}>
            ({formatPaisa(plan.monthly_emi_paisa)} × {plan.tenure_months - 1} mo, final {formatPaisa(plan.final_emi_paisa)})
          </Text>
        )}
      </View>

      <View style={styles.footerRow}>
        <Text style={styles.badgeText}>
          {plan.is_no_cost ? 'No-cost EMI' : `${(plan.interest_rate_bps / 100).toFixed(1)}% p.a.`}
          {cashbackPaisa > 0 ? ` · Cashback ${formatPaisa(cashbackPaisa)}` : ''}
        </Text>
        <Text style={styles.totalPayable}>
          Total: {formatPaisa(plan.total_payable_paisa)}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1.5,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  selectedCard: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: colors.textSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedRadioCircle: {
    borderColor: colors.primary,
  },
  checkmarkIcon: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '800',
    lineHeight: 14,
  },
  tenureText: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  selectedTenureText: {
    color: colors.primaryDark,
  },
  recommendedBadge: {
    backgroundColor: colors.accentGold,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  recommendedText: {
    ...typography.captionSmall,
    color: colors.textPrimary,
    fontWeight: '700',
  },
  amountContainer: {
    marginVertical: spacing.xs,
  },
  monthlyEmi: {
    ...typography.h2,
    color: colors.textPrimary,
    fontWeight: '700',
  },
  selectedMonthlyEmi: {
    color: colors.primaryDark,
  },
  remainderText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.xs + 2,
  },
  badgeText: {
    ...typography.caption,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  totalPayable: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});
