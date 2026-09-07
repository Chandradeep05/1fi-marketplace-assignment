import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';

export default function HomeScreen() {
  const router = useRouter();

  const showPlaceholder = (title: string, desc: string) => {
    Alert.alert(title, desc);
  };

  const brands = [
    { name: 'Apple', logo: '', color: '#111827' },
    { name: 'Reliance D...', logo: 'RD', color: '#0284C7' },
    { name: 'Croma', logo: 'croma', color: '#0F766E' },
    { name: 'Vijay Sales', logo: 'VS', color: '#DC2626' },
    { name: 'MakeMyTrip', logo: 'mmt', color: '#EA580C' },
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Hero Banner */}
        <View style={styles.heroCard}>
          <View style={styles.heroLeft}>
            <Text style={styles.heroBadge}>GET STARTED</Text>
            <Text style={styles.heroTitle}>
              Shop on <Text style={styles.goldText}>no-cost EMI</Text>
            </Text>
            <Text style={styles.heroSubtitle}>
              Backed by your mutual funds, No credit pull, No charges, & quick approval.
            </Text>
            <TouchableOpacity
              style={styles.ctaButton}
              activeOpacity={0.85}
              onPress={() =>
                showPlaceholder(
                  'Credit Line Eligibility',
                  'Instant credit line up to ₹5,00,000 is available against your mutual fund portfolio. Browse products in the Shop tab!'
                )
              }
            >
              <Text style={styles.ctaButtonText}>Check eligibility  →</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.heroRight}>
            <View style={styles.interestGraphic}>
              <Text style={styles.sparkle}>✨</Text>
              <Text style={styles.interestNumber}>0%</Text>
              <Text style={styles.interestText}>INTEREST</Text>
              <Text style={styles.confetti}>🎉</Text>
            </View>
          </View>
        </View>

        {/* Offers Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionBar} />
          <Text style={styles.sectionTitle}>OFFERS</Text>
        </View>

        <TouchableOpacity
          style={styles.offerCard}
          activeOpacity={0.9}
          onPress={() => router.push('/marketplace/iphone-17-pro' as any)}
        >
          <View style={styles.offerContent}>
            <Text style={styles.offerBadge}>APPLE FLAGSHIP DEAL</Text>
            <Text style={styles.offerTitle}>
              Upgrade to iPhone 17 Pro with Easy EMIs
            </Text>
            <View style={styles.offerPill}>
              <Text style={styles.offerPillText}>✓  Upto 24m no cost EMI</Text>
            </View>
          </View>
          <View style={styles.offerImageContainer}>
            <Image
              source={{
                uri: 'https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium?wid=5120&hei=2880&fmt=p-jpg',
              }}
              style={styles.phoneImage}
              resizeMode="contain"
            />
          </View>
        </TouchableOpacity>

        {/* Carousel Pagination Indicator */}
        <View style={styles.dotsRow}>
          <View style={styles.dot} />
          <View style={styles.dot} />
          <View style={styles.activeDot} />
          <View style={styles.dot} />
          <View style={styles.dot} />
        </View>

        {/* Top Brands Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionBar} />
          <Text style={styles.sectionTitle}>SHOP USING 1FI AT TOP BRANDS</Text>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.brandsScroll}
        >
          {brands.map((b, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.brandTile}
              activeOpacity={0.8}
              onPress={() => router.push('/(tabs)/shop' as any)}
            >
              <View style={[styles.brandLogoBox, { borderColor: '#E5E7EB' }]}>
                <Text style={[styles.brandLogoGlyph, { color: b.color }]}>
                  {b.logo}
                </Text>
              </View>
              <Text style={styles.brandName} numberOfLines={1}>
                {b.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Trust & Value Props */}
        <View style={styles.trustCard}>
          <View style={styles.trustItem}>
            <Text style={styles.trustIcon}>🛡️</Text>
            <View style={styles.trustTextCol}>
              <Text style={styles.trustTitle}>Zero Investment Impact</Text>
              <Text style={styles.trustSubtitle}>
                No tax, no exit load. Your mutual funds keep compounding.
              </Text>
            </View>
          </View>
          <View style={styles.trustDivider} />
          <View style={styles.trustItem}>
            <Text style={styles.trustIcon}>⚡</Text>
            <View style={styles.trustTextCol}>
              <Text style={styles.trustTitle}>Repay Only What You Borrow</Text>
              <Text style={styles.trustSubtitle}>
                Transparent 0% no-cost EMIs with instant digital clearance.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 90,
  },
  heroCard: {
    backgroundColor: '#20037A',
    borderRadius: 20,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    overflow: 'hidden',
    shadowColor: '#20037A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 10,
    elevation: 4,
  },
  heroLeft: {
    flex: 1,
    paddingRight: 10,
  },
  heroBadge: {
    fontSize: 10,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.75)',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    lineHeight: 28,
  },
  goldText: {
    color: '#FACC15',
  },
  heroSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.82)',
    lineHeight: 17,
    marginTop: 6,
  },
  ctaButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    paddingVertical: 9,
    paddingHorizontal: 18,
    alignSelf: 'flex-start',
    marginTop: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  ctaButtonText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#161422',
  },
  heroRight: {
    width: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  interestGraphic: {
    alignItems: 'center',
    justifyContent: 'center',
    transform: [{ rotate: '-6deg' }],
  },
  interestNumber: {
    fontSize: 34,
    fontWeight: '900',
    color: '#FFFFFF',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 1, height: 2 },
    textShadowRadius: 4,
  },
  interestText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#FACC15',
    letterSpacing: 1.5,
  },
  sparkle: {
    fontSize: 16,
    position: 'absolute',
    top: -12,
    left: -10,
  },
  confetti: {
    fontSize: 16,
    position: 'absolute',
    bottom: -10,
    right: -10,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 22,
    marginBottom: 12,
  },
  sectionBar: {
    width: 3.5,
    height: 16,
    backgroundColor: '#7C3AED',
    borderRadius: 2,
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#7C3AED',
    letterSpacing: 0.6,
  },
  offerCard: {
    backgroundColor: '#1E0D08',
    borderRadius: 20,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 140,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 3,
  },
  offerContent: {
    flex: 1,
    paddingRight: 8,
  },
  offerBadge: {
    fontSize: 10,
    fontWeight: '800',
    color: '#F59E0B',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  offerTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
    lineHeight: 23,
    marginBottom: 12,
  },
  offerPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 14,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  offerPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  offerImageContainer: {
    width: 90,
    height: 110,
    alignItems: 'center',
    justifyContent: 'center',
  },
  phoneImage: {
    width: 80,
    height: 110,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    marginBottom: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#D1D5DB',
  },
  activeDot: {
    width: 22,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7C3AED',
  },
  brandsScroll: {
    gap: 12,
    paddingVertical: 4,
  },
  brandTile: {
    alignItems: 'center',
    width: 68,
  },
  brandLogoBox: {
    width: 60,
    height: 60,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
    marginBottom: 6,
  },
  brandLogoGlyph: {
    fontSize: 18,
    fontWeight: '800',
  },
  brandName: {
    fontSize: 11,
    fontWeight: '600',
    color: '#4B5563',
    textAlign: 'center',
  },
  trustCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  trustItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  trustIcon: {
    fontSize: 22,
  },
  trustTextCol: {
    flex: 1,
  },
  trustTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#161422',
    marginBottom: 2,
  },
  trustSubtitle: {
    fontSize: 11,
    color: '#6B7280',
    lineHeight: 16,
  },
  trustDivider: {
    height: 1,
    backgroundColor: '#F3F4F6',
    marginVertical: 12,
  },
});
