import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import { AdminApiService } from './services/admin-api.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css'
})
export class AdminDashboardComponent implements OnInit {
  private adminApi = inject(AdminApiService);
  kpi = signal<any>(null);
  runtime = signal<any>(null);
  users = signal<any[]>([]);
  error = signal('');
  
  ngOnInit() { this.load(); }
  
  load() {
    this.error.set('');
    forkJoin({
      kpi: this.adminApi.getKpi(),
      runtime: this.adminApi.getRedisStats(),
      users: this.adminApi.getAdminUsers()
    }).subscribe({
      next: r => {
        this.kpi.set(r.kpi.data);
        this.runtime.set(r.runtime.data);
        this.users.set(r.users.data);
      },
      error: () => this.error.set('Unable to load administrative data. Check your session and service availability.')
    });
  }
}
