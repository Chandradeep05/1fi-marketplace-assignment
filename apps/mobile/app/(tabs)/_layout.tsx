import React from 'react';
import { Tabs } from 'expo-router';
import { StyleSheet, View, Image, ImageSourcePropType } from 'react-native';
import { colors } from '../../src/theme';

const TAB_ICONS: Record<string, ImageSourcePropType> = {
  home: require('../../src/assets/icons/tab_home.png'),
  shop: require('../../src/assets/icons/tab_shop.png'),
  dues: require('../../src/assets/icons/tab_dues.png'),
  limit: require('../../src/assets/icons/tab_limit.png'),
  profile: require('../../src/assets/icons/tab_profile.png'),
};

interface TabIconProps {
  name: 'home' | 'shop' | 'dues' | 'limit' | 'profile';
  focused: boolean;
}

function TabIcon({ name, focused }: TabIconProps) {
  return (
    <View style={styles.tabIconWrapper}>
      {focused && <View style={styles.topIndicator} />}
      <Image
        source={TAB_ICONS[name]}
        style={[
          styles.tabIconImage,
          { tintColor: focused ? colors.primary : '#9CA3AF' },
        ]}
        resizeMode="contain"
      />
    </View>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarLabelStyle: styles.tabBarLabel,
        tabBarShowLabel: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ focused }) => <TabIcon name="home" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="shop"
        options={{
          title: 'Shop',
          tabBarIcon: ({ focused }) => <TabIcon name="shop" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="emi-dues"
        options={{
          title: 'EMI Dues',
          tabBarIcon: ({ focused }) => <TabIcon name="dues" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="limit"
        options={{
          title: 'Limit',
          tabBarIcon: ({ focused }) => <TabIcon name="limit" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ focused }) => <TabIcon name="profile" focused={focused} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    height: 68,
    paddingBottom: 8,
    paddingTop: 6,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 8,
  },
  tabBarLabel: {
    fontSize: 10,
    fontWeight: '700',
    marginTop: 2,
  },
  tabIconWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    paddingTop: 4,
  },
  topIndicator: {
    position: 'absolute',
    top: -6,
    width: 28,
    height: 3,
    backgroundColor: '#7C3AED',
    borderRadius: 2,
  },
  tabIconImage: {
    width: 24,
    height: 24,
  },
});
