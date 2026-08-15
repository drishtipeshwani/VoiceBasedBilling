import {
  AgentResponseSchema,
  type AgentResponse,
  type ModifiedItemPayload,
} from '../types/agentResponse';
import type { Invoice, InvoiceItem } from '../types/invoice';
import { emptyInvoice } from '../data/emptyInvoice';

function hasAnyItemField(item: ModifiedItemPayload): boolean {
  return (
    item.name !== null ||
    item.updatedItemName !== null ||
    item.quantity !== null ||
    item.pricePerItem !== null ||
    item.discountPercent !== null ||
    item.discountAmount !== null ||
    item.removeItem
  );
}

function findItemIndex(invoice: Invoice, name: string): number {
  return invoice.items.findIndex((i) => i.name.toLowerCase() === name.toLowerCase());
}

/** Merge only non-null payload fields onto an existing invoice item. */
function mergeItemFields(existing: InvoiceItem, patch: ModifiedItemPayload): InvoiceItem {
  return {
    name: patch.updatedItemName ?? patch.name ?? existing.name,
    quantity: patch.quantity !== null ? patch.quantity : existing.quantity,
    pricePerItem: patch.pricePerItem !== null ? patch.pricePerItem : existing.pricePerItem,
    discountPercent:
      patch.discountPercent !== null ? patch.discountPercent : existing.discountPercent,
    discountAmount:
      patch.discountAmount !== null ? patch.discountAmount : existing.discountAmount,
  };
}

function coerceNullableString(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed || trimmed.toLowerCase() === 'null') return null;
    return trimmed;
  }
  return String(value);
}

function coerceNullableNumber(value: unknown): number | null {
  if (value == null) return null;
  if (typeof value === 'string') {
    const trimmed = value.trim().toLowerCase();
    if (!trimmed || trimmed === 'null') return null;
    const num = Number(trimmed);
    return Number.isFinite(num) ? num : null;
  }
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return null;
}

function coerceNullableItem(value: unknown): ModifiedItemPayload | null {
  if (value == null) return null;
  let obj: unknown = value;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed || trimmed.toLowerCase() === 'null') return null;
    if (!trimmed.startsWith('{')) {
      return {
        name: trimmed,
        updatedItemName: null,
        quantity: null,
        pricePerItem: null,
        discountPercent: null,
        discountAmount: null,
        removeItem: false,
      };
    }
    try {
      obj = JSON.parse(trimmed);
    } catch {
      return null;
    }
  }
  if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
    return null;
  }
  const record = obj as Record<string, unknown>;
  return {
    name: coerceNullableString(record.name),
    updatedItemName: coerceNullableString(record.updatedItemName),
    quantity: coerceNullableNumber(record.quantity),
    pricePerItem: coerceNullableNumber(record.pricePerItem),
    discountPercent: coerceNullableNumber(record.discountPercent),
    discountAmount: coerceNullableNumber(record.discountAmount),
    removeItem: coerceBoolean(record.removeItem),
  };
}

function coerceBoolean(value: unknown, fallback = false): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    const trimmed = value.trim().toLowerCase();
    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;
  }
  return fallback;
}

/**
 * Parse the raw LLM text reply into an AgentResponse.
 * Extracts the first JSON object from the string, coerces fields, then validates with Zod.
 */
export function parseLlmReply(raw: string): AgentResponse | null {
  const trimmed = raw.trim();

  const bracketStart = trimmed.indexOf('[');
  const braceStart = trimmed.indexOf('{');
  if (braceStart === -1) {
    return null;
  }

  let parsed: unknown;

  if (bracketStart !== -1 && bracketStart < braceStart) {
    const bracketEnd = trimmed.lastIndexOf(']');
    if (bracketEnd === -1) return null;
    try {
      parsed = JSON.parse(trimmed.slice(bracketStart, bracketEnd + 1));
    } catch {
      return null;
    }
  } else {
    const braceEnd = trimmed.lastIndexOf('}');
    if (braceEnd === -1 || braceEnd <= braceStart) return null;
    try {
      parsed = JSON.parse(trimmed.slice(braceStart, braceEnd + 1));
    } catch {
      return null;
    }
  }

  const obj: Record<string, unknown> = Array.isArray(parsed)
    ? (parsed[0] as Record<string, unknown>)
    : (parsed as Record<string, unknown>);
  if (typeof obj !== 'object' || obj === null) {
    return null;
  }

  const candidate = {
    modifiedCompanyName: coerceNullableString(obj.modifiedCompanyName),
    modifiedCustomerName: coerceNullableString(obj.modifiedCustomerName),
    modifiedItems: coerceNullableItem(obj.modifiedItems),
    invoiceDiscountPercent: coerceNullableNumber(obj.invoiceDiscountPercent),
    invoiceDiscountAmount: coerceNullableNumber(obj.invoiceDiscountAmount),
    invoiceDate: coerceNullableString(obj.invoiceDate),
    clearInvoice: coerceBoolean(obj.clearInvoice),
    unknownInput: coerceBoolean(obj.unknownInput),
    incompleteInput: coerceBoolean(obj.incompleteInput),
  };

  const result = AgentResponseSchema.safeParse(candidate);
  return result.success ? result.data : null;
}

/**
 * Apply a voice-command AgentResponse to an invoice.
 * Returns the next invoice, or null if nothing should change / could not apply.
 */
export function applyAgentResponse(
  invoice: Invoice,
  response: AgentResponse,
): Invoice | null {
  if (response.incompleteInput || response.unknownInput) {
    return null;
  }

  if (response.clearInvoice) {
    return { ...emptyInvoice };
  }

  let next: Invoice = invoice;
  let changed = false;

  if (response.modifiedCompanyName !== null) {
    next = { ...next, companyName: response.modifiedCompanyName };
    changed = true;
  }

  if (response.modifiedCustomerName !== null) {
    next = { ...next, customerName: response.modifiedCustomerName };
    changed = true;
  }

  // invoiceDiscountPercent / invoiceDiscountAmount / invoiceDate are parsed and
  // carried in the agent response, but the Invoice model does not hold them yet.

  if (response.modifiedItems !== null && hasAnyItemField(response.modifiedItems)) {
    const item = response.modifiedItems;
    if (item.name === null) {
      return changed ? next : null;
    }

    const idx = findItemIndex(next, item.name);
    if (item.removeItem) {
      if (idx !== -1) {
        next = { ...next, items: next.items.filter((_, i) => i !== idx) };
        changed = true;
      }
    } else if (idx === -1) {
      // No matching item — treat as add when we have a name.
      const nextItem: InvoiceItem = {
        name: item.updatedItemName ?? item.name,
        quantity: item.quantity,
        pricePerItem: item.pricePerItem,
        discountPercent: item.discountPercent,
        discountAmount: item.discountAmount,
      };
      next = { ...next, items: [...next.items, nextItem] };
      changed = true;
    } else if (
      item.updatedItemName !== null ||
      item.quantity !== null ||
      item.pricePerItem !== null ||
      item.discountPercent !== null ||
      item.discountAmount !== null
    ) {
      next = {
        ...next,
        items: next.items.map((existing, i) =>
          i === idx ? mergeItemFields(existing, item) : existing,
        ),
      };
      changed = true;
    } else {
      // Name-only on an existing item — still treat as a no-op update signal,
      // or re-add is not needed; leave unchanged unless company/customer changed.
    }
  }

  return changed ? next : null;
}

/** Short status label for UI / logs. */
export function describeAgentResponse(response: AgentResponse): string {
  if (response.incompleteInput) return 'incomplete';
  if (response.unknownInput) return 'unknown';
  if (response.clearInvoice) return 'CLEAR_INVOICE';
  const parts: string[] = [];
  if (response.modifiedCompanyName !== null) parts.push('company');
  if (response.modifiedCustomerName !== null) parts.push('customer');
  if (response.modifiedItems !== null) parts.push('items');
  return parts.length > 0 ? parts.join('+') : 'no-op';
}
