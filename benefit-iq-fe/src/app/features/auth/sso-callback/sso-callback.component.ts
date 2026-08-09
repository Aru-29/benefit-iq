import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthApiService } from '../services/auth-api.service';
import { TokenService } from '../../../core/services/token.service';
import { AuthStore } from '../../../core/state/auth.store';

@Component({
  selector: 'app-sso-callback',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="layout-fullscreen-center">
      <div class="card" style="text-align: center;">
        <h2 style="margin-bottom: var(--space-md)">Authenticating...</h2>
        <div class="spinner"></div>
        <p style="margin-top: var(--space-md)">Please wait while we verify your sign-in.</p>
        <div *ngIf="error()" class="alert alert-error" style="margin-top: var(--space-md)">
          {{ error() }}
        </div>
      </div>
    </div>
  `
})
export class SsoCallbackComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authApi = inject(AuthApiService);
  private readonly tokenService = inject(TokenService);
  private readonly authStore = inject(AuthStore);

  error = signal<string | null>(null);

  ngOnInit() {
    const provider = this.route.snapshot.paramMap.get('provider');
    const code = this.route.snapshot.queryParamMap.get('code');
    const token = this.route.snapshot.queryParamMap.get('token') || this.route.snapshot.queryParamMap.get('access_token');

    if (!provider || (!code && !token)) {
      this.error.set('Invalid single sign-on response.');
      setTimeout(() => this.router.navigate(['/auth/login']), 3000);
      return;
    }

    this.authApi.ssoCallback(provider, { code, token }).subscribe({
      next: (res) => {
        const tokenData = res.data || res;
        if (tokenData && tokenData.access_token && tokenData.refresh_token) {
          this.tokenService.setTokens(tokenData.access_token, tokenData.refresh_token);
          this.authStore.loadProfile();
          this.router.navigate(['/']);
        } else {
          this.error.set('Login failed. Please try again.');
          setTimeout(() => this.router.navigate(['/auth/login']), 3000);
        }
      },
      error: (err) => {
        this.error.set(err.error?.detail || 'Authentication failed. Please try again.');
        setTimeout(() => this.router.navigate(['/auth/login']), 3000);
      }
    });
  }
}
