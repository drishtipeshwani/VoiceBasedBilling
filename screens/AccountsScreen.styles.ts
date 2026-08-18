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
    paddingVertical: 14,
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
  customerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C28',
    marginTop: 4,
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
  emptyText: {
    textAlign: 'center',
    color: '#A0A0B2',
    fontSize: 14,
    marginTop: 40,
  },
  backButton: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginTop: 4,
  },
  backButtonPressed: {
    opacity: 0.6,
  },
  backText: {
    color: '#6E6E80',
    fontSize: 12,
    fontWeight: '500',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  errorText: {
    color: '#D64545',
    textAlign: 'center',
    fontSize: 13,
  },
});
