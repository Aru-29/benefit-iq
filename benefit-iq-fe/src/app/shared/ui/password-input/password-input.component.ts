import { Component, Input, forwardRef, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-password-input',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatInputModule, MatFormFieldModule, MatIconModule, MatButtonModule],
  template: `
    <mat-form-field appearance="outline" style="width: 100%;">
      <mat-label>{{ label }}</mat-label>
      <input 
        matInput 
        [type]="hidePassword() ? 'password' : 'text'" 
        [placeholder]="placeholder"
        [value]="value()"
        (input)="onInput($event)"
        (blur)="onTouched()"
        [disabled]="disabled()">
      <button 
        mat-icon-button 
        matSuffix 
        (click)="togglePasswordVisibility($event)" 
        [attr.aria-label]="'Hide password'" 
        [attr.aria-pressed]="hidePassword()">
        <mat-icon>{{hidePassword() ? 'visibility_off' : 'visibility'}}</mat-icon>
      </button>
      <mat-hint *ngIf="showStrength && value()">Strength: {{ getStrengthLabel() }}</mat-hint>
    </mat-form-field>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => PasswordInputComponent),
      multi: true
    }
  ]
})
export class PasswordInputComponent implements ControlValueAccessor {
  @Input() label: string = 'Password';
  @Input() placeholder: string = 'Enter your password';
  @Input() showStrength: boolean = false;

  value = signal<string>('');
  disabled = signal<boolean>(false);
  hidePassword = signal<boolean>(true);

  onChange: any = () => {};
  onTouched: any = () => {};

  togglePasswordVisibility(event: Event) {
    event.preventDefault();
    this.hidePassword.update(v => !v);
  }

  onInput(event: Event) {
    const val = (event.target as HTMLInputElement).value;
    this.value.set(val);
    this.onChange(val);
  }

  writeValue(obj: any): void {
    this.value.set(obj || '');
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState?(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }

  getStrengthLabel(): string {
    const val = this.value();
    if (!val) return '';
    if (val.length < 8) return 'Weak';
    if (val.match(/^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/)) return 'Strong';
    return 'Medium';
  }
}
