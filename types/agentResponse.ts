import { z } from 'zod';

export const ModifiedItemPayloadSchema = z.object({
  name: z.string().nullable().default(null),
  updatedItemName: z.string().nullable().default(null),
  quantity: z.number().nullable().default(null),
  pricePerItem: z.number().nullable().default(null),
  discountPercent: z.number().min(0).max(100).nullable().default(null),
  discountAmount: z.number().nullable().default(null),
  removeItem: z.boolean().default(false),
});

export type ModifiedItemPayload = z.infer<typeof ModifiedItemPayloadSchema>;

export const AgentResponseSchema = z.object({
  modifiedCompanyName: z.string().nullable().default(null),
  modifiedCustomerName: z.string().nullable().default(null),
  modifiedItems: ModifiedItemPayloadSchema.nullable().default(null),
  invoiceDiscountPercent: z.number().min(0).max(100).nullable().default(null),
  invoiceDiscountAmount: z.number().nullable().default(null),
  /**
   * Spoken date with a full month name when present: "25th June", "14th",
   * "3rd August 2026". A bare day means the current month. Resolved by the app
   * to DD/MM/YYYY, never by the model.
   */
  invoiceDate: z.string().nullable().default(null),
  clearInvoice: z.boolean().default(false),
  unknownInput: z.boolean().default(false),
  incompleteInput: z.boolean().default(false),
});

export type AgentResponse = z.infer<typeof AgentResponseSchema>;
