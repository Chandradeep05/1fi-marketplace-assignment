import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SegmentedToggle } from '../../../src/features/marketplace/components/SegmentedToggle';
import { isMarketplaceEnabled } from '../../../src/features/marketplace/config/featureFlags';
import { STRINGS } from '../../../src/features/marketplace/constants/strings';
import MarketplaceHome from './marketplace';

export default function ShopScreen() {
  const tabs = isMarketplaceEnabled
    ? [STRINGS.TAB_TOP_BRANDS, STRINGS.TAB_NEARBY_STORES, STRINGS.TAB_1FI_MARKETPLACE]
    : [STRINGS.TAB_TOP_BRANDS, STRINGS.TAB_NEARBY_STORES];

  // Default to 1Fi Marketplace so the functional assignment is immediately front and center,
  // while allowing instant 1-tap switching to Top Brands and Nearby Stores.
  const [activeTab, setActiveTab] = useState<string>(
    isMarketplaceEnabled ? STRINGS.TAB_1FI_MARKETPLACE : STRINGS.TAB_TOP_BRANDS
  );

  const [brandSearch, setBrandSearch] = useState('');
  const [storeSearch, setStoreSearch] = useState('');

  const topBrands = [
    {
      id: 'air-india',
      name: 'Air India',
      subtitle: 'No-cost EMIs upto 18 months',
      badgeColor: '#E11D48',
      badgeText: 'AIR INDIA',
    },
    {
      id: 'apple-reseller',
      name: 'Apple Premium Reseller',
      subtitle: 'No-cost EMIs upto 24 months',
      badgeColor: '#111827',
      badgeText: ' Premium Reseller',
    },
    {
      id: 'caratlane',
      name: 'Caratlane',
      subtitle: 'No-cost EMIs upto 12 months',
      badgeColor: '#7E22CE',
      badgeText: 'CARATLANE',
    },
    {
      id: 'reliance-digital',
      name: 'Reliance Digital',
      subtitle: 'No-cost EMIs upto 24 months',
      badgeColor: '#0284C7',
      badgeText: 'Reliance Digital',
    },
    {
      id: 'croma',
      name: 'Croma',
      subtitle: 'No-cost EMIs upto 24 months',
      badgeColor: '#0F766E',
      badgeText: 'croma',
    },
  ];

  const nearbyStores = [
    {
      id: 'croma-indiranagar',
      name: 'Croma Megastore',
      subtitle: 'Indiranagar 100ft Road · 1.2 km away',
      tag: 'Pay via 1Fi QR',
    },
    {
      id: 'reliance-koramangala',
      name: 'Reliance Digital Plaza',
      subtitle: 'Koramangala 80ft Road · 2.4 km away',
      tag: 'Instant Checkout',
    },
    {
      id: 'vijay-hsr',
      name: 'Vijay Sales Electronics',
      subtitle: 'HSR Layout Sector 1 · 3.1 km away',
      tag: '0% EMI at Counter',
    },
  ];

  const handleBrandPress = (brandName: string) => {
    Alert.alert(
      brandName,
      'Partner store purchasing is available online. Switch to the 1Fi Marketplace tab to shop devices with instant mutual-fund backed EMIs!',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Go to 1Fi Marketplace',
          onPress: () => setActiveTab(STRINGS.TAB_1FI_MARKETPLACE),
        },
      ]
    );
  };

  const handleStorePress = (storeName: string) => {
    Alert.alert(
      storeName,
      'Physical store scan-to-pay QR checkout is presentation-only for this assignment.'
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Top Hero Banner — Matching Screenshot 1 */}
      <View style={styles.heroBanner}>
        <View style={styles.heroBadgePill}>
          <Text style={styles.heroBadgeText}>✨ NO-COST EMIs</Text>
        </View>
        <View style={styles.heroRow}>
          <View style={styles.heroTextCol}>
            <Text style={styles.heroHeading}>Shop today,</Text>
            <Text style={styles.heroHeadingItalic}>Pay later using</Text>
            <Text style={styles.heroHeadingBold}>Mutual funds.</Text>
            <Text style={styles.heroSubText}>
              No credit score required. No interest.{'\n'}Backed by your investments.
            </Text>
          </View>
          <View style={styles.heroGraphicBox}>
            <View style={styles.graphicBadge}>
              <Text style={styles.graphicEmoji}>🛍️</Text>
              <Text style={styles.graphicMini}>0%</Text>
            </View>
            <Text style={styles.confettiTop}>🎉</Text>
            <Text style={styles.confettiBottom}>✨</Text>
          </View>
        </View>
      </View>

      {/* Segmented Sub-Tab Switcher */}
      <SegmentedToggle
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Active Tab Content */}
      {isMarketplaceEnabled && activeTab === STRINGS.TAB_1FI_MARKETPLACE ? (
        <MarketplaceHome />
      ) : activeTab === STRINGS.TAB_TOP_BRANDS ? (
        <ScrollView
          style={styles.contentScroll}
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* Search Box */}
          <View style={styles.searchBox}>
            <Text style={styles.searchIcon}>🔍</Text>
            <TextInput
              style={styles.searchInput}
              placeholder="Search online stores..."
              placeholderTextColor="#9CA3AF"
              value={brandSearch}
              onChangeText={setBrandSearch}
            />
          </View>

          {/* Section Title */}
          <Text style={styles.sectionHeading}>Top Brands</Text>

          {/* Brand Cards */}
          <View style={styles.brandList}>
            {topBrands
              .filter((b) =>
                b.name.toLowerCase().includes(brandSearch.trim().toLowerCase())
              )
              .map((brand) => (
                <TouchableOpacity
                  key={brand.id}
                  style={styles.brandCard}
                  activeOpacity={0.8}
                  onPress={() => handleBrandPress(brand.name)}
                >
                  <View
                    style={[
                      styles.brandLogoContainer,
                      { backgroundColor: brand.badgeColor },
                    ]}
                  >
                    <Text style={styles.brandLogoText}>{brand.badgeText}</Text>
                  </View>
                  <View style={styles.brandInfo}>
                    <Text style={styles.brandTitle}>{brand.name}</Text>
                    <Text style={styles.brandSubtitle}>{brand.subtitle}</Text>
                  </View>
                </TouchableOpacity>
              ))}
          </View>
        </ScrollView>
      ) : (
        <ScrollView
          style={styles.contentScroll}
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* Search Box */}
          <View style={styles.searchBox}>
            <Text style={styles.searchIcon}>📍</Text>
            <TextInput
              style={styles.searchInput}
              placeholder="Search nearby stores..."
              placeholderTextColor="#9CA3AF"
              value={storeSearch}
              onChangeText={setStoreSearch}
            />
          </View>

          {/* Section Title */}
          <Text style={styles.sectionHeading}>Nearby Stores</Text>

          {/* Store Cards */}
          <View style={styles.brandList}>
            {nearbyStores
              .filter((s) =>
                s.name.toLowerCase().includes(storeSearch.trim().toLowerCase())
              )
              .map((store) => (
                <TouchableOpacity
                  key={store.id}
                  style={styles.brandCard}
                  activeOpacity={0.8}
                  onPress={() => handleStorePress(store.name)}
                >
                  <View
                    style={[
                      styles.brandLogoContainer,
                      { backgroundColor: '#4F46E5' },
                    ]}
                  >
                    <Text style={styles.brandLogoText}>🏬</Text>
                  </View>
                  <View style={styles.brandInfo}>
                    <Text style={styles.brandTitle}>{store.name}</Text>
                    <Text style={styles.brandSubtitle}>{store.subtitle}</Text>
                  </View>
                  <View style={styles.storePill}>
                    <Text style={styles.storePillText}>{store.tag}</Text>
                  </View>
                </TouchableOpacity>
              ))}
          </View>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  heroBanner: {
    backgroundColor: '#1E0A8A',
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 16,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  heroBadgePill: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 14,
    alignSelf: 'flex-start',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  heroBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  heroRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  heroTextCol: {
    flex: 1,
    paddingRight: 10,
  },
  heroHeading: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    lineHeight: 26,
  },
  heroHeadingItalic: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    fontStyle: 'italic',
    lineHeight: 25,
  },
  heroHeadingBold: {
    fontSize: 22,
    fontWeight: '900',
    color: '#FFFFFF',
    lineHeight: 27,
  },
  heroSubText: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.82)',
    lineHeight: 15,
    marginTop: 6,
  },
  heroGraphicBox: {
    width: 80,
    height: 80,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  graphicBadge: {
    width: 60,
    height: 60,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  graphicEmoji: {
    fontSize: 26,
  },
  graphicMini: {
    fontSize: 10,
    fontWeight: '900',
    color: '#FACC15',
    position: 'absolute',
    bottom: 4,
    right: 6,
  },
  confettiTop: {
    position: 'absolute',
    top: 0,
    right: 2,
    fontSize: 14,
  },
  confettiBottom: {
    position: 'absolute',
    bottom: 2,
    left: 2,
    fontSize: 14,
  },
  contentScroll: {
    flex: 1,
  },
  scrollContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 90,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  searchIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: '#161422',
    padding: 0,
  },
  sectionHeading: {
    fontSize: 20,
    fontWeight: '800',
    color: '#161422',
    marginBottom: 12,
  },
  brandList: {
    gap: 12,
  },
  brandCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  brandLogoContainer: {
    width: 60,
    height: 60,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 4,
    marginRight: 14,
  },
  brandLogoText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 10,
    textAlign: 'center',
  },
  brandInfo: {
    flex: 1,
  },
  brandTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#161422',
    marginBottom: 3,
  },
  brandSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  storePill: {
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  storePillText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#7C3AED',
  },
});
