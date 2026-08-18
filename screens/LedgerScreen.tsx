import { useEffect, useState } from 'react';
import { FlatList, Pressable, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import AddCustomerComposer from '../components/AddCustomerComposer';
import { listCustomers } from '../db/queries';
import type { CustomerLedgerEntry } from '../types/ledger';
import { useAuth } from '../utils/authContext';
import { formatAmount } from '../utils/currency';
import { useShopData } from '../utils/shopDataContext';
import { styles } from './LedgerScreen.styles';

function CustomerRow({ customer }: { customer: CustomerLedgerEntry }) {
  const isSettled = customer.balanceAmount <= 0;
  return (
    <View style={styles.row}>
      <Text style={styles.customerName}>{customer.name}</Text>
      <View style={styles.balanceWrap}>
        <Text style={[styles.balance, isSettled && styles.balanceSettled]}>
          {formatAmount(customer.balanceAmount)}
        </Text>
        <Text style={styles.balanceLabel}>{isSettled ? 'Settled' : 'Outstanding'}</Text>
      </View>
    </View>
  );
}

export default function LedgerScreen() {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { dataVersion } = useShopData();
  const [customers, setCustomers] = useState<CustomerLedgerEntry[]>([]);
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    if (!user) {
      setCustomers([]);
      return;
    }
    void listCustomers(db, user.id).then(setCustomers);
  }, [db, user, dataVersion]);

  if (isAdding) {
    return <AddCustomerComposer onClose={() => setIsAdding(false)} />;
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Ledger</Text>
          <Text style={styles.subtitle}>Customers and their balances</Text>
        </View>
      </View>

      <FlatList
        data={customers}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => <CustomerRow customer={item} />}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No customers yet.</Text>
        }
      />

      <View style={styles.footer}>
        <Text style={styles.statusText}>Tap to add a customer</Text>
        <Pressable
          onPress={() => setIsAdding(true)}
          accessibilityLabel="Add customer"
          style={({ pressed }) => [styles.addButton, pressed && styles.addButtonPressed]}
        >
          <Text style={styles.addButtonText}>+</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}
