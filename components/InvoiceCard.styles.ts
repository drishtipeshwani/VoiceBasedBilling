import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  letterhead: {
    alignItems: 'center',
    paddingBottom: 16,
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#EEEEF2',
  },
  companyName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1C1C28',
    textAlign: 'center',
  },
  companyNamePlaceholder: {
    fontSize: 22,
    fontWeight: '700',
    color: '#C4C4D2',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  invoiceLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4C6FFF',
    letterSpacing: 2,
    marginTop: 6,
  },
  billedToRow: {
    marginBottom: 18,
  },
  billedToLabel: {
    fontSize: 12,
    color: '#A0A0B2',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  billedToName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1C1C28',
    marginTop: 2,
  },
  billedToNamePlaceholder: {
    fontSize: 17,
    fontWeight: '600',
    color: '#C4C4D2',
    fontStyle: 'italic',
    marginTop: 2,
  },
  table: {
    borderTopWidth: 1,
    borderTopColor: '#EEEEF2',
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#EEEEF2',
  },
  tableRowLast: {
    borderBottomWidth: 0,
  },
  tableHeaderRow: {
    borderBottomWidth: 1,
    borderBottomColor: '#DADAE6',
  },
  cell: {
    fontSize: 13,
  },
  itemCell: {
    flex: 2.2,
    paddingRight: 6,
  },
  qtyCell: {
    flex: 0.7,
    textAlign: 'center',
  },
  priceCell: {
    flex: 1,
    textAlign: 'right',
  },
  discountCell: {
    flex: 1,
    textAlign: 'right',
  },
  totalCell: {
    flex: 1.1,
    textAlign: 'right',
  },
  headerCellText: {
    fontWeight: '700',
    color: '#6E6E80',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  itemNameText: {
    color: '#1C1C28',
    fontWeight: '500',
  },
  cellText: {
    color: '#1C1C28',
  },
  emptyItemsBox: {
    borderTopWidth: 1,
    borderTopColor: '#EEEEF2',
    paddingVertical: 20,
  },
  emptyItemsText: {
    fontSize: 14,
    color: '#A0A0B2',
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 20,
  },
  totalsSection: {
    marginTop: 18,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#EEEEF2',
  },
  totalAmountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  totalAmountLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1C1C28',
  },
  totalAmountValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#4C6FFF',
  },
  wordsRow: {
    marginTop: 10,
  },
  wordsLabel: {
    fontSize: 12,
    color: '#A0A0B2',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  wordsValue: {
    fontSize: 14,
    color: '#6E6E80',
    marginTop: 4,
    lineHeight: 20,
    fontStyle: 'italic',
  },
});
