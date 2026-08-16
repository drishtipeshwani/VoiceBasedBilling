import { useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StatusBar } from 'expo-status-bar';
import { SQLiteProvider } from 'expo-sqlite';
import AuthScreen from './screens/AuthScreen';
import HomeScreen from './screens/HomeScreen';
import AccountsScreen from './screens/AccountsScreen';
import LedgerScreen from './screens/LedgerScreen';
import InventoryScreen from './screens/InventoryScreen';
import BottomTabBar from './components/BottomTabBar';
import { migrateDbIfNeeded } from './db/schema';
import { AuthProvider, useAuth } from './utils/authContext';
import { OnDeviceAIProvider } from './utils/OnDeviceAIProvider';
import { ShopDataProvider } from './utils/shopDataContext';
import type { AppTab } from './types/navigation';

function MainTabs() {
  const [activeTab, setActiveTab] = useState<AppTab>('home');

  return (
    <View style={{ flex: 1 }}>
      <View style={{ flex: 1 }}>
        {activeTab === 'home' ? <HomeScreen /> : null}
        {activeTab === 'accounts' ? <AccountsScreen /> : null}
        {activeTab === 'ledger' ? <LedgerScreen /> : null}
        {activeTab === 'inventory' ? <InventoryScreen /> : null}
      </View>
      <BottomTabBar activeTab={activeTab} onChangeTab={setActiveTab} />
    </View>
  );
}

function RootNavigator() {
  const { unlocked, loading, hasRegisteredUser } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color="#4C6FFF" />
      </View>
    );
  }

  if (!hasRegisteredUser) {
    return <AuthScreen />;
  }

  return (
    <View style={{ flex: 1 }}>
      <MainTabs />
      {!unlocked ? (
        <View style={styles.lockOverlay}>
          <AuthScreen />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  lockOverlay: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: 10,
  },
});

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar style="auto" />
        <SQLiteProvider databaseName="voicebilling.db" onInit={migrateDbIfNeeded}>
          <AuthProvider>
            <ShopDataProvider>
              <OnDeviceAIProvider>
                <RootNavigator />
              </OnDeviceAIProvider>
            </ShopDataProvider>
          </AuthProvider>
        </SQLiteProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
