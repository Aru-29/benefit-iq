import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthStore } from '../state/auth.store';

export const roleGuard: CanActivateFn = (route, state) => {
  const authStore = inject(AuthStore);
  const router = inject(Router);

  // The expected roles are passed in the route data
  const expectedRoles: string[] = route.data['roles'] || [];
  const currentRole = authStore.role();

  if (currentRole && expectedRoles.includes(currentRole)) {
    return true;
  }

  // If unauthorized for the role, we should redirect to an unauthorized page or dashboard
  return router.createUrlTree(['/unauthorized']);
};
