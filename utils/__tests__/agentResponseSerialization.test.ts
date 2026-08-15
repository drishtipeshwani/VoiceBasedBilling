import { readFileSync } from 'fs';
import { join } from 'path';
import { AgentResponseSchema } from '../../types/agentResponse';

const dataDir = join(__dirname, '..', '..', 'finetune', 'data');

function readRows(file: string) {
  return readFileSync(join(dataDir, file), 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

describe('agent response serialization', () => {
  it('round-trips dataset targets with identical key order', () => {
    // The dataset writes targets with a fixed key order. HomeScreen feeds the
    // previous response back through JSON.stringify, so if Zod reordered keys
    // the model would see a shape at inference it never saw in training.
    const rows = readRows('test.jsonl');
    expect(rows.length).toBeGreaterThan(0);

    for (const row of rows) {
      const expected = JSON.stringify(row.agentOutput);
      const parsed = AgentResponseSchema.parse(row.agentOutput);
      expect(JSON.stringify(parsed)).toBe(expected);
    }
  });

  it('accepts every hand-written eval target', () => {
    const rows = readRows('eval_handwritten.jsonl');
    expect(rows.length).toBeGreaterThan(0);

    for (const row of rows) {
      expect(() => AgentResponseSchema.parse(row.agentOutput)).not.toThrow();
      if (row.lastModified) {
        expect(() => AgentResponseSchema.parse(row.lastModified)).not.toThrow();
      }
    }
  });
});
