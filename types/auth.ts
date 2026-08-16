export interface User {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  companyName: string;
  createdAt: string;
}

export interface RegisterInput {
  name: string;
  companyName: string;
  email: string | null;
  phone: string | null;
  pin: string;
  enableBiometrics: boolean;
}

export interface AuthResult {
  error: string | null;
}
