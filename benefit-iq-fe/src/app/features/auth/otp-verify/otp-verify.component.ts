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
  templateUrl: './otp-verify.component.html'
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
