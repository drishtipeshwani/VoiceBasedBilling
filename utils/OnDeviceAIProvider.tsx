import { createContext, useContext, type ReactNode } from 'react';
import { useLLM, type LLMType } from 'react-native-executorch';
import { INVOICE_LLM_MODEL } from './invoiceModel';

interface OnDeviceAIContextValue {
  llm: LLMType;
}

const OnDeviceAIContext = createContext<OnDeviceAIContextValue | null>(null);

export function OnDeviceAIProvider({ children }: { children: ReactNode }) {
  const llm = useLLM({ model: INVOICE_LLM_MODEL });

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
