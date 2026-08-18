import {
  ActionName,
  type StockAction,
  type StockAgentActionResponse,
} from '../types/agentActionResponse';
import type { StockDraft } from '../types/stock';
import { emptyStockDraft } from '../types/stock';
import { normalizeEntityName } from './entityName';

function applyOneAction(draft: StockDraft, action: StockAction): StockDraft | null {
  switch (action.action) {
    case ActionName.SET_NAME:
      return { ...draft, name: normalizeEntityName(action.name) };
    case ActionName.SET_QUANTITY:
      return { ...draft, quantity: action.quantity };
    case ActionName.SET_COST:
      return { ...draft, costPrice: action.costPrice };
    case ActionName.SET_SELLING:
      return { ...draft, sellingPrice: action.sellingPrice };
    case ActionName.CLEAR:
      return { ...emptyStockDraft };
    case ActionName.SAVE:
    case ActionName.UNKNOWN:
    case ActionName.INCOMPLETE:
      return null;
  }
}

export function isIncompleteStockAction(response: StockAgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.INCOMPLETE;
}

export function isUnknownStockAction(response: StockAgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.UNKNOWN;
}

export function isSaveStockAction(response: StockAgentActionResponse): boolean {
  return response.length === 1 && response[0].action === ActionName.SAVE;
}

export function applyStockAction(
  draft: StockDraft,
  response: StockAgentActionResponse,
): StockDraft | null {
  if (isIncompleteStockAction(response) || isUnknownStockAction(response)) {
    return null;
  }

  let next = draft;
  let changed = false;

  for (const action of response) {
    if (action.action === ActionName.SAVE) {
      continue;
    }
    const applied = applyOneAction(next, action);
    if (applied) {
      next = applied;
      changed = true;
    }
  }

  return changed ? next : null;
}

export function describeStockAction(response: StockAgentActionResponse): string {
  if (isIncompleteStockAction(response)) return 'incomplete';
  if (isUnknownStockAction(response)) return 'unknown';
  return response.map((action) => action.action).join('+');
}
