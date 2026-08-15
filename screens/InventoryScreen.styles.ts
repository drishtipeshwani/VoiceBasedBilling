import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#1C1C28',
  },
  subtitle: {
    fontSize: 14,
    color: '#6E6E80',
    marginTop: 4,
  },
  listContent: {
    padding: 20,
    paddingTop: 12,
    gap: 12,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C28',
  },
  quantity: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4C6FFF',
  },
  divider: {
    height: 1,
    backgroundColor: '#EEEEF2',
    marginVertical: 12,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  priceBlock: {
    flex: 1,
  },
  priceLabel: {
    fontSize: 11,
    color: '#A0A0B2',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  priceValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1C1C28',
    marginTop: 2,
  },
  emptyText: {
    textAlign: 'center',
    color: '#A0A0B2',
    fontSize: 14,
    marginTop: 40,
  },
});
