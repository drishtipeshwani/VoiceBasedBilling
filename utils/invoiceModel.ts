import { LFM2_5_350M_QUANTIZED } from 'react-native-executorch';

/**
 * Optional URL or file:// path to a merged+exported invoice LoRA .pte.
 * When unset, the stock quantized LFM2.5-350M preset is used.
 *
 * After `python finetune/merge_lora.py` and ExecuTorch export, set this in
 * `.env` (Expo inlines EXPO_PUBLIC_* at bundle time):
 *
 *   EXPO_PUBLIC_INVOICE_PTE=file:///absolute/path/to/invoice_lfm2_5_350m_8da4w.pte
 *
 * Or host the file and use https://…
 */
const FINETUNED_PTE = process.env.EXPO_PUBLIC_INVOICE_PTE;

export const usesFinetunedInvoiceLlm = Boolean(FINETUNED_PTE);

export const INVOICE_LLM_MODEL = FINETUNED_PTE
  ? {
      ...LFM2_5_350M_QUANTIZED,
      modelName: 'lfm2.5-350m-quantized' as const,
      modelSource: FINETUNED_PTE,
    }
  : LFM2_5_350M_QUANTIZED;
