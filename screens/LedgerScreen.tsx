import { FlatList, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { dummyCustomers } from '../data/dummyCustomers';
import type { CustomerLedgerEntry } from '../types/ledger';
import { formatAmount } from '../utils/currency';
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
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>Ledger</Text>
        <Text style={styles.subtitle}>Customers and their balances</Text>
      </View>

      <FlatList
        data={dummyCustomers}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => <CustomerRow customer={item} />}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No customers yet.</Text>
        }
      />
    </SafeAreaView>
  );
}
