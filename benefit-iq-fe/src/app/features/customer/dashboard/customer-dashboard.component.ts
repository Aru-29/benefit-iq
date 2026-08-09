import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ChatbotComponent } from '../../../shared/components/chatbot/chatbot.component';

interface KpiData {
  total_claims_ytd: string;
  claims_growth: string;
  approved_claims_pct: string;
  total_savings: string;
  active_members: number;
  avg_processing_days: number;
  loss_ratio_pct: string;
}

interface TrendItem {
  month: string;
  medical: number;
  dental: number;
  vision: number;
  rx: number;
}

interface CategoryItem {
  category: string;
  percentage: number;
  amount: number;
}

@Component({
  selector: 'app-customer-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    ChatbotComponent
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header Bar -->
      <div class="dashboard-header">
        <div>
          <h1 class="page-title">Benefit Utilization Analytics</h1>
          <p class="page-subtitle">Real-time enterprise health plan utilization and claims performance insights.</p>
        </div>

        <div class="header-actions">
          <select class="filter-select" (change)="onTimeframeChange($event)">
            <option value="ytd">Year To Date (2026)</option>
            <option value="q2">Q2 2026</option>
            <option value="q1">Q1 2026</option>
            <option value="12m">Last 12 Months</option>
          </select>
          <button class="btn-primary" (click)="exportReport()">
            Export Report
          </button>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="kpi-grid">
        <div class="kpi-card glass-card">
          <div class="kpi-label">Total Claims (YTD)</div>
          <div class="kpi-val">{{ kpi()?.total_claims_ytd || '$1,482,900' }}</div>
          <div class="kpi-badge badge-positive">{{ kpi()?.claims_growth || '+12.4%' }} vs last year</div>
        </div>

        <div class="kpi-card glass-card">
          <div class="kpi-label">Approved Claims Rate</div>
          <div class="kpi-val">{{ kpi()?.approved_claims_pct || '94.8%' }}</div>
          <div class="kpi-sub">Avg Processing: {{ kpi()?.avg_processing_days || '1.8' }} days</div>
        </div>

        <div class="kpi-card glass-card">
          <div class="kpi-label">Cumulative Savings</div>
          <div class="kpi-val accent-text">{{ kpi()?.total_savings || '$342,150' }}</div>
          <div class="kpi-sub">PPO & Formulary discounts</div>
        </div>

        <div class="kpi-card glass-card">
          <div class="kpi-label">Active Members</div>
          <div class="kpi-val">{{ kpi()?.active_members || '1,420' }}</div>
          <div class="kpi-sub">Loss Ratio: {{ kpi()?.loss_ratio_pct || '68.2%' }}</div>
        </div>
      </div>

      <!-- Analytics Charts Section -->
      <div class="analytics-grid">
        <!-- Monthly Utilization Trend -->
        <div class="card chart-card">
          <div class="card-header">
            <h3>Monthly Claims Trend by Category</h3>
            <span class="badge">Live Feed</span>
          </div>

          <div class="chart-timeline">
            <div *ngFor="let item of trends()" class="timeline-bar-group">
              <div class="bar-stack">
                <div class="bar-segment medical" [style.height.%]="(item.medical / 200000) * 100" [title]="'Medical: $' + item.medical"></div>
                <div class="bar-segment rx" [style.height.%]="(item.rx / 200000) * 100" [title]="'Rx: $' + item.rx"></div>
                <div class="bar-segment dental" [style.height.%]="(item.dental / 200000) * 100" [title]="'Dental: $' + item.dental"></div>
              </div>
              <div class="bar-label">{{ item.month }}</div>
            </div>
          </div>

          <div class="chart-legend">
            <span class="legend-item"><span class="dot medical"></span> Medical Care</span>
            <span class="legend-item"><span class="dot rx"></span> Prescription Drugs</span>
            <span class="legend-item"><span class="dot dental"></span> Dental & Vision</span>
          </div>
        </div>

        <!-- Category Breakdown -->
        <div class="card category-card">
          <div class="card-header">
            <h3>Coverage Category Share</h3>
          </div>

          <div class="category-list">
            <div *ngFor="let cat of categories()" class="category-row">
              <div class="category-info">
                <span class="cat-name">{{ cat.category }}</span>
                <span class="cat-amt">\${{ cat.amount | number }}</span>
              </div>
              <div class="progress-bg">
                <div class="progress-fill" [style.width.%]="cat.percentage"></div>
              </div>
              <span class="cat-pct">{{ cat.percentage }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Claims Activity Feed -->
      <div class="card activity-card">
        <div class="card-header">
          <h3>Recent Claims Activity</h3>
          <button class="btn-text" (click)="loadAnalytics()">Refresh Data</button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Member Name</th>
              <th>Benefit Type</th>
              <th>Claim Amount</th>
              <th>Approved Amount</th>
              <th>Status</th>
              <th>Submitted Date</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let c of mockActivity">
              <td class="font-mono">{{ c.id }}</td>
              <td>{{ c.member_name }}</td>
              <td><span class="badge">{{ c.benefit_type }}</span></td>
              <td>\${{ c.claim_amount | number:'1.2-2' }}</td>
              <td class="font-bold">\${{ c.approved_amount | number:'1.2-2' }}</td>
              <td>
                <span class="status-chip" [class.approved]="c.status === 'APPROVED'" [class.pending]="c.status === 'PENDING'">
                  {{ c.status }}
                </span>
              </td>
              <td>{{ c.submitted_date }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Floating AI Chatbot Widget -->
      <app-chatbot></app-chatbot>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: var(--space-xl);
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: var(--space-xl);
    }
    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: var(--space-md);
    }
    .page-title {
      font-size: var(--font-2xl);
      font-weight: 700;
      color: var(--color-text);
      margin: 0;
    }
    .page-subtitle {
      font-size: var(--font-sm);
      color: var(--color-text-secondary);
      margin: var(--space-xs) 0 0 0;
    }
    .header-actions {
      display: flex;
      gap: var(--space-md);
      align-items: center;
    }
    .filter-select {
      padding: 0.5rem 1rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border);
      background: var(--color-surface);
      color: var(--color-text);
      font-size: var(--font-sm);
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: var(--space-lg);
    }
    .kpi-card {
      padding: var(--space-lg);
      border-radius: var(--radius-xl);
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      box-shadow: var(--shadow-md);
    }
    .kpi-label {
      font-size: var(--font-xs);
      font-weight: 600;
      color: var(--color-text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .kpi-val {
      font-size: var(--font-3xl);
      font-weight: 800;
      color: var(--color-text);
      margin: var(--space-xs) 0;
    }
    .accent-text { color: var(--color-primary); }
    .kpi-badge {
      display: inline-block;
      font-size: var(--font-xs);
      font-weight: 600;
      padding: 2px 8px;
      border-radius: var(--radius-full);
    }
    .badge-positive {
      background: rgba(16, 185, 129, 0.1);
      color: var(--color-success);
    }
    .kpi-sub {
      font-size: var(--font-xs);
      color: var(--color-text-secondary);
    }
    .analytics-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: var(--space-lg);
    }
    @media (max-width: 992px) {
      .analytics-grid { grid-template-columns: 1fr; }
    }
    .chart-card, .category-card, .activity-card {
      padding: var(--space-lg);
      background: var(--color-surface);
      border-radius: var(--radius-xl);
      border: 1px solid var(--color-border);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-lg);
    }
    .card-header h3 {
      font-size: var(--font-lg);
      margin: 0;
    }
    .chart-timeline {
      display: flex;
      justify-content: space-around;
      align-items: flex-end;
      height: 220px;
      padding-top: var(--space-md);
      border-bottom: 1px solid var(--color-border);
    }
    .timeline-bar-group {
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      width: 40px;
    }
    .bar-stack {
      flex: 1;
      width: 24px;
      display: flex;
      flex-direction: column-reverse;
      background: var(--color-surface-hover);
      border-radius: var(--radius-sm);
      overflow: hidden;
    }
    .bar-segment.medical { background: #3b82f6; }
    .bar-segment.rx { background: #8b5cf6; }
    .bar-segment.dental { background: #10b981; }
    .bar-label {
      font-size: var(--font-xs);
      color: var(--color-text-secondary);
      margin-top: 8px;
    }
    .chart-legend {
      display: flex;
      gap: var(--space-lg);
      justify-content: center;
      margin-top: var(--space-md);
      font-size: var(--font-xs);
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .dot.medical { background: #3b82f6; }
    .dot.rx { background: #8b5cf6; }
    .dot.dental { background: #10b981; }
    .category-list {
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
    }
    .category-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .category-info {
      display: flex;
      justify-content: space-between;
      font-size: var(--font-xs);
      font-weight: 500;
    }
    .progress-bg {
      height: 8px;
      background: var(--color-surface-hover);
      border-radius: var(--radius-full);
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: var(--gradient-primary);
      border-radius: var(--radius-full);
    }
    .cat-pct {
      font-size: 11px;
      color: var(--color-text-tertiary);
      text-align: right;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: var(--font-sm);
    }
    .data-table th, .data-table td {
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--color-border-subtle);
    }
    .data-table th {
      font-size: var(--font-xs);
      color: var(--color-text-secondary);
      text-transform: uppercase;
    }
    .status-chip {
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-size: 11px;
      font-weight: 600;
    }
    .status-chip.approved {
      background: rgba(16, 185, 129, 0.1);
      color: var(--color-success);
    }
    .status-chip.pending {
      background: rgba(245, 158, 11, 0.1);
      color: var(--color-warning);
    }
    .font-mono { font-family: monospace; }
    .font-bold { font-weight: 700; }
  `]
})
export class CustomerDashboardComponent implements OnInit {
  private readonly http = inject(HttpClient);

  kpi = signal<KpiData | null>(null);
  trends = signal<TrendItem[]>([]);
  categories = signal<CategoryItem[]>([]);

  mockActivity = [
    { id: 'CLM-2026-001', member_name: 'Jane Doe', benefit_type: 'Medical', claim_amount: 1450.00, approved_amount: 1305.00, status: 'APPROVED', submitted_date: '2026-08-08' },
    { id: 'CLM-2026-002', member_name: 'John Smith', benefit_type: 'Dental', claim_amount: 320.00, approved_amount: 288.00, status: 'APPROVED', submitted_date: '2026-08-07' },
    { id: 'CLM-2026-003', member_name: 'Alice Johnson', benefit_type: 'Vision', claim_amount: 210.00, approved_amount: 210.00, status: 'APPROVED', submitted_date: '2026-08-06' },
    { id: 'CLM-2026-004', member_name: 'Robert Davis', benefit_type: 'Prescription', claim_amount: 85.50, approved_amount: 76.95, status: 'APPROVED', submitted_date: '2026-08-05' },
    { id: 'CLM-2026-005', member_name: 'Emily Wilson', benefit_type: 'Medical', claim_amount: 2890.00, approved_amount: 0.00, status: 'PENDING', submitted_date: '2026-08-05' }
  ];

  ngOnInit() {
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.http.get<any>('/api/v1/analytics/kpi').subscribe({
      next: (res) => this.kpi.set(res.data),
      error: () => {}
    });

    this.http.get<any>('/api/v1/analytics/utilization-trends').subscribe({
      next: (res) => this.trends.set(res.data),
      error: () => {}
    });

    this.http.get<any>('/api/v1/analytics/category-breakdown').subscribe({
      next: (res) => this.categories.set(res.data),
      error: () => {}
    });
  }

  onTimeframeChange(event: Event) {
    this.loadAnalytics();
  }

  exportReport() {
    const csvContent = 'data:text/csv;charset=utf-8,Claim ID,Member,Type,Amount,Approved,Status,Date\n' +
      this.mockActivity.map(e => `${e.id},${e.member_name},${e.benefit_type},${e.claim_amount},${e.approved_amount},${e.status},${e.submitted_date}`).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'benefit_utilization_report.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
