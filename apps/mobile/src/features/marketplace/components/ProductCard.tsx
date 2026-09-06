import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { Product } from '@1fi/contracts';
import { colors, radius, spacing, typography } from '../../../theme';
import { formatPaisa, formatSavings } from '../utils/formatMoney';

interface ProductCardProps {
  product: Product;
  onPress: () => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onPress }) => {
  const imageUrl = product.images?.[0]?.url || product.variants?.[0]?.image_url;
  const savings = formatSavings(product.mrp_paisa, product.base_price_paisa);

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.85}
      accessibilityRole="button"
      accessibilityLabel={`${product.name} by ${product.brand.name}, Price ${formatPaisa(product.base_price_paisa)}`}
    >
      <View style={styles.imageContainer}>
        {imageUrl ? (
          <Image
            source={{ uri: imageUrl }}
            style={styles.image}
            resizeMode="cover"
          />
        ) : (
          <View style={styles.placeholderImage}>
            <Text style={styles.placeholderText}>📦</Text>
          </View>
        )}
        {savings && (
          <View style={styles.savingsBadge}>
            <Text style={styles.savingsText}>{savings}</Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        <Text style={styles.brand}>{product.brand.name}</Text>
        <Text style={styles.title} numberOfLines={2}>
          {product.name}
        </Text>

        <View style={styles.priceRow}>
          <Text style={styles.price}>{formatPaisa(product.base_price_paisa)}</Text>
          {product.mrp_paisa && product.mrp_paisa > product.base_price_paisa && (
            <Text style={styles.mrp}>{formatPaisa(product.mrp_paisa)}</Text>
          )}
        </View>

        <View style={styles.emiBadge}>
          <Text style={styles.emiBadgeText}>No-Cost EMI Available</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    marginBottom: spacing.md,
    flex: 1,
  },
  imageContainer: {
    height: 140,
    backgroundColor: colors.surfaceSecondary,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 32,
  },
  savingsBadge: {
    position: 'absolute',
    bottom: spacing.xs,
    left: spacing.xs,
    backgroundColor: colors.success,
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: 2,
    borderRadius: radius.chip,
  },
  savingsText: {
    ...typography.captionSmall,
    color: colors.textOnPrimary,
  },
  content: {
    padding: spacing.sm,
  },
  brand: {
    ...typography.captionSmall,
    color: colors.textSecondary,
    textTransform: 'uppercase',
  },
  title: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    marginTop: 2,
    minHeight: 38,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  price: {
    ...typography.h3,
    color: colors.textPrimary,
    fontWeight: '700',
  },
  mrp: {
    ...typography.caption,
    color: colors.textSecondary,
    textDecorationLine: 'line-through',
  },
  emiBadge: {
    backgroundColor: colors.primaryLight,
    paddingVertical: 3,
    paddingHorizontal: spacing.xs,
    borderRadius: radius.chip,
    marginTop: spacing.xs,
    alignSelf: 'flex-start',
  },
  emiBadgeText: {
    ...typography.captionSmall,
    color: colors.primaryDark,
  },
});
