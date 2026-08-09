import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthApiService } from '../services/auth-api.service';
import { TokenService } from '../../../core/services/token.service';
import { AuthStore } from '../../../core/state/auth.store';

@Component({
  selector: 'app-otp-verify',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule, 
    RouterModule,
    MatButtonModule, 
    MatInputModule, 
    MatFormFieldModule, 
    MatCardModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="layout-fullscreen-center">
      <mat-card class="card">
        <div class="card-header">
          <h1>Verification Required</h1>
          <p>Please enter the 6-digit code sent to <strong>{{ email }}</strong></p>
        </div>

        <form [formGroup]="otpForm" (ngSubmit)="onSubmit()">
          <div *ngIf="error()" class="alert alert-error">
            {{ error() }}
          </div>
          <div *ngIf="successMsg()" class="alert alert-success">
            {{ successMsg() }}
          </div>

          <div class="form-group">
            <mat-form-field appearance="outline" style="width: 100%;">
              <mat-label>6-Digit OTP</mat-label>
              <input matInput formControlName="otp" maxlength="6" autocomplete="one-time-code" required style="text-align: center; letter-spacing: 0.25em; font-size: var(--font-2xl);">
              <mat-error *ngIf="otpForm.get('otp')?.hasError('required')">Code is required</mat-error>
              <mat-error *ngIf="otpForm.get('otp')?.hasError('pattern')">Must be 6 digits</mat-error>
            </mat-form-field>
          </div>

          <button class="btn-primary" type="submit" [disabled]="otpForm.invalid || isLoading()">
            <span *ngIf="isLoading()" class="spinner"></span>
            <span *ngIf="!isLoading()">Verify & Continue</span>
          </button>
        </form>
      </mat-card>
    </div>
  `
})
export class OtpVerifyComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly tokenService = inject(TokenService);
  private readonly authStore = inject(AuthStore);

  email: string = '';
  purpose: string = '';

  otpForm: FormGroup = this.fb.group({
    otp: ['', [Validators.required, Validators.pattern(/^[0-9]{6}$/)]]
  });

  isLoading = signal(false);
  error = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  ngOnInit(): void {
    this.email = this.route.snapshot.queryParamMap.get('email') || '';
    const rawPurpose = this.route.snapshot.queryParamMap.get('purpose') || this.route.snapshot.queryParamMap.get('type') || 'login';
    this.purpose = rawPurpose.toLowerCase();

    if (!this.email) {
      this.router.navigate(['/auth/login']);
    }
  }

  onSubmit() {
    if (this.otpForm.invalid) return;

    this.isLoading.set(true);
    this.error.set(null);

    const otp = this.otpForm.value.otp;
    const payload = { email: this.email, otp };

    const isRegistration = this.purpose === 'register' || this.purpose === 'registration';
    const request$ = isRegistration 
      ? this.authApi.verifyRegistrationOtp(payload)
      : this.authApi.verifyLoginOtp(payload);

    request$.subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.successMsg.set('Verification successful!');
        
        const tokenData = res.data || res;
        if (tokenData && tokenData.access_token && tokenData.refresh_token) {
          this.tokenService.setTokens(tokenData.access_token, tokenData.refresh_token);
          this.authStore.loadProfile(); // Load profile immediately after token sets
          
          // Redirect to landing page
          setTimeout(() => {
            this.router.navigate(['/']);
          }, 600);
        } else {
          this.router.navigate(['/auth/login']);
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.error.set(err.error?.detail || err.error?.error?.message || 'Invalid or expired OTP.');
      }
    });
  }
}
