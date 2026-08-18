import {
  parseInvoiceSnapshot,
  serializeInvoiceSnapshot,
  type Invoice,
} from '../../types/invoice';
import { isoToInvoiceDate } from '../invoiceDate';

describe('invoice snapshot', () => {
  const invoice: Invoice = {
    companyName: 'DHA Enterprises',
    customerName: 'Ramesh',
    items: [
      {
        name: 'pens',
        quantity: 10,
        pricePerItem: 20,
        discountPercent: null,
        discountAmount: 5,
      },
    ],
    invoiceDate: '18/08/2026',
    invoiceDiscountPercent: 10,
    invoiceDiscountAmount: null,
  };

  it('round-trips the invoice JSON used for Accounts display', () => {
    const raw = serializeInvoiceSnapshot(invoice);
    expect(parseInvoiceSnapshot(raw)).toEqual(invoice);
  });
});

describe('isoToInvoiceDate', () => {
  it('converts a stored ISO date to DD/MM/YYYY', () => {
    expect(isoToInvoiceDate('2026-08-18T00:00:00.000Z')).toBe('18/08/2026');
  });
});
