export interface User {
  id: string;
  name: string | null;
  companyName: string | null;
  createdAt: string;
}

/** Local session shape (replaces Supabase Session for demo auth). */
export interface Session {
  user: {
    id: string;
    email?: string | null;
    phone?: string | null;
  };
}
