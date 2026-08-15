import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Session, User } from '../types/auth';

const AUTH_STORAGE_KEY = '@voicebilling/local_auth';

interface AuthResult {
  error: string | null;
}

interface SignUpResult extends AuthResult {
  needsEmailConfirmation: boolean;
}

interface StoredAuth {
  session: Session;
  user: User;
}

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signInWithPassword: (email: string, password: string) => Promise<AuthResult>;
  signUpWithPassword: (
    email: string,
    password: string,
    name: string,
    companyName: string,
  ) => Promise<SignUpResult>;
  sendPhoneOtp: (phone: string, name?: string, companyName?: string) => Promise<AuthResult>;
  verifyPhoneOtp: (phone: string, code: string) => Promise<AuthResult>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function makeId(): string {
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

async function persistAuth(payload: StoredAuth | null): Promise<void> {
  if (!payload) {
    await AsyncStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }
  await AsyncStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(payload));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingPhoneProfile, setPendingPhoneProfile] = useState<{
    phone: string;
    name?: string;
    companyName?: string;
  } | null>(null);

  useEffect(() => {
    let isMounted = true;

    AsyncStorage.getItem(AUTH_STORAGE_KEY)
      .then((raw) => {
        if (!isMounted) return;
        if (raw) {
          try {
            const stored = JSON.parse(raw) as StoredAuth;
            setSession(stored.session);
            setUser(stored.user);
          } catch {
            // ignore corrupt storage
          }
        }
        setLoading(false);
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const establishSession = useCallback(
    async (next: StoredAuth) => {
      await persistAuth(next);
      setSession(next.session);
      setUser(next.user);
    },
    [],
  );

  const signInWithPassword = useCallback(
    async (email: string, _password: string): Promise<AuthResult> => {
      const id = makeId();
      await establishSession({
        session: { user: { id, email } },
        user: {
          id,
          name: null,
          companyName: null,
          createdAt: new Date().toISOString(),
        },
      });
      return { error: null };
    },
    [establishSession],
  );

  const signUpWithPassword = useCallback(
    async (
      email: string,
      _password: string,
      name: string,
      companyName: string,
    ): Promise<SignUpResult> => {
      const id = makeId();
      await establishSession({
        session: { user: { id, email } },
        user: {
          id,
          name: name.trim() || null,
          companyName: companyName.trim() || null,
          createdAt: new Date().toISOString(),
        },
      });
      return { error: null, needsEmailConfirmation: false };
    },
    [establishSession],
  );

  const sendPhoneOtp = useCallback(
    async (phone: string, name?: string, companyName?: string): Promise<AuthResult> => {
      setPendingPhoneProfile({ phone, name, companyName });
      return { error: null };
    },
    [],
  );

  const verifyPhoneOtp = useCallback(
    async (phone: string, _code: string): Promise<AuthResult> => {
      const profile = pendingPhoneProfile?.phone === phone ? pendingPhoneProfile : { phone };
      const id = makeId();
      await establishSession({
        session: { user: { id, phone } },
        user: {
          id,
          name: profile.name?.trim() || null,
          companyName: profile.companyName?.trim() || null,
          createdAt: new Date().toISOString(),
        },
      });
      setPendingPhoneProfile(null);
      return { error: null };
    },
    [establishSession, pendingPhoneProfile],
  );

  const signOut = useCallback(async () => {
    await persistAuth(null);
    setSession(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user,
      loading,
      signInWithPassword,
      signUpWithPassword,
      sendPhoneOtp,
      verifyPhoneOtp,
      signOut,
    }),
    [
      session,
      user,
      loading,
      signInWithPassword,
      signUpWithPassword,
      sendPhoneOtp,
      verifyPhoneOtp,
      signOut,
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
