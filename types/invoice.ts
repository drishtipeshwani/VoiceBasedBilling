import { z } from 'zod';

export const InvoiceItemSchema = z.object({
  name: z.string(),
  quantity: z.number().nullable(),
  pricePerItem: z.number().nullable(),
  discountPercent: z.number().min(0).max(100).nullable(),
  discountAmount: z.number().nullable(),
});

export type InvoiceItem = z.infer<typeof InvoiceItemSchema>;

export const InvoiceSchema = z.object({
  companyName: z.string(),
  customerName: z.string(),
  items: z.array(InvoiceItemSchema),
  /** Display date as DD/MM/YYYY after the app resolves the spoken phrase. */
  invoiceDate: z.string().nullable(),
  invoiceDiscountPercent: z.number().min(0).max(100).nullable(),
  invoiceDiscountAmount: z.number().nullable(),
});

export type Invoice = z.infer<typeof InvoiceSchema>;

export function serializeInvoiceSnapshot(invoice: Invoice): string {
  return JSON.stringify(invoice);
}

export function parseInvoiceSnapshot(raw: string): Invoice {
  return InvoiceSchema.parse(JSON.parse(raw));
}

export function getItemTotal(item: InvoiceItem): number {
  const quantity = item.quantity ?? 0;
  const pricePerItem = item.pricePerItem ?? 0;
  const discountPercent = item.discountPercent ?? 0;
  const discountAmount = item.discountAmount ?? 0;
  const gross = quantity * pricePerItem;
  return gross - discountAmount - (gross * discountPercent) / 100;
}

export function getInvoiceSubtotal(invoice: Invoice): number {
  return invoice.items.reduce((sum, item) => sum + getItemTotal(item), 0);
}

export function getInvoiceDiscount(invoice: Invoice): number {
  const subtotal = getInvoiceSubtotal(invoice);
  const percent = invoice.invoiceDiscountPercent ?? 0;
  const amount = invoice.invoiceDiscountAmount ?? 0;
  return (subtotal * percent) / 100 + amount;
}

export function getInvoiceTotal(invoice: Invoice): number {
  return Math.max(0, getInvoiceSubtotal(invoice) - getInvoiceDiscount(invoice));
}
