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
  template: `
    <div class="layout-fullscreen-center">
      <mat-card class="card">
        <div class="card-header">
          <h1>Sign in to BenefitIQ</h1>
          <p>Or <a routerLink="/auth/register">create a new account</a></p>
        </div>

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <div *ngIf="error()" class="alert alert-error">
            {{ error() }}
          </div>

          <div class="form-group">
            <mat-form-field appearance="outline">
              <mat-label>Email address</mat-label>
              <input matInput type="email" formControlName="email" autocomplete="email" required>
              <mat-error *ngIf="loginForm.get('email')?.hasError('required')">Email is required</mat-error>
              <mat-error *ngIf="loginForm.get('email')?.hasError('email')">Please enter a valid email</mat-error>
            </mat-form-field>

            <app-password-input 
              formControlName="password" 
              label="Password" 
              placeholder="Enter your password">
            </app-password-input>
          </div>

          <div class="layout-flex-between" style="margin-bottom: var(--space-md);">
            <div style="flex: 1"></div>
            <a href="#">Forgot your password?</a>
          </div>

          <button class="btn-primary" type="submit" [disabled]="loginForm.invalid || isLoading()">
            <span *ngIf="isLoading()" class="spinner"></span>
            <span *ngIf="!isLoading()">Sign in</span>
          </button>
        </form>

        <div style="margin-top: var(--space-xl); text-align: center;">
          <p style="margin-bottom: var(--space-md); color: var(--text-muted); font-size: var(--font-sm);">Or continue with</p>
          <div class="layout-flex-row" style="justify-content: center;">
            <button mat-stroked-button (click)="loginWithProvider('google')" style="flex: 1; border-radius: var(--border-radius);">
              Google
            </button>
            <button mat-stroked-button (click)="loginWithProvider('microsoft')" style="flex: 1; border-radius: var(--border-radius);">
              Microsoft
            </button>
          </div>
        </div>
      </mat-card>
    </div>
  `
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
          this.error.set(err.error?.detail || 'Login failed. Please try again.');
        }
      });
    } catch (e) {
      this.isLoading.set(false);
      this.error.set('Failed to encrypt password or communicate with server.');
    }
  }

  loginWithProvider(provider: string) {
    if (provider === 'google') {
      this.socialAuthService.signIn(GoogleLoginProvider.PROVIDER_ID);
    } else if (provider === 'microsoft') {
      this.socialAuthService.signIn(MicrosoftLoginProvider.PROVIDER_ID);
    }
  }
}
