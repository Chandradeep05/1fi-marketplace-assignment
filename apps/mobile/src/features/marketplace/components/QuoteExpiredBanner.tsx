import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, radius, spacing, typography } from '../../../theme';
import { STRINGS } from '../constants/strings';

interface QuoteExpiredBannerProps {
  onRefresh: () => void;
  isLoading?: boolean;
}

export const QuoteExpiredBanner: React.FC<QuoteExpiredBannerProps> = ({
  onRefresh,
  isLoading = false,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.textContainer}>
        <Text style={styles.icon}>⏱️</Text>
        <Text style={styles.message}>
          {STRINGS.QUOTE_EXPIRED_DESC}
        </Text>
      </View>
      <TouchableOpacity
        style={styles.refreshButton}
        onPress={onRefresh}
        disabled={isLoading}
        activeOpacity={0.8}
      >
        <Text style={styles.refreshText}>
          {isLoading ? 'Refreshing...' : STRINGS.REFRESH_QUOTE}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FEF3C7', // Amber warning light
    borderWidth: 1,
    borderColor: colors.warning,
    borderRadius: radius.card,
    padding: spacing.md,
    marginVertical: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  textContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginRight: spacing.sm,
  },
  icon: {
    fontSize: 16,
  },
  message: {
    ...typography.caption,
    color: '#92400E', // Dark amber
    fontWeight: '500',
    flexShrink: 1,
  },
  refreshButton: {
    backgroundColor: colors.warning,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.pill,
  },
  refreshText: {
    ...typography.caption,
    color: colors.textOnPrimary,
    fontWeight: '700',
  },
});
