import {
  ActionName,
  type Action,
  type AgentActionResponse,
} from '../types/agentActionResponse';
import type { Invoice } from '../types/invoice';
import {
  applySingleInvoiceAction,
  invoiceHasItem,
} from './applyInvoiceAction';
import { normalizeEntityName } from './entityName';

export type CatalogKind = 'customer' | 'stock';

export interface EntityPrompt {
  kind: CatalogKind;
  name: string;
  action: Action;
  remaining: Action[];
}

export interface GatedApplyResult {
  invoice: Invoice;
  changed: boolean;
  prompt: EntityPrompt | null;
  applied: Action[];
}

export function rewriteCompanyAsCustomer(action: Action): Action {
  if (action.action !== ActionName.SET_COMPANY) {
    return action;
  }
  return {
    action: ActionName.SET_CUSTOMER,
    customerName: action.companyName,
  };
}

export function catalogRequirement(
  invoice: Invoice,
  action: Action,
): { kind: CatalogKind; name: string } | null {
  switch (action.action) {
    case ActionName.SET_CUSTOMER: {
      const name = normalizeEntityName(action.customerName);
      if (!name) {
        return null;
      }
      return { kind: 'customer', name };
    }
    case ActionName.ADD_ITEM: {
      const name = normalizeEntityName(action.name);
      if (!name) {
        return null;
      }
      return { kind: 'stock', name };
    }
    case ActionName.SET_PRICE:
    case ActionName.SET_QUANTITY:
    case ActionName.SET_ITEM_DISCOUNT: {
      const name = normalizeEntityName(action.name);
      if (!name) {
        return null;
      }
      if (invoiceHasItem(invoice, name)) {
        return null;
      }
      return { kind: 'stock', name };
    }
    case ActionName.RENAME_ITEM: {
      const name = normalizeEntityName(action.updatedItemName);
      if (!name) {
        return null;
      }
      return { kind: 'stock', name };
    }
    default:
      return null;
  }
}

export async function processGatedInvoiceActions(
  invoice: Invoice,
  actions: AgentActionResponse,
  lookup: {
    customerExists: (name: string) => Promise<boolean>;
    stockItemExists: (name: string) => Promise<boolean>;
  },
): Promise<GatedApplyResult> {
  let next = invoice;
  let changed = false;
  const applied: Action[] = [];

  for (let index = 0; index < actions.length; index += 1) {
    const action = rewriteCompanyAsCustomer(actions[index]);
    if (action.action === ActionName.SAVE_INVOICE) {
      continue;
    }

    const requirement = catalogRequirement(next, action);
    if (requirement) {
      const exists =
        requirement.kind === 'customer'
          ? await lookup.customerExists(requirement.name)
          : await lookup.stockItemExists(requirement.name);
      if (!exists) {
        return {
          invoice: next,
          changed,
          applied,
          prompt: {
            kind: requirement.kind,
            name: requirement.name,
            action,
            remaining: actions.slice(index + 1).map(rewriteCompanyAsCustomer),
          },
        };
      }
    }

    const appliedInvoice = applySingleInvoiceAction(next, action);
    if (appliedInvoice) {
      next = appliedInvoice;
      changed = true;
      applied.push(action);
    }
  }

  return { invoice: next, changed, prompt: null, applied };
}
