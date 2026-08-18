import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  ScrollView,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import InvoiceCard from '../components/InvoiceCard';
import { getInvoiceById, listInvoices } from '../db/queries';
import type { InvoiceSummary, SavedInvoice } from '../types/accounts';
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
      accessibilityLabel={`Open invoice ${invoice.invoiceNumber}`}
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

function InvoiceDetailView({
  invoiceId,
  onClose,
}: {
  invoiceId: string;
  onClose: () => void;
}) {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const [saved, setSaved] = useState<SavedInvoice | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!user) {
      setSaved(null);
      return;
    }

    let cancelled = false;
    void getInvoiceById(db, user.id, invoiceId).then((result) => {
      if (cancelled) return;
      setSaved(result);
      setLoadError(result == null);
    });

    return () => {
      cancelled = true;
    };
  }, [db, invoiceId, user]);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>
            {saved ? `Invoice #${saved.invoiceNumber}` : 'Invoice'}
          </Text>
          <Text style={styles.subtitle}>Saved bill</Text>
        </View>
        <Pressable
          onPress={onClose}
          accessibilityLabel="Back to invoices"
          style={({ pressed }) => [styles.backButton, pressed && styles.backButtonPressed]}
        >
          <Text style={styles.backText}>Back</Text>
        </Pressable>
      </View>

      {saved ? (
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <InvoiceCard invoice={saved.invoice} />
        </ScrollView>
      ) : (
        <View style={styles.centered}>
          {loadError ? (
            <Text style={styles.errorText}>Could not open this invoice.</Text>
          ) : (
            <ActivityIndicator size="large" color="#4C6FFF" />
          )}
        </View>
      )}
    </SafeAreaView>
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
      <InvoiceDetailView
        invoiceId={selectedInvoiceId}
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
