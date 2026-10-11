import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Envelope<T> { data: T; }
export interface Product { id: string; name: string; issuer_name: string; description: string; }
export interface Card { id: string; card_alias: string; card_last_four: string; }
export interface Benefit {
  card_id: string; benefit_id: string; benefit_name: string; benefit_category: string;
  entitled_value: string; used_value: string; remaining_value: string; currency: string;
  utilization_percentage: string; status: string; eligibility_reason: string;
  usage_count: number; usage_limit: number | null; value_type: string;
  expiry_date: string; rule_version: number;
}
export interface Summary {
  total_entitled_value: string; total_used_value: string; total_unused_value: string;
  overall_utilization_percentage: string; currency: string; utilizations: Benefit[];
}
export interface Recommendation { id: string; explanation: string; }

@Injectable({
  providedIn: 'root'
})
export class CustomerApiService {
  private readonly http = inject(HttpClient);
  
  getUtilizationSummary(currency: string): Observable<Envelope<Summary>> {
    return this.http.get<Envelope<Summary>>(`/api/v1/analytics/me/utilization?currency=${currency}`);
  }
  
  getProducts(): Observable<Envelope<Product[]>> {
    return this.http.get<Envelope<Product[]>>('/api/v1/analytics/cards');
  }
  
  getCards(): Observable<Envelope<Card[]>> {
    return this.http.get<Envelope<Card[]>>('/api/v1/analytics/me/cards');
  }
  
  getRecommendations(currency: string): Observable<Envelope<Recommendation[]>> {
    return this.http.get<Envelope<Recommendation[]>>(`/api/v1/analytics/me/recommendations?currency=${currency}`);
  }
  
  addCard(body: any): Observable<any> {
    return this.http.post('/api/v1/analytics/me/cards', body);
  }
  
  recordUsage(body: any): Observable<any> {
    return this.http.post('/api/v1/analytics/me/usage', body);
  }
  
  addTransaction(body: any): Observable<any> {
    return this.http.post('/api/v1/analytics/me/transactions', body);
  }
}
