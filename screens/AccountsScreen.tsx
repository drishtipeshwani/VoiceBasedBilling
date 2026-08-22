import { useEffect, useState } from 'react';
import { FlatList, Pressable, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import InvoiceComposer from '../components/InvoiceComposer';
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

function InvoiceRow({
  invoice,
  onPress,
}: {
  invoice: InvoiceSummary;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Edit invoice ${invoice.invoiceNumber}`}
      style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
    >
      <View style={styles.rowLeft}>
        <Text style={styles.invoiceNumber}>#{invoice.invoiceNumber}</Text>
        <Text style={styles.customerName}>{invoice.customerName}</Text>
        <Text style={styles.date}>{formatDate(invoice.date)}</Text>
      </View>
      <Text style={styles.amount}>{formatAmount(invoice.totalAmount)}</Text>
    </Pressable>
  );
}

export default function AccountsScreen() {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { dataVersion } = useShopData();
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setInvoices([]);
      return;
    }
    void listInvoices(db, user.id).then(setInvoices);
  }, [db, user, dataVersion]);

  if (selectedInvoiceId) {
    return (
      <InvoiceComposer
        existingInvoiceId={selectedInvoiceId}
        onClose={() => setSelectedInvoiceId(null)}
      />
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Accounts</Text>
          <Text style={styles.subtitle}>Your saved invoices</Text>
        </View>
      </View>

      <FlatList
        data={invoices}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <InvoiceRow invoice={item} onPress={() => setSelectedInvoiceId(item.id)} />
        )}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No invoices saved yet.</Text>
        }
      />
    </SafeAreaView>
  );
}
