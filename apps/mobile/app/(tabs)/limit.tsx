import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
} from 'react-native';

export default function LimitScreen() {
  const showNotice = (feature: string) => {
    Alert.alert(
      feature,
      'Portfolio limit valuation is handled by 1Fi backend underwriting. This screen is presentation-only for the Marketplace assignment.'
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Credit Limit</Text>
          <Text style={styles.headerSubtitle}>
            Mutual fund portfolio valuation and credit line.
          </Text>
        </View>

        {/* Limit Card */}
        <View style={styles.limitCard}>
          <Text style={styles.limitBadge}>AVAILABLE CREDIT LINE</Text>
          <Text style={styles.limitAmount}>₹5,00,000</Text>
          <Text style={styles.limitSub}>0% interest on eligible merchant tenures</Text>

          <View style={styles.divider} />

          <View style={styles.statGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Pledged Portfolio</Text>
              <Text style={styles.statVal}>₹10,50,000</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Max LTV</Text>
              <Text style={styles.statVal}>50%</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Utilized</Text>
              <Text style={styles.statVal}>₹0</Text>
            </View>
          </View>
        </View>

        {/* Portfolio Security Card */}
        <View style={styles.infoCard}>
          <Text style={styles.infoIcon}>🌱</Text>
          <View style={styles.infoTextCol}>
            <Text style={styles.infoTitle}>Compounding Stays Intact</Text>
            <Text style={styles.infoSub}>
              Your mutual fund units remain invested in the market. You continue to earn all dividends and market growth while enjoying instant EMI credit.
            </Text>
          </View>
        </View>

        {/* Action Button */}
        <TouchableOpacity
          style={styles.ctaBtn}
          activeOpacity={0.85}
          onPress={() => showNotice('Increase Limit')}
        >
          <Text style={styles.ctaBtnText}>Increase Limit with More Mutual Funds →</Text>
        </TouchableOpacity>
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
    paddingTop: 16,
    paddingBottom: 90,
  },
  header: {
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#161422',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 20,
  },
  limitCard: {
    backgroundColor: '#1E0A8A',
    borderRadius: 20,
    padding: 20,
    shadowColor: '#1E0A8A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 4,
  },
  limitBadge: {
    fontSize: 10,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.75)',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  limitAmount: {
    fontSize: 34,
    fontWeight: '900',
    color: '#FFFFFF',
  },
  limitSub: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.82)',
    marginTop: 4,
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    marginVertical: 16,
  },
  statGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
    marginBottom: 4,
  },
  statVal: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  infoIcon: {
    fontSize: 24,
  },
  infoTextCol: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#161422',
    marginBottom: 4,
  },
  infoSub: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 18,
  },
  ctaBtn: {
    backgroundColor: '#7C3AED',
    borderRadius: 14,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 20,
    shadowColor: '#7C3AED',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
  },
  ctaBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
