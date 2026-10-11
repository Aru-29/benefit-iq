import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/auth';
  login(credentials: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, credentials);
  }

  verifyLoginOtp(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/verify-login-otp`, data);
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  verifyRegistrationOtp(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/verify-registration-otp`, data);
  }

  ssoCallback(provider: string, data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/${provider}/callback`, data);
  }

  async encryptPassword(password: string): Promise<string> {
    const response = await firstValueFrom(this.http.get<{data:{public_key:string}}>(`${this.apiUrl}/public-key`));
    const encoded = response.data.public_key.replace(/-----[^-]+-----/g, '').replace(/\s/g, '');
    const der = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
    const key = await crypto.subtle.importKey('spki', der, {name:'RSA-OAEP', hash:'SHA-256'}, false, ['encrypt']);
    const ciphertext = await crypto.subtle.encrypt({name:'RSA-OAEP'}, key, new TextEncoder().encode(password));
    return btoa(String.fromCharCode(...new Uint8Array(ciphertext)));
  }
}
