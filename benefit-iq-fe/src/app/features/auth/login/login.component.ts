import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PasswordInputComponent } from '../../../shared/ui/password-input/password-input.component';
import { AuthApiService } from '../services/auth-api.service';
import { SocialAuthService, GoogleLoginProvider, MicrosoftLoginProvider } from '@abacritt/angularx-social-login';
import { TokenService } from '../../../core/services/token.service';
import { AuthStore } from '../../../core/state/auth.store';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    RouterModule,
    MatButtonModule, 
    MatInputModule, 
    MatFormFieldModule, 
    MatCardModule,
    MatProgressSpinnerModule,
    PasswordInputComponent
  ],
  templateUrl: './login.component.html'
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  private readonly socialAuthService = inject(SocialAuthService);
  private readonly tokenService = inject(TokenService);
  private readonly authStore = inject(AuthStore);

  loginForm: FormGroup;
  isLoading = signal(false);
  error = signal<string | null>(null);

  constructor() {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  ngOnInit() {
    this.socialAuthService.authState.subscribe((user) => {
      if (user && user.provider) {
        this.isLoading.set(true);
        this.authApi.ssoCallback(user.provider.toLowerCase(), { token: user.idToken }).subscribe({
          next: (res) => {
            this.isLoading.set(false);
            const tokenData = res.data || res;
            if (tokenData && tokenData.access_token && tokenData.refresh_token) {
              this.tokenService.setTokens(tokenData.access_token, tokenData.refresh_token);
              this.authStore.loadProfile();
              this.router.navigate(['/']);
            }
          },
          error: (err) => {
            this.isLoading.set(false);
            this.error.set(err.error?.detail || 'SSO Authentication failed.');
          }
        });
      }
    });
  }

  async onSubmit() {
    if (this.loginForm.invalid) return;

    this.isLoading.set(true);
    this.error.set(null);

    try {
      const encryptedPassword = await this.authApi.encryptPassword(this.loginForm.value.password!);
      
      this.authApi.login({
        email: this.loginForm.value.email,
        password: encryptedPassword
      }).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.router.navigate(['/auth/verify-otp'], { 
            queryParams: { email: this.loginForm.value.email, type: 'login' } 
          });
        },
        error: (err) => {
          this.isLoading.set(false);
          this.error.set(this.errorMessage(err, 'Login failed. Please try again.'));
        }
      });
    } catch (e) {
      this.isLoading.set(false);
      this.error.set('Failed to encrypt password or communicate with server.');
    }
  }

  private errorMessage(error: { error?: { detail?: unknown } }, fallback: string): string {
    const detail = error.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map(item => item.msg ?? String(item)).join('. ');
    return fallback;
  }

  loginWithProvider(provider: string) {
    if (provider === 'google') {
      this.socialAuthService.signIn(GoogleLoginProvider.PROVIDER_ID);
    } else if (provider === 'microsoft') {
      this.socialAuthService.signIn(MicrosoftLoginProvider.PROVIDER_ID);
    }
  }
}
