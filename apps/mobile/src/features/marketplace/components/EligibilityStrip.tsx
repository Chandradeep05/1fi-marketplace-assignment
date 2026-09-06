import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, radius, spacing, typography } from '../../../theme';
import { useEligibility } from '../hooks/useEligibility';
import { formatPaisa } from '../utils/formatMoney';

export const EligibilityStrip: React.FC = () => {
  const { data, isLoading, isError } = useEligibility();

  if (isLoading || isError || !data?.data) {
    return null;
  }

  const { available_paisa, total_limit_paisa } = data.data;

  return (
    <View style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>⚡ Credit Limit</Text>
      </View>
      <View style={styles.infoRow}>
        <Text style={styles.label}>Available for Instant EMI:</Text>
        <Text style={styles.amount}>{formatPaisa(available_paisa)}</Text>
      </View>
      <Text style={styles.subtext}>
        Total approved line: {formatPaisa(total_limit_paisa)}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginVertical: spacing.xs,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    marginBottom: spacing.xs,
  },
  badgeText: {
    ...typography.captionSmall,
    color: colors.primaryDark,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  amount: {
    ...typography.h3,
    color: colors.success,
    fontWeight: '700',
  },
  subtext: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
