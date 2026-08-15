# Voice Billing App

An Expo React Native app for voice-driven invoicing. Tap the mic, speak in English, and on-device Whisper transcribes live; each committed segment is sent to an on-device Hammer LLM.

## How it works

- Built with [Expo](https://expo.dev) (TypeScript template).
- Speech-to-text uses [`react-native-executorch`](https://docs.swmansion.com/react-native-executorch/) `useSpeechToText` with **Whisper base.en** and FSMN VAD for live streaming transcription.
- Microphone capture uses [`react-native-audio-api`](https://docs.swmansion.com/react-native-audio-api/) (`AudioRecorder` → 16 kHz mono chunks).
- On each Whisper **committed** segment, the app runs [`useLLM`](https://docs.swmansion.com/react-native-executorch/docs/hooks/natural-language-processing/useLLM) with **LFM2.5-350M quantized**, or a merged fine-tuned `.pte` when `EXPO_PUBLIC_INVOICE_PTE` is set.
- Language is currently English-only (Whisper `.en`).

## Important: this app requires a custom dev build

`react-native-executorch` and `react-native-audio-api` include native code, so this app **will not run inside the plain Expo Go app**. Use a custom development build. Rebuild whenever native dependencies or config plugins change.

## Setup

```bash
npm install
```

## Running the app

### iOS (requires macOS + Xcode)

```bash
npx expo run:ios
```

### Android (requires Android Studio / SDK)

```bash
npx expo run:android
```

### Alternative: EAS dev client build

```bash
npx eas build --profile development --platform ios
npx eas build --profile development --platform android
```

Install the resulting build, then run `npx expo start` and open the project from that dev client.

## Usage

1. Launch the app (via the custom dev build).
2. Wait for on-device models to finish downloading/loading (progress shown under the mic).
3. Tap the mic, grant microphone permission if prompted, and speak in English.
4. Partial text updates live; on a pause, Whisper commits a segment and the Hammer LLM runs on it.
5. Tap stop to end the listening session.

## Project structure

- `App.tsx` — local auth + tabs; wraps the signed-in tree in `OnDeviceAIProvider`.
- `utils/OnDeviceAIProvider.tsx` — loads `useLLM` (stock LFM2.5-350M quantized, or a merged invoice `.pte` when `EXPO_PUBLIC_INVOICE_PTE` is set).
- `screens/HomeScreen.tsx` — invoice UI, mic session, STT → on-device LLM tool calls.
- `utils/executorchInit.ts` — `initExecutorch` with Expo resource fetcher (imported from `index.ts`).
- `app.json` — Expo config, including the `react-native-audio-api` plugin for mic permissions.
- `databaseSchema.md` / `supabase/migrations/` — schema reference only (no live Supabase client).
