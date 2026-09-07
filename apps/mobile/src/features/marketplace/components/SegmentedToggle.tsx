import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, radius, spacing, typography } from '../../../theme';

interface SegmentedToggleProps {
  tabs: string[];
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const SegmentedToggle: React.FC<SegmentedToggleProps> = ({
  tabs,
  activeTab,
  onTabChange,
}) => {
  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const isActive = tab === activeTab;
        return (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, isActive && styles.activeTab]}
            onPress={() => onTabChange(tab)}
            activeOpacity={0.8}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
          >
            <Text
              style={[styles.tabText, isActive && styles.activeTabText]}
              numberOfLines={1}
            >
              {tab}
            </Text>
            {isActive && <View style={styles.indicator} />}
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#F3F0FA',
    borderRadius: 32,
    padding: 4,
    marginHorizontal: spacing.md,
    marginVertical: spacing.sm,
    borderWidth: 1,
    borderColor: '#E8E4F5',
  },
  tab: {
    flex: 1,
    paddingVertical: 9,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 28,
  },
  activeTab: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#5B21B6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    textAlign: 'center',
  },
  activeTabText: {
    color: '#5B21B6',
    fontWeight: '800',
  },
  indicator: {
    width: 24,
    height: 3,
    backgroundColor: '#5B21B6',
    borderRadius: 2,
    marginTop: 3,
  },
});
