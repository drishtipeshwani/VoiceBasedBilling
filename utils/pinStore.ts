import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';

const PIN_KEY = 'voicebilling.pin';
const BIOMETRIC_KEY = 'voicebilling.biometricEnabled';

interface StoredPin {
  salt: string;
  hash: string;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export function isValidPin(pin: string): boolean {
  return /^\d{4,6}$/.test(pin);
}

export async function storePin(pin: string): Promise<void> {
  const saltBytes = await Crypto.getRandomBytesAsync(16);
  const salt = bytesToHex(saltBytes);
  const hash = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    `${salt}:${pin}`,
  );
  const payload: StoredPin = { salt, hash };
  await SecureStore.setItemAsync(PIN_KEY, JSON.stringify(payload));
}

export async function verifyPin(pin: string): Promise<boolean> {
  const raw = await SecureStore.getItemAsync(PIN_KEY);
  if (!raw) {
    return false;
  }
  let stored: StoredPin;
  try {
    stored = JSON.parse(raw) as StoredPin;
  } catch {
    return false;
  }
  const candidate = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    `${stored.salt}:${pin}`,
  );
  return candidate === stored.hash;
}

export async function setBiometricEnabled(enabled: boolean): Promise<void> {
  await SecureStore.setItemAsync(BIOMETRIC_KEY, enabled ? '1' : '0');
}

export async function getBiometricEnabled(): Promise<boolean> {
  const raw = await SecureStore.getItemAsync(BIOMETRIC_KEY);
  return raw === '1';
}
