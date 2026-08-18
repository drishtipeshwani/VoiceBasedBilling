import { readFileSync } from 'fs';
import { join } from 'path';
import { INVOICE_SYSTEM_PROMPT_SHORT } from '../invoiceSystemPrompt';

describe('INVOICE_SYSTEM_PROMPT_SHORT', () => {
  it('matches finetune_actions/system_prompt.txt, which the dataset is built with', () => {
    const fromDisk = readFileSync(
      join(__dirname, '..', '..', 'finetune_actions', 'system_prompt.txt'),
      'utf8',
    ).replace(/\n$/, '');

    expect(INVOICE_SYSTEM_PROMPT_SHORT).toBe(fromDisk);
  });
});
