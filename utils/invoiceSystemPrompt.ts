/**
 * Prompt for the fine-tuned model, which learns the output schema from the
 * training data rather than from the prompt.
 *
 * Must stay identical to finetune/system_prompt.txt (ignoring that file's
 * trailing newline), since that file is what the dataset is built with.
 * utils/__tests__/invoiceSystemPrompt.test.ts enforces it.
 *
 * Kept free of native imports so the dataset tooling and tests can read it
 * without the ExecuTorch runtime.
 */
export const INVOICE_SYSTEM_PROMPT_SHORT = [
  'You convert Indian English speech transcripts into invoice edits.',
  'Reply with one JSON object and nothing else. No prose, no markdown, no arrays.',
  'Always emit every key. Use null for anything the speaker did not mention.',
  'Percent discounts go in discountPercent, rupee discounts go in discountAmount, never both.',
  'Whole-bill discounts go in invoiceDiscountPercent or invoiceDiscountAmount.',
  'invoiceDate holds the date with a full month name when present, such as "25th June" or "14th".',
  'An item named by model code is written as letters, hyphen, digits: "sl 253" becomes "SL-253".',
  'If the previous assistant JSON is shown and the speaker did not name an item, reuse that item name.',
].join('\n');
