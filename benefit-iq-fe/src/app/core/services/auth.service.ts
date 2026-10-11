import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import { TokenService } from './token.service';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly tokenService = inject(TokenService);
  private readonly apiUrl = '/api/v1/auth';

  refreshToken(): Observable<TokenResponse> {
    const refreshToken = this.tokenService.getRefreshToken();
    return this.http.post<{data: TokenResponse}>(`${this.apiUrl}/refresh`, { refresh_token: refreshToken }).pipe(
      map(response => response.data),
      tap(response => {
        this.tokenService.setTokens(response.access_token, response.refresh_token);
      })
    );
  }

  logout(): void {
    const refreshToken = this.tokenService.getRefreshToken();
    if (refreshToken) {
      this.http.post(`${this.apiUrl}/logout`, { refresh_token: refreshToken }).subscribe({
        next: () => {},
        error: () => {}
      });
    }
    this.tokenService.clearTokens();
  }

  getProfile(): Observable<any> {
    return this.http.get('/api/v1/users/me');
  }
}
