import { LFM2_5_350M } from 'react-native-executorch';

const DEFAULT_FINETUNED_PTE =
  'https://huggingface.co/drishti09/LFM-350M-VoiceBilling-FineTuned/resolve/main/invoice_lfm2_5_350m_fp16.pte';

const envPte = process.env.EXPO_PUBLIC_INVOICE_PTE;
const FINETUNED_PTE =
  envPte?.startsWith('https://') ? envPte : DEFAULT_FINETUNED_PTE;

export const usesFinetunedInvoiceLlm = true;

export const INVOICE_LLM_MODEL = {
  ...LFM2_5_350M,
  modelName: 'lfm2.5-350m' as const,
  modelSource: FINETUNED_PTE,
};
