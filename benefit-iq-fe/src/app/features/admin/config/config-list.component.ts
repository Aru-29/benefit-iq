import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterModule, Router } from '@angular/router';
import { AdminApiService, AppConfig } from '../services/admin-api.service';
import { DataTableComponent, TableColumn } from '../../../shared/ui/data-table/data-table.component';
import { HasRoleDirective } from '../../../shared/directives/has-role.directive';

@Component({
  selector: 'app-config-list',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, RouterModule, DataTableComponent, HasRoleDirective],
  templateUrl: './config-list.component.html'
})
export class ConfigListComponent implements OnInit {
  private readonly adminApi = inject(AdminApiService);
  private readonly router = inject(Router);

  configs = signal<AppConfig[]>([]);
  error = signal<string | null>(null);

  columns: TableColumn[] = [
    { def: 'app', header: 'Application', cell: (row: AppConfig) => row.application },
    { def: 'env', header: 'Environment', cell: (row: AppConfig) => row.environment },
    { def: 'key', header: 'Key', cell: (row: AppConfig) => row.config_key },
    { def: 'secret', header: 'Is Secret', cell: (row: AppConfig) => row.is_secret ? 'Yes' : 'No' },
    { def: 'actions', header: 'Actions', cell: (row: AppConfig) => '' }
  ];
  
  displayedColumns = ['app', 'env', 'key', 'secret'];

  ngOnInit(): void {
    this.loadConfigs();
  }

  loadConfigs() {
    this.adminApi.getConfigs().subscribe({
      next: (data) => this.configs.set(data),
      error: (err) => this.error.set(err.error?.detail || 'Failed to load configurations.')
    });
  }
}
