import { useEffect, useState } from 'react';
import { FlatList, Pressable, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import AddCustomerComposer from '../components/AddCustomerComposer';
import InvoiceComposer from '../components/InvoiceComposer';
import { listCustomers, listInvoices } from '../db/queries';
import type { InvoiceSummary } from '../types/accounts';
import type { CustomerLedgerEntry } from '../types/ledger';
import { useAuth } from '../utils/authContext';
import { formatAmount } from '../utils/currency';
import { useShopData } from '../utils/shopDataContext';
import { styles } from './LedgerScreen.styles';

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function CustomerRow({
  customer,
  onPress,
}: {
  customer: CustomerLedgerEntry;
  onPress: () => void;
}) {
  const isSettled = customer.balanceAmount <= 0;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`View invoices for ${customer.name}`}
      style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
    >
      <Text style={styles.customerName}>{customer.name}</Text>
      <View style={styles.balanceWrap}>
        <Text style={[styles.balance, isSettled && styles.balanceSettled]}>
          {formatAmount(customer.balanceAmount)}
        </Text>
        <Text style={styles.balanceLabel}>{isSettled ? 'Settled' : 'Outstanding'}</Text>
      </View>
    </Pressable>
  );
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
      accessibilityLabel={`Open invoice ${invoice.invoiceNumber}`}
      style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
    >
      <View style={styles.rowLeft}>
        <Text style={styles.invoiceNumber}>#{invoice.invoiceNumber}</Text>
        <Text style={styles.date}>{formatDate(invoice.date)}</Text>
      </View>
      <Text style={styles.amount}>{formatAmount(invoice.totalAmount)}</Text>
    </Pressable>
  );
}

function CustomerInvoicesView({
  customer,
  invoices,
  onBack,
  onEdit,
  onSelectInvoice,
}: {
  customer: CustomerLedgerEntry;
  invoices: InvoiceSummary[];
  onBack: () => void;
  onEdit: () => void;
  onSelectInvoice: (invoiceId: string) => void;
}) {
  const isSettled = customer.balanceAmount <= 0;
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>{customer.name}</Text>
          <Text style={styles.subtitle}>
            {formatAmount(customer.balanceAmount)} {isSettled ? 'Settled' : 'Outstanding'}
          </Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable
            onPress={onBack}
            accessibilityLabel="Back to customers"
            style={({ pressed }) => [styles.headerButton, pressed && styles.headerButtonPressed]}
          >
            <Text style={styles.headerButtonText}>Back</Text>
          </Pressable>
          <Pressable
            onPress={onEdit}
            accessibilityLabel={`Edit customer ${customer.name}`}
            style={({ pressed }) => [styles.headerButton, pressed && styles.headerButtonPressed]}
          >
            <Text style={styles.headerButtonText}>Edit</Text>
          </Pressable>
        </View>
      </View>

      <FlatList
        data={invoices}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <InvoiceRow invoice={item} onPress={() => onSelectInvoice(item.id)} />
        )}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No invoices for this customer yet.</Text>
        }
      />
    </SafeAreaView>
  );
}

export default function LedgerScreen() {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { dataVersion } = useShopData();
  const [customers, setCustomers] = useState<CustomerLedgerEntry[]>([]);
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerLedgerEntry | null>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const [composerTarget, setComposerTarget] = useState<'new' | CustomerLedgerEntry | null>(
    null,
  );

  useEffect(() => {
    if (!user) {
      setCustomers([]);
      return;
    }
    void listCustomers(db, user.id).then((next) => {
      setCustomers(next);
      setSelectedCustomer((current) =>
        current ? (next.find((customer) => customer.id === current.id) ?? null) : null,
      );
    });
  }, [db, user, dataVersion]);

  useEffect(() => {
    if (!user || !selectedCustomer) {
      setInvoices([]);
      return;
    }
    void listInvoices(db, user.id, selectedCustomer.id).then(setInvoices);
  }, [db, user, dataVersion, selectedCustomer]);

  if (selectedInvoiceId) {
    return (
      <InvoiceComposer
        existingInvoiceId={selectedInvoiceId}
        onClose={() => setSelectedInvoiceId(null)}
      />
    );
  }

  if (composerTarget) {
    return (
      <AddCustomerComposer
        existingCustomer={composerTarget === 'new' ? undefined : composerTarget}
        onClose={() => setComposerTarget(null)}
      />
    );
  }

  if (selectedCustomer) {
    return (
      <CustomerInvoicesView
        customer={selectedCustomer}
        invoices={invoices}
        onBack={() => setSelectedCustomer(null)}
        onEdit={() => setComposerTarget(selectedCustomer)}
        onSelectInvoice={setSelectedInvoiceId}
      />
    );
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
        renderItem={({ item }) => (
          <CustomerRow customer={item} onPress={() => setSelectedCustomer(item)} />
        )}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No customers yet.</Text>
        }
      />

      <View style={styles.footer}>
        <Text style={styles.statusText}>Tap a customer to view invoices</Text>
        <Pressable
          onPress={() => setComposerTarget('new')}
          accessibilityLabel="Add customer"
          style={({ pressed }) => [styles.addButton, pressed && styles.addButtonPressed]}
        >
          <Text style={styles.addButtonText}>+</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}
