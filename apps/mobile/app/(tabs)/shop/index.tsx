import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import { colors, spacing, typography } from '../../../src/theme';
import { SegmentedToggle } from '../../../src/features/marketplace/components/SegmentedToggle';
import { isMarketplaceEnabled } from '../../../src/features/marketplace/config/featureFlags';
import { STRINGS } from '../../../src/features/marketplace/constants/strings';
import MarketplaceHome from './marketplace';

export default function ShopScreen() {
  const tabs = isMarketplaceEnabled
    ? [STRINGS.TAB_TOP_BRANDS, STRINGS.TAB_NEARBY_STORES, STRINGS.TAB_1FI_MARKETPLACE]
    : [STRINGS.TAB_TOP_BRANDS, STRINGS.TAB_NEARBY_STORES];

  const [activeTab, setActiveTab] = useState<string>(
    isMarketplaceEnabled ? STRINGS.TAB_1FI_MARKETPLACE : STRINGS.TAB_TOP_BRANDS
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{STRINGS.SHOP_TITLE}</Text>
      </View>

      <SegmentedToggle
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {isMarketplaceEnabled && activeTab === STRINGS.TAB_1FI_MARKETPLACE ? (
        <MarketplaceHome />
      ) : (
        <View style={styles.outOfScopeContainer}>
          <Text style={styles.outOfScopeIcon}>
            {activeTab === STRINGS.TAB_TOP_BRANDS ? '🏷️' : '📍'}
          </Text>
          <Text style={styles.outOfScopeTitle}>{activeTab}</Text>
          <Text style={styles.outOfScopeSubtitle}>
            {STRINGS.OUT_OF_SCOPE_SUBTITLE}
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
