import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PasswordInputComponent } from '../../../shared/ui/password-input/password-input.component';
import { AuthApiService } from '../services/auth-api.service';

@Component({
  selector: 'app-register',
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
          <h1>Create an account</h1>
          <p>Or <a routerLink="/auth/login">sign in to your existing account</a></p>
        </div>

        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()">
          <div *ngIf="error()" class="alert alert-error">
            {{ error() }}
          </div>

          <div class="form-group">
            <div class="form-row">
              <mat-form-field appearance="outline">
                <mat-label>First Name</mat-label>
                <input matInput formControlName="first_name" required>
                <mat-error *ngIf="registerForm.get('first_name')?.hasError('required')">Required</mat-error>
              </mat-form-field>
              
              <mat-form-field appearance="outline">
                <mat-label>Last Name</mat-label>
                <input matInput formControlName="last_name" required>
                <mat-error *ngIf="registerForm.get('last_name')?.hasError('required')">Required</mat-error>
              </mat-form-field>
            </div>

            <mat-form-field appearance="outline" style="width: 100%;">
              <mat-label>Email address</mat-label>
              <input matInput type="email" formControlName="email" autocomplete="email" required>
              <mat-error *ngIf="registerForm.get('email')?.hasError('required')">Email is required</mat-error>
              <mat-error *ngIf="registerForm.get('email')?.hasError('email')">Please enter a valid email</mat-error>
            </mat-form-field>

            <app-password-input 
              formControlName="password" 
              label="Password" 
              placeholder="Create a strong password"
              [showStrength]="true">
            </app-password-input>
            
            <app-password-input 
              formControlName="confirmPassword" 
              label="Confirm Password" 
              placeholder="Confirm your password">
            </app-password-input>
            <div *ngIf="registerForm.hasError('passwordMismatch') && registerForm.get('confirmPassword')?.touched" style="color: var(--color-danger); font-size: var(--font-xs); margin-top: var(--space-xs);">
              Passwords do not match
            </div>
          </div>

          <button class="btn-primary" type="submit" [disabled]="registerForm.invalid || isLoading()">
            <span *ngIf="isLoading()" class="spinner"></span>
            <span *ngIf="!isLoading()">Register</span>
          </button>
        </form>
      </mat-card>
    </div>
  `
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);

  registerForm: FormGroup = this.fb.group({
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', Validators.required]
  }, { validators: this.passwordMatchValidator });

  isLoading = signal(false);
  error = signal<string | null>(null);

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirm = control.get('confirmPassword');
    if (password && confirm && password.value !== confirm.value) {
      return { passwordMismatch: true };
    }
    return null;
  }

  async onSubmit() {
    if (this.registerForm.invalid) return;

    this.isLoading.set(true);
    this.error.set(null);

    try {
      const encryptedPassword = await this.authApi.encryptPassword(this.registerForm.value.password!);
      
      this.authApi.register({
        first_name: this.registerForm.value.first_name,
        last_name: this.registerForm.value.last_name,
        email: this.registerForm.value.email,
        password: encryptedPassword,
        username: this.registerForm.value.email
      }).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.router.navigate(['/auth/verify-otp'], { 
            queryParams: { email: this.registerForm.value.email, type: 'registration' }
          });
        },
        error: (err) => {
          this.isLoading.set(false);
          this.error.set(err.error?.detail || 'Registration failed. Please try again.');
        }
      });
    } catch (e) {
      this.isLoading.set(false);
      this.error.set('Failed to encrypt password. Please try again.');
    }
  }
}
