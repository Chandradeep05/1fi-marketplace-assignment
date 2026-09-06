import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import { colors, spacing, typography } from '../../../src/theme';
import { SegmentedToggle } from '../../../src/features/marketplace/components/SegmentedToggle';
import MarketplaceHome from './marketplace';

export default function ShopScreen() {
  const tabs = ['Top Brands', 'Nearby Stores', '1Fi Marketplace'];
  const [activeTab, setActiveTab] = useState<string>('1Fi Marketplace');

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Shop</Text>
      </View>

      <SegmentedToggle
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {activeTab === '1Fi Marketplace' ? (
        <MarketplaceHome />
      ) : (
        <View style={styles.outOfScopeContainer}>
          <Text style={styles.outOfScopeIcon}>
            {activeTab === 'Top Brands' ? '🏷️' : '📍'}
          </Text>
          <Text style={styles.outOfScopeTitle}>{activeTab}</Text>
          <Text style={styles.outOfScopeSubtitle}>
            Browse online products with instant EMI in the 1Fi Marketplace tab.
          </Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xs,
  },
  headerTitle: {
    ...typography.displayBold,
    color: colors.textPrimary,
  },
  outOfScopeContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  outOfScopeIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  outOfScopeTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  outOfScopeSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});
