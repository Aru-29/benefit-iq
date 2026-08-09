import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { OtpVerifyComponent } from './otp-verify/otp-verify.component';
import { SsoCallbackComponent } from './sso-callback/sso-callback.component';
// import { ForgotPasswordComponent } from './forgot-password/forgot-password.component';
// import { ResetPasswordComponent } from './reset-password/reset-password.component';

export const authRoutes: Routes = [
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'register',
    component: RegisterComponent
  },
  {
    path: 'verify-otp',
    component: OtpVerifyComponent
  },
  {
    path: ':provider/callback',
    component: SsoCallbackComponent
  },
  // {
  //   path: 'forgot-password',
  //   component: ForgotPasswordComponent
  // },
  // {
  //   path: 'reset-password',
  //   component: ResetPasswordComponent
  // },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  }
];
