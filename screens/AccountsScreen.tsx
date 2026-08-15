import { FlatList, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { dummyInvoices } from '../data/dummyInvoices';
import type { InvoiceSummary } from '../types/accounts';
import { formatAmount } from '../utils/currency';
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
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>Accounts</Text>
        <Text style={styles.subtitle}>Your saved invoices</Text>
      </View>

      <FlatList
        data={dummyInvoices}
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
