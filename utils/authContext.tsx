import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { AppState } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import { useSQLiteContext } from 'expo-sqlite';
import { getRegisteredUser, insertUser } from '../db/queries';
import type { AuthResult, RegisterInput, User } from '../types/auth';
import {
  getBiometricEnabled,
  isValidPin,
  setBiometricEnabled,
  storePin,
  verifyPin,
} from './pinStore';

interface AuthContextValue {
  user: User | null;
  unlocked: boolean;
  loading: boolean;
  hasRegisteredUser: boolean;
  biometricAvailable: boolean;
  biometricEnabled: boolean;
  register: (input: RegisterInput) => Promise<AuthResult>;
  unlockWithBiometrics: () => Promise<AuthResult>;
  unlockWithPin: (pin: string) => Promise<AuthResult>;
  lock: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function detectBiometrics(): Promise<boolean> {
  const [hasHardware, isEnrolled] = await Promise.all([
    LocalAuthentication.hasHardwareAsync(),
    LocalAuthentication.isEnrolledAsync(),
  ]);
  return hasHardware && isEnrolled;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const [user, setUser] = useState<User | null>(null);
  const [unlocked, setUnlocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricEnabled, setBiometricEnabledState] = useState(false);

  useEffect(() => {
    let isMounted = true;

    Promise.all([getRegisteredUser(db), getBiometricEnabled(), detectBiometrics()])
      .then(([registered, biometricOn, biometricOk]) => {
        if (!isMounted) return;
        setUser(registered);
        setBiometricEnabledState(biometricOn);
        setBiometricAvailable(biometricOk);
        setLoading(false);
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [db]);

  const lock = useCallback(() => {
    setUnlocked(false);
  }, []);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'background') {
        setUnlocked(false);
      }
    });
    return () => subscription.remove();
  }, []);

  const register = useCallback(
    async (input: RegisterInput): Promise<AuthResult> => {
      const name = input.name.trim();
      const companyName = input.companyName.trim();
      if (!name) {
        return { error: 'Please enter your name.' };
      }
      if (!companyName) {
        return { error: 'Please enter your company name.' };
      }
      if (!isValidPin(input.pin)) {
        return { error: 'PIN must be 4 to 6 digits.' };
      }

      const existing = await getRegisteredUser(db);
      if (existing) {
        return { error: 'This device is already set up.' };
      }

      try {
        await storePin(input.pin);
        const enableBiometrics = input.enableBiometrics && (await detectBiometrics());
        await setBiometricEnabled(enableBiometrics);
        const created = await insertUser(db, {
          name,
          companyName,
          email: input.email?.trim() || null,
          phone: input.phone?.trim() || null,
        });
        setUser(created);
        setBiometricEnabledState(enableBiometrics);
        setUnlocked(true);
        return { error: null };
      } catch {
        return { error: 'Could not finish setup. Please try again.' };
      }
    },
    [db],
  );

  const unlockWithBiometrics = useCallback(async (): Promise<AuthResult> => {
    if (!user) {
      return { error: 'No account on this device.' };
    }
    if (!biometricEnabled) {
      return { error: 'Face ID is not enabled.' };
    }

    const available = await detectBiometrics();
    setBiometricAvailable(available);
    if (!available) {
      return { error: 'Face ID is not available. Use your PIN.' };
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Unlock Voice Invoice',
      cancelLabel: 'Use PIN',
      disableDeviceFallback: true,
    });

    if (!result.success) {
      return { error: 'Face ID cancelled. Enter your PIN.' };
    }

    setUnlocked(true);
    return { error: null };
  }, [biometricEnabled, user]);

  const unlockWithPin = useCallback(
    async (pin: string): Promise<AuthResult> => {
      if (!user) {
        return { error: 'No account on this device.' };
      }
      if (!isValidPin(pin)) {
        return { error: 'PIN must be 4 to 6 digits.' };
      }
      const matches = await verifyPin(pin);
      if (!matches) {
        return { error: 'Incorrect PIN.' };
      }
      setUnlocked(true);
      return { error: null };
    },
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      unlocked,
      loading,
      hasRegisteredUser: user != null,
      biometricAvailable,
      biometricEnabled,
      register,
      unlockWithBiometrics,
      unlockWithPin,
      lock,
    }),
    [
      user,
      unlocked,
      loading,
      biometricAvailable,
      biometricEnabled,
      register,
      unlockWithBiometrics,
      unlockWithPin,
      lock,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
