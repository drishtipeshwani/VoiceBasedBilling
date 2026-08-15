import { toCurrency } from 'to-words/en-IN';

export function formatAmount(amount: number): string {
  return `₹${amount.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatAmountInWords(amount: number): string {
  return toCurrency(amount);
}
