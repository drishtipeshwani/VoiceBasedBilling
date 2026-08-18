import { readFileSync } from 'fs';
import { join } from 'path';
import { CUSTOMER_SYSTEM_PROMPT_SHORT } from '../customerSystemPrompt';

describe('CUSTOMER_SYSTEM_PROMPT_SHORT', () => {
  it('matches finetune_actions/system_prompt_customer.txt, which the dataset is built with', () => {
    const fromDisk = readFileSync(
      join(__dirname, '..', '..', 'finetune_actions', 'system_prompt_customer.txt'),
      'utf8',
    ).replace(/\n$/, '');

    expect(CUSTOMER_SYSTEM_PROMPT_SHORT).toBe(fromDisk);
  });
});
