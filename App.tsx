import { useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StatusBar } from 'expo-status-bar';
import AuthScreen from './screens/AuthScreen';
import HomeScreen from './screens/HomeScreen';
import AccountsScreen from './screens/AccountsScreen';
import LedgerScreen from './screens/LedgerScreen';
import InventoryScreen from './screens/InventoryScreen';
import BottomTabBar from './components/BottomTabBar';
import { AuthProvider, useAuth } from './utils/authContext';
import { OnDeviceAIProvider } from './utils/OnDeviceAIProvider';
import type { AppTab } from './types/navigation';

function MainTabs() {
  const [activeTab, setActiveTab] = useState<AppTab>('home');

  return (
    <OnDeviceAIProvider>
      <View style={{ flex: 1 }}>
        <View style={{ flex: 1 }}>
          {activeTab === 'home' ? <HomeScreen /> : null}
          {activeTab === 'accounts' ? <AccountsScreen /> : null}
          {activeTab === 'ledger' ? <LedgerScreen /> : null}
          {activeTab === 'inventory' ? <InventoryScreen /> : null}
        </View>
        <BottomTabBar activeTab={activeTab} onChangeTab={setActiveTab} />
      </View>
    </OnDeviceAIProvider>
  );
}

function RootNavigator() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color="#4C6FFF" />
      </View>
    );
  }

  return session ? <MainTabs /> : <AuthScreen />;
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar style="auto" />
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
