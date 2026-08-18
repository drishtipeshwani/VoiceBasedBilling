# On-device database

All shop data stays on the phone in SQLite (`voicebilling.db`) via [`expo-sqlite`](https://docs.expo.dev/versions/v57.0.0/sdk/sqlite/). There is no remote database. Migrations run on app start in `schema.ts` (`PRAGMA user_version`, currently **4**). Queries live in `queries.ts`.

The PIN is stored separately in the device keychain (`expo-secure-store`), not in SQLite.

## Tables

```
users 1──* stock
users 1──* customers
users 1──* invoices
customers 1──* invoices
invoices 1──* invoice_items
```

### `users`

The shop owner. The app currently supports a single registered user.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT PK | UUID |
| `name` | TEXT | |
| `email` | TEXT | optional |
| `phone` | TEXT | optional |
| `company_name` | TEXT | printed on invoices |
| `created_at` | TEXT | ISO timestamp |

### `stock`

Inventory catalog. Names are unique per user, case-insensitive.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT PK | UUID |
| `user_id` | TEXT FK → users | cascade delete |
| `name` | TEXT | normalized display name |
| `quantity` | REAL | units on hand; can go negative if more is sold than stocked |
| `cost_price` | REAL | |
| `selling_price` | REAL | default rate when adding the item to a bill |
| `created_at` | TEXT | ISO timestamp |

Unique: `(user_id, name COLLATE NOCASE)`.

### `customers`

Ledger of customers and what they owe.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT PK | UUID |
| `user_id` | TEXT FK → users | cascade delete |
| `name` | TEXT | normalized display name |
| `balance_amount` | REAL | outstanding rupees; 0 is settled |
| `created_at` | TEXT | ISO timestamp |

Unique: `(user_id, name COLLATE NOCASE)`.

### `invoices`

Saved bills. `invoice_number` is assigned per user, starting at 1.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT PK | UUID |
| `user_id` | TEXT FK → users | cascade delete |
| `customer_id` | TEXT FK → customers | required; customer must already exist |
| `invoice_number` | INTEGER | unique per user |
| `customer_name` | TEXT | snapshot of the name at save time |
| `total_amount` | REAL | after item and bill discounts |
| `invoice_date` | TEXT | ISO date |
| `created_at` | TEXT | ISO timestamp |
| `discount_percent` | REAL | whole-bill percent discount |
| `discount_amount` | REAL | whole-bill rupee discount |
| `snapshot` | TEXT | JSON copy of the full invoice used for later viewing |

Unique: `(user_id, invoice_number)`.

### `invoice_items`

Line items on a saved invoice. Cascade-deleted with the parent invoice.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT PK | UUID |
| `invoice_id` | TEXT FK → invoices | cascade delete |
| `name` | TEXT | |
| `quantity` | REAL | |
| `price_per_item` | REAL | |
| `discount_percent` | REAL | item-level percent discount |
| `discount_amount` | REAL | item-level rupee discount |

Percent and amount discounts are alternatives; the app does not set both on the same item or bill.

## What happens on save

Saving is a single SQLite transaction:

1. The customer must already exist in `customers`; every line item must already exist in `stock`.
2. The invoice total is added to that customer's `balance_amount`.
3. The invoice row and its `invoice_items` are inserted. `snapshot` stores the full invoice JSON so Accounts can reopen the bill as it was saved.
4. Each line item deducts its quantity from `stock.quantity`.

Re-adding an existing stock name increases quantity instead of inserting a duplicate. Customer names cannot be duplicated.
