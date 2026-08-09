import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthStore } from '../state/auth.store';
import { TokenService } from '../services/token.service';

export const authGuard: CanActivateFn = (route, state) => {
  const tokenService = inject(TokenService);
  const authStore = inject(AuthStore);
  const router = inject(Router);

  if (tokenService.hasTokens()) {
    // We have tokens, ideally we check if the profile is loaded. 
    // If not, we might want to trigger loadProfile here or it will be done at App init.
    return true;
  }

  // Not logged in, redirect to login with return url
  return router.createUrlTree(['/auth/login'], { queryParams: { returnUrl: state.url } });
};
