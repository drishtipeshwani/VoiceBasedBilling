import { useEffect, useState } from 'react';
import { FlatList, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import { listInvoices } from '../db/queries';
import type { InvoiceSummary } from '../types/accounts';
import { useAuth } from '../utils/authContext';
import { formatAmount } from '../utils/currency';
import { useShopData } from '../utils/shopDataContext';
import { styles } from './AccountsScreen.styles';

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function InvoiceRow({ invoice }: { invoice: InvoiceSummary }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        <Text style={styles.invoiceNumber}>#{invoice.invoiceNumber}</Text>
        <Text style={styles.customerName}>{invoice.customerName}</Text>
        <Text style={styles.date}>{formatDate(invoice.date)}</Text>
      </View>
      <Text style={styles.amount}>{formatAmount(invoice.totalAmount)}</Text>
    </View>
  );
}

export default function AccountsScreen() {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { dataVersion } = useShopData();
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);

  useEffect(() => {
    if (!user) {
      setInvoices([]);
      return;
    }
    void listInvoices(db, user.id).then(setInvoices);
  }, [db, user, dataVersion]);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>Accounts</Text>
        <Text style={styles.subtitle}>Your saved invoices</Text>
      </View>

      <FlatList
        data={invoices}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => <InvoiceRow invoice={item} />}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No invoices saved yet.</Text>
        }
      />
    </SafeAreaView>
  );
}
