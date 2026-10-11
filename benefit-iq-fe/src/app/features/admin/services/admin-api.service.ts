import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AppConfig {
  id?: string;
  application: string;
  environment: string;
  config_key: string;
  config_value?: string | null;
  is_secret: boolean;
  secret_path?: string | null;
  secret_key?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface UserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role_id?: string;
  is_active: boolean;
  is_verified: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AdminApiService {
  private readonly http = inject(HttpClient);
  private readonly configUrl = '/api/v1/config';
  private readonly usersUrl = '/api/v1/users';

  // Config Endpoints
  getConfigs(): Observable<AppConfig[]> {
    return this.http.get<AppConfig[]>(this.configUrl);
  }

  getConfig(id: string): Observable<AppConfig> {
    return this.http.get<AppConfig>(`${this.configUrl}/${id}`);
  }

  createConfig(config: AppConfig): Observable<AppConfig> {
    return this.http.post<AppConfig>(this.configUrl, config);
  }

  updateConfig(id: string, config: AppConfig): Observable<AppConfig> {
    return this.http.put<AppConfig>(`${this.configUrl}/${id}`, config);
  }

  deleteConfig(id: string): Observable<any> {
    return this.http.delete(`${this.configUrl}/${id}`);
  }

  // User Endpoints
  getUsers(): Observable<UserResponse[]> {
    return this.http.get<UserResponse[]>(this.usersUrl);
  }

  // Dashboard / Analytics Endpoints
  getKpi(): Observable<any> {
    return this.http.get<any>('/api/v1/analytics/kpi');
  }

  getRedisStats(): Observable<any> {
    return this.http.get<any>('/api/v1/system/redis/stats');
  }
  
  getAdminUsers(): Observable<any> {
    return this.http.get<any>('/api/v1/users');
  }
}
