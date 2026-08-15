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
});

export type Invoice = z.infer<typeof InvoiceSchema>;

export function getItemTotal(item: InvoiceItem): number {
  const quantity = item.quantity ?? 0;
  const pricePerItem = item.pricePerItem ?? 0;
  const discountPercent = item.discountPercent ?? 0;
  const discountAmount = item.discountAmount ?? 0;
  const gross = quantity * pricePerItem;
  return gross - discountAmount - (gross * discountPercent) / 100;
}

export function getInvoiceTotal(invoice: Invoice): number {
  return invoice.items.reduce((sum, item) => sum + getItemTotal(item), 0);
}
