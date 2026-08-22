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
  headerActions: {
    marginLeft: 12,
    marginTop: 4,
    alignItems: 'flex-end',
    gap: 8,
  },
  headerButton: {
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  headerButtonPressed: {
    opacity: 0.6,
  },
  headerButtonText: {
    color: '#6E6E80',
    fontSize: 12,
    fontWeight: '500',
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
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingVertical: 16,
    paddingHorizontal: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  rowPressed: {
    opacity: 0.7,
  },
  customerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C28',
    flex: 1,
  },
  rowLeft: {
    flex: 1,
  },
  invoiceNumber: {
    fontSize: 12,
    fontWeight: '700',
    color: '#4C6FFF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  date: {
    fontSize: 12,
    color: '#A0A0B2',
    marginTop: 2,
  },
  amount: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C28',
  },
  balanceWrap: {
    alignItems: 'flex-end',
  },
  balance: {
    fontSize: 16,
    fontWeight: '700',
    color: '#D64545',
  },
  balanceSettled: {
    color: '#2E7D32',
  },
  balanceLabel: {
    fontSize: 11,
    color: '#A0A0B2',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
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
    flex: 1,
  },
  placeholderBalance: {
    fontSize: 16,
    fontWeight: '700',
    color: '#C4C4D2',
  },
});
