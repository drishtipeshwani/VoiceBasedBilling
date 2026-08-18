import { Invoice } from '../types/invoice';

export const emptyInvoice: Invoice = {
  companyName: '',
  customerName: '',
  items: [],
  invoiceDate: null,
  invoiceDiscountPercent: null,
  invoiceDiscountAmount: null,
};
