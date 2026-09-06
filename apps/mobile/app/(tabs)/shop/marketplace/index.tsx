import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { colors, spacing, typography, radius } from '../../../../src/theme';
import { SearchBar } from '../../../../src/features/marketplace/components/SearchBar';
import { EligibilityStrip } from '../../../../src/features/marketplace/components/EligibilityStrip';
import { CategoryChips } from '../../../../src/features/marketplace/components/CategoryChips';
import { ProductCard } from '../../../../src/features/marketplace/components/ProductCard';
import { ProductCardSkeleton } from '../../../../src/features/marketplace/components/Skeleton';
import { useCategories } from '../../../../src/features/marketplace/hooks/useCategories';
import { useProducts } from '../../../../src/features/marketplace/hooks/useProducts';
import { useMarketplaceStore } from '../../../../src/features/marketplace/state/useMarketplaceStore';

export default function MarketplaceHome() {
  const router = useRouter();
  const setActiveProduct = useMarketplaceStore((s) => s.setActiveProduct);

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // 350ms debounce on search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data: categoriesData } = useCategories();
  const {
    data: productsData,
    isLoading,
    isError,
    refetch,
    isRefetching,
  } = useProducts({
    category: selectedCategory || undefined,
    search: debouncedSearch || undefined,
  });

  const categories = categoriesData?.data || [];
  const products = productsData?.data || [];

  const handleProductPress = (product: any) => {
    setActiveProduct(product);
    router.push(`/shop/marketplace/${product.id}` as any);
  };

  return (
    <View style={styles.container}>
      <SearchBar
        value={searchTerm}
        onChangeText={setSearchTerm}
        placeholder="Search 1Fi Marketplace..."
      />

      <EligibilityStrip />

      {categories.length > 0 && (
        <CategoryChips
          categories={categories}
          selectedCategoryId={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />
      )}

      {isLoading ? (
        <View style={styles.grid}>
          {Array.from({ length: 6 }).map((_, i) => (
            <View key={i} style={styles.columnWrapper}>
              <ProductCardSkeleton />
            </View>
          ))}
        </View>
      ) : isError ? (
        <View style={styles.centerContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Unable to load products</Text>
          <Text style={styles.errorSubtitle}>Please check your connection and try again.</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : products.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyTitle}>No products found</Text>
          <Text style={styles.emptySubtitle}>
            {debouncedSearch
              ? `No matches found for "${debouncedSearch}".`
              : 'No products in this category yet.'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item.id}
          numColumns={2}
          contentContainerStyle={styles.listContent}
          columnWrapperStyle={styles.rowWrapper}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} colors={[colors.primary]} />
          }
          renderItem={({ item }) => (
            <View style={styles.columnWrapper}>
              <ProductCard product={item} onPress={() => handleProductPress(item)} />
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xl,
  },
  rowWrapper: {
    gap: spacing.md,
  },
  columnWrapper: {
    flex: 1,
    maxWidth: '50%',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: spacing.md,
    gap: spacing.md,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  errorIcon: {
    fontSize: 40,
    marginBottom: spacing.sm,
  },
  errorTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  errorSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  retryButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
  },
  retryText: {
    ...typography.buttonLabel,
    color: colors.textOnPrimary,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: spacing.sm,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  emptySubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});
