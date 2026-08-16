import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

interface ShopDataContextValue {
  dataVersion: number;
  bumpData: () => void;
}

const ShopDataContext = createContext<ShopDataContextValue | undefined>(undefined);

export function ShopDataProvider({ children }: { children: ReactNode }) {
  const [dataVersion, setDataVersion] = useState(0);
  const bumpData = useCallback(() => {
    setDataVersion((version) => version + 1);
  }, []);
  const value = useMemo(
    () => ({ dataVersion, bumpData }),
    [dataVersion, bumpData],
  );

  return (
    <ShopDataContext.Provider value={value}>{children}</ShopDataContext.Provider>
  );
}

export function useShopData(): ShopDataContextValue {
  const ctx = useContext(ShopDataContext);
  if (!ctx) {
    throw new Error('useShopData must be used within a ShopDataProvider');
  }
  return ctx;
}
