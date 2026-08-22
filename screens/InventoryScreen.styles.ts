import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F6FA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerText: {
    flex: 1,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  statusText: {
    fontSize: 14,
    color: '#6E6E80',
    marginBottom: 14,
  },
  addButton: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: '#4C6FFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#4C6FFF',
    shadowOpacity: 0.4,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  addButtonPressed: {
    opacity: 0.8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 40,
    fontWeight: '500',
    marginTop: -2,
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
  cardPressed: {
    opacity: 0.7,
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
  quantityNegative: {
    color: '#D64545',
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
  placeholderName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#C4C4D2',
    fontStyle: 'italic',
  },
  placeholderValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#C4C4D2',
    marginTop: 2,
  },
});
