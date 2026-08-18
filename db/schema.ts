import type { SQLiteDatabase } from 'expo-sqlite';
import { backfillInvoiceSnapshots, dedupeCustomersAndStock } from './queries';

const DATABASE_VERSION = 4;

export async function migrateDbIfNeeded(db: SQLiteDatabase): Promise<void> {
  await db.execAsync('PRAGMA foreign_keys = ON;');

  const row = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
  let currentDbVersion = row?.user_version ?? 0;
  if (currentDbVersion >= DATABASE_VERSION) {
    return;
  }

  if (currentDbVersion === 0) {
    await db.execAsync(`
PRAGMA journal_mode = 'wal';
CREATE TABLE users (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  company_name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE stock (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  quantity REAL NOT NULL DEFAULT 0,
  cost_price REAL NOT NULL DEFAULT 0,
  selling_price REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE (user_id, name COLLATE NOCASE)
);
CREATE TABLE customers (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  balance_amount REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE (user_id, name COLLATE NOCASE)
);
CREATE TABLE invoices (
  id TEXT PRIMARY KEY NOT NULL,
  user_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  customer_id TEXT NOT NULL REFERENCES customers (id),
  invoice_number INTEGER NOT NULL,
  customer_name TEXT NOT NULL,
  total_amount REAL NOT NULL,
  invoice_date TEXT NOT NULL,
  created_at TEXT NOT NULL,
  discount_percent REAL,
  discount_amount REAL,
  snapshot TEXT,
  UNIQUE (user_id, invoice_number)
);
CREATE TABLE invoice_items (
  id TEXT PRIMARY KEY NOT NULL,
  invoice_id TEXT NOT NULL REFERENCES invoices (id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  quantity REAL,
  discount_percent REAL,
  price_per_item REAL,
  discount_amount REAL
);
`);
    currentDbVersion = 3;
  }

  if (currentDbVersion === 1) {
    await db.execAsync(`
ALTER TABLE invoices ADD COLUMN discount_percent REAL;
ALTER TABLE invoices ADD COLUMN discount_amount REAL;
`);
    currentDbVersion = 2;
  }

  if (currentDbVersion === 2) {
    await db.execAsync('ALTER TABLE invoices ADD COLUMN snapshot TEXT;');
    await db.execAsync(`
PRAGMA foreign_keys = OFF;
CREATE TABLE invoice_items_new (
  id TEXT PRIMARY KEY NOT NULL,
  invoice_id TEXT NOT NULL REFERENCES invoices (id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  quantity REAL,
  discount_percent REAL,
  price_per_item REAL,
  discount_amount REAL
);
INSERT INTO invoice_items_new (
  id, invoice_id, name, quantity, discount_percent, price_per_item, discount_amount
)
SELECT id, invoice_id, name, quantity, discount_percent, price_per_item, discount_amount
FROM invoice_items;
DROP TABLE invoice_items;
ALTER TABLE invoice_items_new RENAME TO invoice_items;
PRAGMA foreign_keys = ON;
`);
    await backfillInvoiceSnapshots(db);
    currentDbVersion = 3;
  }

  if (currentDbVersion === 3) {
    await dedupeCustomersAndStock(db);
    currentDbVersion = 4;
  }

  await db.execAsync(`PRAGMA user_version = ${DATABASE_VERSION}`);
}
