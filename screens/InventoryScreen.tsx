import { useEffect, useState } from 'react';
import { FlatList, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSQLiteContext } from 'expo-sqlite';
import { listStockItems } from '../db/queries';
import type { StockItem } from '../types/stock';
import { useAuth } from '../utils/authContext';
import { formatAmount } from '../utils/currency';
import { useShopData } from '../utils/shopDataContext';
import { styles } from './InventoryScreen.styles';

function StockItemCard({ item }: { item: StockItem }) {
  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <Text style={styles.itemName}>{item.name}</Text>
        <Text style={styles.quantity}>{item.quantity} in stock</Text>
      </View>
      <View style={styles.divider} />
      <View style={styles.bottomRow}>
        <View style={styles.priceBlock}>
          <Text style={styles.priceLabel}>Cost Price</Text>
          <Text style={styles.priceValue}>{formatAmount(item.costPrice)}</Text>
        </View>
        <View style={styles.priceBlock}>
          <Text style={styles.priceLabel}>Selling Price</Text>
          <Text style={styles.priceValue}>{formatAmount(item.sellingPrice)}</Text>
        </View>
      </View>
    </View>
  );
}

export default function InventoryScreen() {
  const db = useSQLiteContext();
  const { user } = useAuth();
  const { dataVersion } = useShopData();
  const [items, setItems] = useState<StockItem[]>([]);

  useEffect(() => {
    if (!user) {
      setItems([]);
      return;
    }
    void listStockItems(db, user.id).then(setItems);
  }, [db, user, dataVersion]);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>Inventory</Text>
        <Text style={styles.subtitle}>Stock items on hand</Text>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => <StockItemCard item={item} />}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No stock items yet.</Text>
        }
      />
    </SafeAreaView>
  );
}
