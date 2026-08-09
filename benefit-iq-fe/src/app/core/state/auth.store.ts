import { inject } from '@angular/core';
import { signalStore, withState, withMethods, patchState } from '@ngrx/signals';
import { AuthState, User } from '../models/user.model';
import { AuthService } from '../services/auth.service';
import { TokenService } from '../services/token.service';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap, catchError, of } from 'rxjs';

const initialState: AuthState = {
  user: null,
  role: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,
};

export const AuthStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withMethods((store, authService = inject(AuthService), tokenService = inject(TokenService)) => ({
    
    setLoading: (isLoading: boolean) => patchState(store, { isLoading }),
    setError: (error: string | null) => patchState(store, { error }),
    setUser: (user: User | null, role: string | null) => patchState(store, { user, role, isAuthenticated: !!user }),
    
    logout: () => {
      authService.logout();
      patchState(store, initialState);
    },

    loadProfile: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoading: true, error: null })),
        switchMap(() => {
          if (!tokenService.hasTokens()) {
            patchState(store, { isLoading: false, isAuthenticated: false });
            return of(null);
          }
          return authService.getProfile().pipe(
            tap((response) => {
              const userData = response.data || response.user || response;
              const userRole = userData?.role_name || response?.role || 'CUSTOMER';
              patchState(store, { 
                user: userData, 
                role: userRole, 
                isAuthenticated: true, 
                isLoading: false 
              });
            }),
            catchError((err) => {
              patchState(store, { error: err.message, isLoading: false, isAuthenticated: false });
              return of(null);
            })
          );
        })
      )
    ),

    init: () => {
      if (tokenService.hasTokens()) {
        // We can call loadProfile here if needed
        // For now, let's just trigger loadProfile in the app component or route guards.
      }
    }
  }))
);
