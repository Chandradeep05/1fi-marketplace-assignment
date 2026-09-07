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

interface ActionItem {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  badge?: string;
}

export default function ProfileScreen() {
  const showNotice = (title: string) => {
    Alert.alert(
      title,
      'This section is outside the current 1Fi Marketplace assignment scope.'
    );
  };

  const quickActions: ActionItem[] = [
    {
      id: 'details',
      title: 'Profile details',
      subtitle: 'Name, contact and KYC info',
      icon: '👤',
    },
    {
      id: 'purchases',
      title: 'Purchases',
      subtitle: 'Orders, invoices and loan status',
      icon: '📦',
    },
    {
      id: 'pledge',
      title: 'Pledge history',
      subtitle: 'Funds you pledged or released',
      icon: '🐖',
    },
    {
      id: 'invite',
      title: 'Invite friends',
      subtitle: 'Share the app, earn rewards',
      icon: '👥',
      badge: 'EARN ₹500',
    },
    {
      id: 'support',
      title: 'Support & FAQs',
      subtitle: 'Find answers or contact us',
      icon: '❓',
    },
    {
      id: 'privacy',
      title: 'Privacy policy',
      subtitle: 'Data safety and security disclosures',
      icon: '🔒',
    },
    {
      id: 'terms',
      title: 'Terms & conditions',
      subtitle: 'Borrower agreement and legal terms',
      icon: '📄',
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
          <Text style={styles.headerSubtitle}>
            Manage your account settings and personal preferences.
          </Text>
        </View>

        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>U</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>User</Text>
            <Text style={styles.userPhone}>+91 XXXXXXXXXX</Text>
          </View>
        </View>

        {/* Quick Actions Title */}
        <Text style={styles.sectionHeader}>QUICK ACTIONS</Text>

        {/* Quick Actions List */}
        <View style={styles.actionsList}>
          {quickActions.map((action) => (
            <TouchableOpacity
              key={action.id}
              style={styles.actionCard}
              activeOpacity={0.7}
              onPress={() => showNotice(action.title)}
            >
              <View style={styles.actionIconBox}>
                <Text style={styles.actionIcon}>{action.icon}</Text>
              </View>
              <View style={styles.actionTextCol}>
                <Text style={styles.actionTitle}>{action.title}</Text>
                <Text style={styles.actionSubtitle}>{action.subtitle}</Text>
              </View>
              {action.badge && (
                <View style={styles.badgePill}>
                  <Text style={styles.badgeText}>{action.badge}</Text>
                </View>
              )}
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>
          ))}
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
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 20,
  },
  userCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  avatar: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: '#EDE9FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 22,
    fontWeight: '800',
    color: '#7C3AED',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#161422',
  },
  userPhone: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
    fontWeight: '500',
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: '#9CA3AF',
    letterSpacing: 0.8,
    marginTop: 24,
    marginBottom: 12,
  },
  actionsList: {
    gap: 10,
  },
  actionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
    borderWidth: 1,
    borderColor: '#E8E7ED',
  },
  actionIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#F5F3FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  actionIcon: {
    fontSize: 18,
  },
  actionTextCol: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#161422',
    marginBottom: 2,
  },
  actionSubtitle: {
    fontSize: 11,
    color: '#6B7280',
  },
  badgePill: {
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#7C3AED',
  },
  chevron: {
    fontSize: 20,
    color: '#9CA3AF',
    fontWeight: '600',
  },
});
