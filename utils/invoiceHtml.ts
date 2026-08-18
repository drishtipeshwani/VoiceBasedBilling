import {
  getInvoiceDiscount,
  getInvoiceSubtotal,
  getInvoiceTotal,
  getItemTotal,
  Invoice,
  InvoiceItem,
} from '../types/invoice';
import { formatAmount, formatAmountInWords } from './currency';

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function formatItemDiscount(item: InvoiceItem): string {
  const parts: string[] = [];
  if (item.discountPercent != null && item.discountPercent > 0) {
    parts.push(`${item.discountPercent}%`);
  }
  if (item.discountAmount != null && item.discountAmount > 0) {
    parts.push(item.discountAmount.toLocaleString('en-IN'));
  }
  return parts.length > 0 ? parts.join(' + ') : '-';
}

export function buildInvoiceHtml(invoice: Invoice): string {
  const subtotal = getInvoiceSubtotal(invoice);
  const invoiceDiscount = getInvoiceDiscount(invoice);
  const totalAmount = getInvoiceTotal(invoice);
  const dateLabel = invoice.invoiceDate ? `Date ${escapeHtml(invoice.invoiceDate)}` : '';
  const discountLabel =
    invoice.invoiceDiscountPercent != null && invoice.invoiceDiscountPercent > 0
      ? `${invoice.invoiceDiscountPercent}%`
      : invoice.invoiceDiscountAmount != null && invoice.invoiceDiscountAmount > 0
        ? formatAmount(invoice.invoiceDiscountAmount)
        : null;
  const discountRow =
    invoiceDiscount > 0 && discountLabel
      ? `
          <div class="subtotal-row">
            <span class="subtotal-label">Subtotal</span>
            <span class="subtotal-value">${formatAmount(subtotal)}</span>
          </div>
          <div class="subtotal-row">
            <span class="subtotal-label">Invoice discount (${discountLabel})</span>
            <span class="subtotal-value">-${formatAmount(invoiceDiscount)}</span>
          </div>
        `
      : '';

  const rows = invoice.items
    .map((item) => {
      const total = getItemTotal(item);
      return `
        <tr>
          <td class="item-name">${escapeHtml(item.name)}</td>
          <td class="num">${item.quantity ?? '-'}</td>
          <td class="num">${
            item.pricePerItem != null
              ? item.pricePerItem.toLocaleString('en-IN')
              : '-'
          }</td>
          <td class="num">${formatItemDiscount(item)}</td>
          <td class="num">${total.toLocaleString('en-IN')}</td>
        </tr>
      `;
    })
    .join('');

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
          @page {
            margin: 32px;
          }
          body {
            font-family: -apple-system, Helvetica, Arial, sans-serif;
            color: #1C1C28;
            padding: 0;
            margin: 0;
          }
          .letterhead {
            text-align: center;
            padding-bottom: 16px;
            margin-bottom: 20px;
            border-bottom: 1px solid #EEEEF2;
          }
          .company-name {
            font-size: 24px;
            font-weight: 700;
            margin: 0;
          }
          .invoice-label {
            font-size: 12px;
            font-weight: 600;
            color: #4C6FFF;
            letter-spacing: 2px;
            margin-top: 6px;
          }
          .invoice-date {
            font-size: 13px;
            color: #6E6E80;
            margin-top: 8px;
          }
          .billed-to-label {
            font-size: 11px;
            color: #A0A0B2;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
          }
          .billed-to-name {
            font-size: 16px;
            font-weight: 600;
            margin: 2px 0 20px 0;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
          }
          th {
            text-align: left;
            font-size: 11px;
            font-weight: 700;
            color: #6E6E80;
            text-transform: uppercase;
            border-bottom: 1px solid #DADAE6;
            padding: 8px 6px;
          }
          td {
            font-size: 13px;
            padding: 8px 6px;
            border-bottom: 1px solid #EEEEF2;
          }
          th.num, td.num {
            text-align: right;
          }
          .item-name {
            font-weight: 500;
          }
          .totals {
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #EEEEF2;
          }
          .subtotal-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }
          .subtotal-label, .subtotal-value {
            font-size: 13px;
            color: #6E6E80;
          }
          .total-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .total-label {
            font-size: 15px;
            font-weight: 700;
          }
          .total-value {
            font-size: 20px;
            font-weight: 700;
            color: #4C6FFF;
          }
          .words-label {
            font-size: 11px;
            color: #A0A0B2;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 14px 0 4px 0;
          }
          .words-value {
            font-size: 13px;
            color: #6E6E80;
            font-style: italic;
            margin: 0;
          }
        </style>
      </head>
      <body>
        <div class="letterhead">
          <p class="company-name">${escapeHtml(invoice.companyName)}</p>
          <p class="invoice-label">INVOICE</p>
          ${dateLabel ? `<p class="invoice-date">${dateLabel}</p>` : ''}
        </div>

        <p class="billed-to-label">Billed To</p>
        <p class="billed-to-name">${escapeHtml(invoice.customerName)}</p>

        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th class="num">Qty</th>
              <th class="num">Price</th>
              <th class="num">Disc.</th>
              <th class="num">Total</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>

        <div class="totals">
          ${discountRow}
          <div class="total-row">
            <span class="total-label">Total Amount</span>
            <span class="total-value">${formatAmount(totalAmount)}</span>
          </div>
          <p class="words-label">In Words</p>
          <p class="words-value">${formatAmountInWords(totalAmount)}</p>
        </div>
      </body>
    </html>
  `;
}
