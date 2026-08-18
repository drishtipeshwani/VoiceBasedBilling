import { readFileSync } from 'fs';
import { join } from 'path';
import {
  CustomerAgentActionResponseSchema,
  StockAgentActionResponseSchema,
} from '../../types/agentActionResponse';

const evalPath = join(
  __dirname,
  '..',
  '..',
  'finetune_actions',
  'data',
  'eval_handwritten.jsonl',
);

function readRows() {
  return readFileSync(evalPath, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

describe('customer and stock action schemas', () => {
  const rows = readRows();

  it('accept every handwritten customer target', () => {
    const customerRows = rows.filter((row) => row.meta?.task === 'customer');
    expect(customerRows.length).toBeGreaterThan(0);

    for (const row of customerRows) {
      expect(() =>
        CustomerAgentActionResponseSchema.parse(row.agentOutput),
      ).not.toThrow();
    }
  });

  it('accept every handwritten stock target', () => {
    const stockRows = rows.filter((row) => row.meta?.task === 'stock');
    expect(stockRows.length).toBeGreaterThan(0);

    for (const row of stockRows) {
      expect(() =>
        StockAgentActionResponseSchema.parse(row.agentOutput),
      ).not.toThrow();
    }
  });

  it('rejects invoice SET_CUSTOMER on the customer schema', () => {
    const result = CustomerAgentActionResponseSchema.safeParse([
      { action: 'SET_CUSTOMER', customerName: 'Ramesh' },
    ]);
    expect(result.success).toBe(false);
  });

  it('rejects invoice SET_QUANTITY (named line item) on the stock schema', () => {
    const result = StockAgentActionResponseSchema.safeParse([
      { action: 'SET_QUANTITY', name: 'onion', quantity: 2 },
    ]);
    expect(result.success).toBe(false);
  });
});
