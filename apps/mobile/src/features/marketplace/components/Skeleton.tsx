import React from 'react';
import { View, StyleSheet } from 'react-native';
import { colors, radius, spacing } from '../../../theme';

export const ProductCardSkeleton: React.FC = () => {
  return (
    <View style={styles.productCard}>
      <View style={styles.imagePlaceholder} />
      <View style={styles.content}>
        <View style={[styles.line, { width: '40%', height: 12, marginBottom: spacing.xs }]} />
        <View style={[styles.line, { width: '85%', height: 16, marginBottom: spacing.xs }]} />
        <View style={[styles.line, { width: '60%', height: 20, marginBottom: spacing.xs }]} />
        <View style={[styles.line, { width: '50%', height: 14 }]} />
      </View>
    </View>
  );
};

export const EmiPlanSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <View style={styles.emiContainer}>
      {Array.from({ length: count }).map((_, index) => (
        <View key={index} style={styles.emiCard}>
          <View style={styles.emiHeader}>
            <View style={[styles.line, { width: '30%', height: 18 }]} />
            <View style={[styles.line, { width: '25%', height: 18 }]} />
          </View>
          <View style={[styles.line, { width: '50%', height: 26, marginVertical: spacing.xs }]} />
          <View style={[styles.line, { width: '70%', height: 14 }]} />
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  productCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    marginBottom: spacing.md,
    flex: 1,
  },
  imagePlaceholder: {
    height: 140,
    backgroundColor: colors.surfaceSecondary,
  },
  content: {
    padding: spacing.sm,
  },
  line: {
    backgroundColor: '#E5E7EB',
    borderRadius: radius.chip,
  },
  emiContainer: {
    marginVertical: spacing.sm,
  },
  emiCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  emiHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
});
