export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role_id?: string;
  role_name?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at?: string;
  password_hash?: string | null;
}

export interface AuthState {
  user: User | null;
  role: string | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}
