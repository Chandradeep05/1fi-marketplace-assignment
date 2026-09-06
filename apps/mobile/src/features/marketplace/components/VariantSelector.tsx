import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ProductVariant } from '@1fi/contracts';
import { colors, radius, spacing, typography } from '../../../theme';

interface VariantSelectorProps {
  variants: ProductVariant[];
  selectedVariantId: string | null;
  onSelectVariant: (variantId: string) => void;
}

export const VariantSelector: React.FC<VariantSelectorProps> = ({
  variants,
  selectedVariantId,
  onSelectVariant,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>Select Variant</Text>
      <View style={styles.variantList}>
        {variants.map((v) => {
          const isSelected = selectedVariantId === v.id;
          const label = Object.values(v.attributes).join(' · ');
          const isAvailable = v.available;

          return (
            <TouchableOpacity
              key={v.id}
              style={[
                styles.variantPill,
                isSelected && styles.selectedPill,
                !isAvailable && styles.disabledPill,
              ]}
              onPress={() => isAvailable && onSelectVariant(v.id)}
              disabled={!isAvailable}
              activeOpacity={0.8}
              accessibilityRole="radio"
              accessibilityState={{ selected: isSelected, disabled: !isAvailable }}
              accessibilityLabel={`${label}${!isAvailable ? ' - Out of stock' : ''}`}
            >
              <Text
                style={[
                  styles.variantText,
                  isSelected && styles.selectedText,
                  !isAvailable && styles.disabledText,
                ]}
              >
                {label} {!isAvailable && '(Out of stock)'}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: spacing.md,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  variantList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  variantPill: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  selectedPill: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  disabledPill: {
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    opacity: 0.6,
  },
  variantText: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
  },
  selectedText: {
    color: colors.primaryDark,
    fontWeight: '700',
  },
  disabledText: {
    color: colors.textSecondary,
    textDecorationLine: 'line-through',
  },
});
