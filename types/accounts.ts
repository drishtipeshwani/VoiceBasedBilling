import type { Invoice } from './invoice';

export interface InvoiceSummary {
  id: string;
  invoiceNumber: number;
  customerName: string;
  date: string;
  totalAmount: number;
}

export interface SavedInvoice {
  invoiceNumber: number;
  invoice: Invoice;
}
