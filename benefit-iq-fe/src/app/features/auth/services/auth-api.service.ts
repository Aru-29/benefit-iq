import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import * as forge from 'node-forge';

@Injectable({
  providedIn: 'root'
})
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/auth';
  private readonly cryptoUrl = '/api/v1/crypto';

  private readonly publicKey = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAw2+R0dcYrz45ECRJyThr
v0t1lzYJiexvyvaoUVMQt7Dllto84K4hq+U/vGcIJDWs0hTeYokS5fT+K4cWOgT4
iioFctFSprusQ3+4k8XLp8u7OFF+kfoRnTAbvrMxdaMOI8iEgKKEAr5LaMJk9I9n
nG+Zq4t4tnNHJnne8qFujlPCzJr2pPxLMCsvZ9F3hvt/mmFdSPHzJjeTYxrhRU+u
4YYeOKroiFK7W1S2NAQs475W+B1H5nicMourhY/V0XC8EVK3+5A4bFwaOeaA579l
HZOsV2iZYATb/21HRzG++jQ2ozEgBGmkmpTO/egkxkf/xHpInTtZoBdjXzHCQnH7
7wIDAQAB
-----END PUBLIC KEY-----`;

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
    
    try {
      const publicKey = forge.pki.publicKeyFromPem(this.publicKey);
      const encrypted = publicKey.encrypt(password, 'RSA-OAEP', {
        md: forge.md.sha256.create(),
        mgf1: forge.mgf.mgf1.create(forge.md.sha256.create())
      });
      return forge.util.encode64(encrypted);
    } catch (e) {
      console.error('Encryption failed', e);
      // Fallback or throw
      return password; 
    }
  }
}
