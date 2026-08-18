# Voice Billing App

End-to-end billing software you run by speaking. Create invoices, keep inventory, and manage customers without typing through forms.

The app is built for shops that work hands-free. Tap the mic, speak in English, and the device transcribes the utterance, turns it into structured actions, and updates the bill, ledger, or stock list.

Everything stays on the phone. A fine-tuned LLM runs directly on the device, and shop data lives in local SQLite. No billing records are sent to a server, so the experience works offline and keeps customer and inventory data private.

## Tech stack

| Layer | Choice |
| --- | --- |
| App | [Expo](https://docs.expo.dev/versions/v57.0.0/) SDK 57, React Native, TypeScript |
| Speech | [`expo-speech-recognition`](https://docs.expo.dev/versions/v57.0.0/sdk/speech-recognition/) (on-device Apple STT on iOS) |
| On-device LLM | [`react-native-executorch`](https://docs.swmansion.com/react-native-executorch/) with a fine-tuned LiquidAI **LFM2.5-350M** `.pte` |
| Local database | [`expo-sqlite`](https://docs.expo.dev/versions/v57.0.0/sdk/sqlite/) |
| Auth | PIN via [`expo-secure-store`](https://docs.expo.dev/versions/v57.0.0/sdk/securestore/), optional Face ID / biometrics via [`expo-local-authentication`](https://docs.expo.dev/versions/v57.0.0/sdk/local-authentication/) |
| Invoices | PDF via [`expo-print`](https://docs.expo.dev/versions/v57.0.0/sdk/print/) and [`expo-sharing`](https://docs.expo.dev/versions/v57.0.0/sdk/sharing/) |
| Structured output | [Zod](https://zod.dev/) schemas for invoice, customer, and stock actions |

## Run locally

`react-native-executorch` includes native code, so this app **does not run in Expo Go**. Use a custom development build. Rebuild whenever native dependencies or config plugins change.

```bash
npm install
```

### iOS (macOS + Xcode)

```bash
npx expo run:ios
```

### Android (Android Studio / SDK)

```bash
npx expo run:android
```

### EAS dev client (optional)

```bash
npx eas build --profile development --platform ios
npx eas build --profile development --platform android
```

Install the resulting build, then run `npx expo start` and open the project from that dev client.

On first launch, wait for the on-device model to download and load (progress shows under the mic). Register with a PIN (and Face ID if you want), then tap the mic and speak.

The fine-tuned `.pte` is fetched over HTTPS into the app documents directory. Override the URL with `EXPO_PUBLIC_INVOICE_PTE` in `.env` if needed.

## Features

All of these are driven by voice:

- **Create invoices** — add and rename items, set quantity and price, apply item or bill discounts, set the date and customer, then save.
- **Maintain inventory** — add stock items with quantity, cost price, and selling price. Saving an invoice deducts sold units from stock.
- **Customer ledger** — add customers and outstanding balances. Saving an invoice adds the bill total to that customer's balance.
- **Accounts** — browse saved invoices and open a full copy of a past bill.
- **Share a PDF** of the current invoice.
- **Device lock** — PIN, with optional Face ID / biometrics.

If a spoken customer or stock item is not in the catalog yet, the app pauses the invoice and asks you to add it by voice before continuing.

### Voice agents

One on-device model, three system prompts. Each agent replies with a JSON array of actions (only the fields that utterance set):

1. **Invoice agent** — line items, discounts, date, customer, save / clear. Used on the home screen.
2. **Customer agent** — name and outstanding balance for a ledger draft. Used when adding a customer.
3. **Stock agent** — name, quantity, cost price, and selling price for an inventory draft. Used when adding stock.

## Fine-tuned model

The on-device model is **LiquidAI LFM2.5-350M**, LoRA-fine-tuned to map Indian English speech transcripts to those action arrays.

Training data, hyperparameters, and export notes live in [`finetune_actions/README.md`](finetune_actions/README.md). The ExecuTorch `.pte` export recipe is in [`finetune/README.md`](finetune/README.md).

## Database

Shop data is stored on-device in SQLite (`voicebilling.db`). Schema, tables, and save-time side effects are documented in [`db/README.md`](db/README.md).
