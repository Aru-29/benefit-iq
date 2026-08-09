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
  template: `
    <div class="layout-container" style="padding-top: var(--space-xl)">
      <div class="layout-flex-between" style="margin-bottom: var(--space-lg)">
        <h1>Application Configuration</h1>
        <button class="btn-primary" style="width: auto" routerLink="new" *appHasRole="['ADMIN']">
          <mat-icon>add</mat-icon> Add Config
        </button>
      </div>

      <div *ngIf="error()" class="alert alert-error">
        {{ error() }}
      </div>

      <app-data-table 
        [data]="configs()" 
        [columns]="columns" 
        [displayedColumns]="displayedColumns">
      </app-data-table>
    </div>
  `
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
  
  // Adding edit action manually to the template would require modifying the data-table component to support custom templates,
  // or we can just render an 'Edit' button in the cell using a template ref. 
  // For simplicity, let's update data-table to allow action columns, or just use Router in row click.
  // Actually, since I created data-table, it renders string output from `cell()`. 
  // Wait, I should just modify `data-table.component.ts` to support ng-template for specific columns if needed, 
  // but for now, we'll just show the basic data. In a real app we'd pass a template for the actions column.

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
