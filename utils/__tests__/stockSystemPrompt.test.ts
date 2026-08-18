import { readFileSync } from 'fs';
import { join } from 'path';
import { STOCK_SYSTEM_PROMPT_SHORT } from '../stockSystemPrompt';

describe('STOCK_SYSTEM_PROMPT_SHORT', () => {
  it('matches finetune_actions/system_prompt_stock.txt, which the dataset is built with', () => {
    const fromDisk = readFileSync(
      join(__dirname, '..', '..', 'finetune_actions', 'system_prompt_stock.txt'),
      'utf8',
    ).replace(/\n$/, '');

    expect(STOCK_SYSTEM_PROMPT_SHORT).toBe(fromDisk);
  });
});
