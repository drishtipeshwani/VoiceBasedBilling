export interface CustomerLedgerEntry {
  id: string;
  name: string;
  balanceAmount: number;
}

export interface CustomerDraft {
  name: string;
  balanceAmount: number | null;
}

export const emptyCustomerDraft: CustomerDraft = {
  name: '',
  balanceAmount: null,
};
