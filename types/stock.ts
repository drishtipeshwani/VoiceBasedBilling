export interface StockItem {
  id: string;
  name: string;
  quantity: number;
  costPrice: number;
  sellingPrice: number;
}

export interface StockDraft {
  name: string;
  quantity: number | null;
  costPrice: number | null;
  sellingPrice: number | null;
}

export const emptyStockDraft: StockDraft = {
  name: '',
  quantity: null,
  costPrice: null,
  sellingPrice: null,
};
