import {
  ActionName,
  type Action,
  type AgentActionResponse,
} from '../types/agentActionResponse';
import type { Invoice, InvoiceItem } from '../types/invoice';
import { emptyInvoice } from '../data/emptyInvoice';
import { entityNamesMatch, normalizeEntityName } from './entityName';
import { resolveInvoiceDate } from './invoiceDate';

function findItemIndex(invoice: Invoice, name: string): number {
  return invoice.items.findIndex((item) => entityNamesMatch(item.name, name));
}

function blankItem(name: string): InvoiceItem {
  return {
    name,
    quantity: null,
    pricePerItem: null,
    discountPercent: null,
    discountAmount: null,
  };
}

function replaceItem(invoice: Invoice, index: number, item: InvoiceItem): Invoice {
  return {
    ...invoice,
    items: invoice.items.map((existing, i) => (i === index ? item : existing)),
  };
}

function upsertItem(
  invoice: Invoice,
  name: string,
  patch: Partial<InvoiceItem>,
): Invoice {
  const canonical = normalizeEntityName(name);
  const index = findItemIndex(invoice, canonical);
  if (index === -1) {
    return {
      ...invoice,
      items: [
        ...invoice.items,
        { ...blankItem(canonical), ...patch, name: patch.name ?? canonical },
      ],
    };
  }
  return replaceItem(invoice, index, {
    ...invoice.items[index],
    ...patch,
  });
}

function applyOneAction(invoice: Invoice, action: Action): Invoice | null {
  switch (action.action) {
    case ActionName.ADD_ITEM:
      return {
        ...invoice,
        items: [
          ...invoice.items,
          {
            name: normalizeEntityName(action.name),
            quantity: action.quantity ?? null,
            pricePerItem: action.pricePerItem ?? null,
            discountPercent: action.discountPercent ?? null,
            discountAmount: action.discountAmount ?? null,
          },
        ],
      };

    case ActionName.DELETE_ITEM: {
      const index = findItemIndex(invoice, action.name);
      if (index === -1) {
        return null;
      }
      return {
        ...invoice,
        items: invoice.items.filter((_, i) => i !== index),
      };
    }

    case ActionName.SET_PRICE:
      return upsertItem(invoice, action.name, { pricePerItem: action.pricePerItem });

    case ActionName.SET_QUANTITY:
      return upsertItem(invoice, action.name, { quantity: action.quantity });

    case ActionName.RENAME_ITEM:
      return upsertItem(invoice, action.name, {
        name: normalizeEntityName(action.updatedItemName),
      });

    case ActionName.SET_ITEM_DISCOUNT:
      if ('discountPercent' in action) {
        return upsertItem(invoice, action.name, {
          discountPercent: action.discountPercent,
          discountAmount: null,
        });
      }
      return upsertItem(invoice, action.name, {
        discountAmount: action.discountAmount,
        discountPercent: null,
      });

    case ActionName.SET_INVOICE_DISCOUNT:
      if ('invoiceDiscountPercent' in action) {
        return {
          ...invoice,
          invoiceDiscountPercent: action.invoiceDiscountPercent,
          invoiceDiscountAmount: null,
        };
      }
      return {
        ...invoice,
        invoiceDiscountAmount: action.invoiceDiscountAmount,
        invoiceDiscountPercent: null,
      };

    case ActionName.SET_DATE: {
      const resolved = resolveInvoiceDate(action.invoiceDate);
      if (!resolved) {
        return null;
      }
      return { ...invoice, invoiceDate: resolved };
    }

    case ActionName.SET_CUSTOMER:
      return { ...invoice, customerName: normalizeEntityName(action.customerName) };

    case ActionName.SET_COMPANY:
      return {
        ...invoice,
        customerName: normalizeEntityName(action.companyName),
      };

    case ActionName.CLEAR_INVOICE:
      return { ...emptyInvoice, companyName: invoice.companyName };

    case ActionName.SAVE_INVOICE:
    case ActionName.UNKNOWN:
    case ActionName.INCOMPLETE:
      return null;
  }
}

export function invoiceHasItem(invoice: Invoice, name: string): boolean {
  return findItemIndex(invoice, name) !== -1;
}

export function applySingleInvoiceAction(
  invoice: Invoice,
  action: Action,
): Invoice | null {
  if (action.action === ActionName.SAVE_INVOICE) {
    return null;
  }
  return applyOneAction(invoice, action);
}

export function isIncompleteInvoiceAction(response: AgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.INCOMPLETE;
}

export function isUnknownInvoiceAction(response: AgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.UNKNOWN;
}

export function isSaveInvoiceAction(response: AgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.SAVE_INVOICE;
}

export function describeInvoiceAction(response: AgentActionResponse): string {
  if (isIncompleteInvoiceAction(response)) return 'incomplete';
  if (isUnknownInvoiceAction(response)) return 'unknown';
  return response.map((action) => action.action).join('+');
}
