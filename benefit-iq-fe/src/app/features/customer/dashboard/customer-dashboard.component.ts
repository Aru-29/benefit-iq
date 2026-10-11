import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { CustomerApiService, Envelope, Summary, Product, Card, Benefit, Recommendation } from '../services/customer-api.service';

@Component({
  selector: 'app-customer-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './customer-dashboard.component.html',
  styleUrl: './customer-dashboard.component.css'
})
export class CustomerDashboardComponent implements OnInit {
  private customerApi = inject(CustomerApiService);
  summary = signal<Summary | null>(null); products = signal<Product[]>([]); cards = signal<Card[]>([]);
  recommendations = signal<Recommendation[]>([]); error = signal(''); loading = signal(false); busy = signal(false);
  currency = 'USD'; productId = ''; lastFour = ''; amounts: Record<string, number> = {};
  txCard = ''; reference = ''; merchant = ''; mcc = ''; txAmount = 0; txDate = '';
  private usageKeys: Record<string, string> = {};
  
  ngOnInit() { this.load(); }
  
  load() {
    this.loading.set(true); this.error.set('');
    forkJoin({
      summary: this.customerApi.getUtilizationSummary(this.currency),
      products: this.customerApi.getProducts(),
      cards: this.customerApi.getCards(),
      recommendations: this.customerApi.getRecommendations(this.currency)
    }).subscribe({
      next: r => { 
        this.summary.set(r.summary.data); 
        this.products.set(r.products.data); 
        this.cards.set(r.cards.data); 
        this.recommendations.set(r.recommendations.data); 
        this.loading.set(false); 
      }, 
      error: e => { 
        this.loading.set(false); 
        this.fail(e); 
      }
    });
  }
  
  private fail(e: any) { 
    this.busy.set(false); 
    this.error.set(typeof e.error?.detail === 'string' ? e.error.detail : 'Unable to complete the request. Check your input and retry.'); 
  }
  
  addCard() { 
    this.busy.set(true); this.error.set('');
    this.customerApi.addCard({product_id:this.productId, last_four:this.lastFour, alias:'My Explorer'})
      .subscribe({next: () => { this.busy.set(false); this.load(); }, error: e => this.fail(e)}); 
  }
  
  recordUse(b: Benefit) {
    const key = b.card_id+b.benefit_id; this.usageKeys[key] ||= crypto.randomUUID();
    this.busy.set(true); this.error.set('');
    this.customerApi.recordUsage({external_id:this.usageKeys[key], card_id:b.card_id, benefit_id:b.benefit_id, currency:b.currency, value:b.value_type === 'monetary' ? String(this.amounts[key] || 0) : '0'})
      .subscribe({next: () => { this.busy.set(false); delete this.usageKeys[key]; this.load(); }, error: e => this.fail(e)});
  }
  
  addTransaction() {
    this.busy.set(true); this.error.set('');
    this.customerApi.addTransaction({external_id:this.reference, card_id:this.txCard, amount:String(this.txAmount), currency:this.currency, merchant_name:this.merchant, merchant_category_code:this.mcc, transaction_date:new Date(this.txDate).toISOString()})
      .subscribe({next: () => { this.busy.set(false); this.load(); }, error: e => this.fail(e)});
  }
}
