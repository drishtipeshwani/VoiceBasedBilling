import { Text, View } from 'react-native';
import {
  getInvoiceDiscount,
  getInvoiceSubtotal,
  getInvoiceTotal,
  getItemTotal,
  Invoice,
  InvoiceItem,
} from '../types/invoice';
import { formatAmount, formatAmountInWords } from '../utils/currency';
import { styles } from './InvoiceCard.styles';

interface InvoiceCardProps {
  invoice: Invoice;
}

function formatItemDiscount(item: InvoiceItem): string {
  const parts: string[] = [];
  if (item.discountPercent != null && item.discountPercent > 0) {
    parts.push(`${item.discountPercent}%`);
  }
  if (item.discountAmount != null && item.discountAmount > 0) {
    parts.push(item.discountAmount.toLocaleString('en-IN'));
  }
  return parts.length > 0 ? parts.join(' + ') : '-';
}

function formatInvoiceDiscount(invoice: Invoice): string | null {
  if (invoice.invoiceDiscountPercent != null && invoice.invoiceDiscountPercent > 0) {
    return `${invoice.invoiceDiscountPercent}%`;
  }
  if (invoice.invoiceDiscountAmount != null && invoice.invoiceDiscountAmount > 0) {
    return formatAmount(invoice.invoiceDiscountAmount);
  }
  return null;
}

export default function InvoiceCard({ invoice }: InvoiceCardProps) {
  const hasItems = invoice.items.length > 0;
  const subtotal = getInvoiceSubtotal(invoice);
  const invoiceDiscount = getInvoiceDiscount(invoice);
  const totalAmount = getInvoiceTotal(invoice);
  const invoiceDiscountLabel = formatInvoiceDiscount(invoice);
  const showInvoiceDiscount = invoiceDiscount > 0 && invoiceDiscountLabel !== null;

  return (
    <View style={styles.card}>
      <View style={styles.letterhead}>
        <Text style={invoice.companyName ? styles.companyName : styles.companyNamePlaceholder}>
          {invoice.companyName || 'Your Company Name'}
        </Text>
        <Text style={styles.invoiceLabel}>INVOICE</Text>
        <Text style={invoice.invoiceDate ? styles.invoiceDate : styles.invoiceDatePlaceholder}>
          {invoice.invoiceDate ? `Date ${invoice.invoiceDate}` : 'Date not set'}
        </Text>
      </View>

      <View style={styles.billedToRow}>
        <Text style={styles.billedToLabel}>Billed To</Text>
        <Text style={invoice.customerName ? styles.billedToName : styles.billedToNamePlaceholder}>
          {invoice.customerName || 'No customer yet'}
        </Text>
      </View>

      {hasItems ? (
        <View style={styles.table}>
          <View style={[styles.tableRow, styles.tableHeaderRow]}>
            <Text style={[styles.cell, styles.itemCell, styles.headerCellText]}>Item</Text>
            <Text style={[styles.cell, styles.qtyCell, styles.headerCellText]}>Qty</Text>
            <Text style={[styles.cell, styles.priceCell, styles.headerCellText]}>Price</Text>
            <Text style={[styles.cell, styles.discountCell, styles.headerCellText]}>Disc.</Text>
            <Text style={[styles.cell, styles.totalCell, styles.headerCellText]}>Total</Text>
          </View>

          {invoice.items.map((item: InvoiceItem, index: number) => (
            <View
              key={`${item.name}-${index}`}
              style={[
                styles.tableRow,
                index === invoice.items.length - 1 && styles.tableRowLast,
              ]}
            >
              <Text style={[styles.cell, styles.itemCell, styles.itemNameText]}>
                {item.name}
              </Text>
              <Text style={[styles.cell, styles.qtyCell, styles.cellText]}>
                {item.quantity ?? '-'}
              </Text>
              <Text style={[styles.cell, styles.priceCell, styles.cellText]}>
                {item.pricePerItem != null
                  ? item.pricePerItem.toLocaleString('en-IN')
                  : '-'}
              </Text>
              <Text style={[styles.cell, styles.discountCell, styles.cellText]}>
                {formatItemDiscount(item)}
              </Text>
              <Text style={[styles.cell, styles.totalCell, styles.cellText]}>
                {getItemTotal(item).toLocaleString('en-IN')}
              </Text>
            </View>
          ))}
        </View>
      ) : (
        <View style={styles.emptyItemsBox}>
          <Text style={styles.emptyItemsText}>
            No items yet. Try saying "add item pens quantity 5 price 20".
          </Text>
        </View>
      )}

      {hasItems ? (
        <View style={styles.totalsSection}>
          {showInvoiceDiscount ? (
            <>
              <View style={styles.subtotalRow}>
                <Text style={styles.subtotalLabel}>Subtotal</Text>
                <Text style={styles.subtotalValue}>{formatAmount(subtotal)}</Text>
              </View>
              <View style={styles.subtotalRow}>
                <Text style={styles.subtotalLabel}>
                  Invoice discount ({invoiceDiscountLabel})
                </Text>
                <Text style={styles.subtotalValue}>-{formatAmount(invoiceDiscount)}</Text>
              </View>
            </>
          ) : null}
          <View style={styles.totalAmountRow}>
            <Text style={styles.totalAmountLabel}>Total Amount</Text>
            <Text style={styles.totalAmountValue}>{formatAmount(totalAmount)}</Text>
          </View>
          <View style={styles.wordsRow}>
            <Text style={styles.wordsLabel}>In Words</Text>
            <Text style={styles.wordsValue}>{formatAmountInWords(totalAmount)}</Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}
