import * as Crypto from 'expo-crypto';
import type { SQLiteDatabase } from 'expo-sqlite';
import type { InvoiceSummary } from '../types/accounts';
import type { User } from '../types/auth';
import type { Invoice } from '../types/invoice';
import { getInvoiceTotal } from '../types/invoice';
import type { CustomerLedgerEntry } from '../types/ledger';
import type { StockItem } from '../types/stock';

interface UserRow {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  company_name: string;
  created_at: string;
}

function newId(): string {
  return Crypto.randomUUID();
}

function mapUser(row: UserRow): User {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    phone: row.phone,
    companyName: row.company_name,
    createdAt: row.created_at,
  };
}

export async function getRegisteredUser(db: SQLiteDatabase): Promise<User | null> {
  const row = await db.getFirstAsync<UserRow>('SELECT * FROM users LIMIT 1');
  return row ? mapUser(row) : null;
}

export async function insertUser(
  db: SQLiteDatabase,
  input: {
    name: string;
    email: string | null;
    phone: string | null;
    companyName: string;
  },
): Promise<User> {
  const id = newId();
  const createdAt = new Date().toISOString();
  await db.runAsync(
    `INSERT INTO users (id, name, email, phone, company_name, created_at)
     VALUES (?, ?, ?, ?, ?, ?)`,
    id,
    input.name,
    input.email,
    input.phone,
    input.companyName,
    createdAt,
  );
  return {
    id,
    name: input.name,
    email: input.email,
    phone: input.phone,
    companyName: input.companyName,
    createdAt,
  };
}

export async function listStockItems(
  db: SQLiteDatabase,
  userId: string,
): Promise<StockItem[]> {
  const rows = await db.getAllAsync<{
    id: string;
    name: string;
    quantity: number;
    cost_price: number;
    selling_price: number;
  }>(
    `SELECT id, name, quantity, cost_price, selling_price
     FROM stock
     WHERE user_id = ?
     ORDER BY name COLLATE NOCASE`,
    userId,
  );
  return rows.map((row) => ({
    id: row.id,
    name: row.name,
    quantity: row.quantity,
    costPrice: row.cost_price,
    sellingPrice: row.selling_price,
  }));
}

export async function listCustomers(
  db: SQLiteDatabase,
  userId: string,
): Promise<CustomerLedgerEntry[]> {
  const rows = await db.getAllAsync<{
    id: string;
    name: string;
    balance_amount: number;
  }>(
    `SELECT id, name, balance_amount
     FROM customers
     WHERE user_id = ?
     ORDER BY name COLLATE NOCASE`,
    userId,
  );
  return rows.map((row) => ({
    id: row.id,
    name: row.name,
    balanceAmount: row.balance_amount,
  }));
}

export async function listInvoices(
  db: SQLiteDatabase,
  userId: string,
): Promise<InvoiceSummary[]> {
  const rows = await db.getAllAsync<{
    id: string;
    invoice_number: number;
    customer_name: string;
    invoice_date: string;
    total_amount: number;
  }>(
    `SELECT id, invoice_number, customer_name, invoice_date, total_amount
     FROM invoices
     WHERE user_id = ?
     ORDER BY invoice_number DESC`,
    userId,
  );
  return rows.map((row) => ({
    id: row.id,
    invoiceNumber: row.invoice_number,
    customerName: row.customer_name,
    date: row.invoice_date,
    totalAmount: row.total_amount,
  }));
}

export class SaveInvoiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SaveInvoiceError';
  }
}

export async function saveInvoice(
  db: SQLiteDatabase,
  userId: string,
  invoice: Invoice,
): Promise<void> {
  const customerName = invoice.customerName.trim();
  if (!customerName) {
    throw new SaveInvoiceError('Add a customer before saving.');
  }
  if (invoice.items.length === 0) {
    throw new SaveInvoiceError('Add at least one item before saving.');
  }

  const totalAmount = getInvoiceTotal(invoice);
  const now = new Date().toISOString();

  await db.withTransactionAsync(async () => {
    let customer = await db.getFirstAsync<{ id: string }>(
      `SELECT id FROM customers
       WHERE user_id = ? AND name = ? COLLATE NOCASE`,
      userId,
      customerName,
    );

    if (!customer) {
      const customerId = newId();
      await db.runAsync(
        `INSERT INTO customers (id, user_id, name, balance_amount, created_at)
         VALUES (?, ?, ?, ?, ?)`,
        customerId,
        userId,
        customerName,
        0,
        now,
      );
      customer = { id: customerId };
    }

    await db.runAsync(
      'UPDATE customers SET balance_amount = balance_amount + ? WHERE id = ?',
      totalAmount,
      customer.id,
    );

    const nextRow = await db.getFirstAsync<{ next: number }>(
      `SELECT COALESCE(MAX(invoice_number), 0) + 1 AS next
       FROM invoices
       WHERE user_id = ?`,
      userId,
    );
    const invoiceNumber = nextRow?.next ?? 1;
    const invoiceId = newId();

    await db.runAsync(
      `INSERT INTO invoices (
         id, user_id, customer_id, invoice_number, customer_name,
         total_amount, invoice_date, created_at
       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      invoiceId,
      userId,
      customer.id,
      invoiceNumber,
      customerName,
      totalAmount,
      now,
      now,
    );

    for (const item of invoice.items) {
      const itemName = item.name.trim();
      if (!itemName) {
        continue;
      }

      await db.runAsync(
        `INSERT INTO invoice_items (
           id, invoice_id, name, quantity, discount_percent,
           price_per_item, discount_amount, item_date
         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        newId(),
        invoiceId,
        itemName,
        item.quantity,
        item.discountPercent,
        item.pricePerItem,
        item.discountAmount,
        now,
      );

      const soldQty = item.quantity ?? 0;
      const sellingPrice = item.pricePerItem ?? 0;
      const stock = await db.getFirstAsync<{ id: string; quantity: number }>(
        `SELECT id, quantity FROM stock
         WHERE user_id = ? AND name = ? COLLATE NOCASE`,
        userId,
        itemName,
      );

      if (stock) {
        await db.runAsync(
          'UPDATE stock SET quantity = ? WHERE id = ?',
          Math.max(0, stock.quantity - soldQty),
          stock.id,
        );
      } else {
        await db.runAsync(
          `INSERT INTO stock (
             id, user_id, name, quantity, cost_price, selling_price, created_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?)`,
          newId(),
          userId,
          itemName,
          0,
          0,
          sellingPrice,
          now,
        );
      }
    }
  });
}
