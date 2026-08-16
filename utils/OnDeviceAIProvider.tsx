import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react';
import { useLLM, type LLMType } from 'react-native-executorch';
import { INVOICE_LLM_MODEL, usesFinetunedInvoiceLlm } from './invoiceModel';

interface OnDeviceAIContextValue {
  llm: LLMType;
}

const OnDeviceAIContext = createContext<OnDeviceAIContextValue | null>(null);

export function OnDeviceAIProvider({ children }: { children: ReactNode }) {
  const llm = useLLM({ model: INVOICE_LLM_MODEL });
  const wasGeneratingRef = useRef(false);

  useEffect(() => {
    if (!llm.isReady) {
      return;
    }
    console.log('[InvoiceLLM] ready', {
      finetuned: usesFinetunedInvoiceLlm,
      modelName: INVOICE_LLM_MODEL.modelName,
    });
  }, [llm.isReady]);

  useEffect(() => {
    if (llm.error) {
      console.error('[InvoiceLLM] error:', llm.error.message);
    }
  }, [llm.error]);

  useEffect(() => {
    if (llm.isGenerating && llm.response) {
      wasGeneratingRef.current = true;
      console.log('[InvoiceLLM] token:', JSON.stringify(llm.token), 'so far:', llm.response);
    } else if (wasGeneratingRef.current && !llm.isGenerating) {
      wasGeneratingRef.current = false;
      console.log('[InvoiceLLM] generation ended:', llm.response || '(empty)');
    }
  }, [llm.isGenerating, llm.response, llm.token]);

  return (
    <OnDeviceAIContext.Provider value={{ llm }}>
      {children}
    </OnDeviceAIContext.Provider>
  );
}

export function useOnDeviceAI(): OnDeviceAIContextValue {
  const value = useContext(OnDeviceAIContext);
  if (!value) {
    throw new Error('useOnDeviceAI must be used within OnDeviceAIProvider');
  }
  return value;
}
