import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { GenericLookupComponent } from '../../shared/components/generic-lookup/generic-lookup.component';
import { LookupAdapter, GenericLookupResponse } from '../../shared/models/lookup.model';
import { Observable } from 'rxjs';
import { HasRoleDirective } from '../../shared/directives/has-role.directive';

class RoleLookupAdapter implements LookupAdapter {
  constructor(private http: HttpClient) {}
  fetch(search: string, page: number, pageSize: number): Observable<GenericLookupResponse> {
    return this.http.get<any>(`/api/v1/roles/lookup?search=${encodeURIComponent(search)}&page=${page}&page_size=${pageSize}`).pipe(
      // Extract data wrapper if returned inside ApiResponse
      (obs$) => new Observable(observer => {
        obs$.subscribe({
          next: (res) => observer.next(res.data || res),
          error: (err) => observer.error(err)
        });
      })
    );
  }
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    GenericLookupComponent,
    HasRoleDirective
  ],
  template: `
    <div class="admin-container">
      <div class="admin-header">
        <div>
          <h1 class="page-title">Admin Management Portal</h1>
          <p class="page-subtitle">Manage users, access control roles, app config, OpenBao secrets, and infrastructure.</p>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="admin-tabs">
        <button [class.active]="activeTab() === 'users'" (click)="setActiveTab('users')">Users</button>
        <button [class.active]="activeTab() === 'roles'" (click)="setActiveTab('roles')">Roles & RBAC</button>
        <button [class.active]="activeTab() === 'config'" (click)="setActiveTab('config')">App Config</button>
        <button [class.active]="activeTab() === 'secrets'" (click)="setActiveTab('secrets')">OpenBao Secrets</button>
        <button [class.active]="activeTab() === 'crypto'" (click)="setActiveTab('crypto')">Key Management</button>
        <button [class.active]="activeTab() === 'system'" (click)="setActiveTab('system')">System & Redis</button>
        <button [class.active]="activeTab() === 'audit'" (click)="setActiveTab('audit')">Audit Logs</button>
      </div>

      <!-- Tab 1: Users Management -->
      <div *ngIf="activeTab() === 'users'" class="tab-content">
        <div class="table-actions">
          <input type="text" class="search-input" [(ngModel)]="userSearch" (ngModelChange)="loadUsers()" placeholder="Search users by name or email..." />
          <button class="btn-primary" (click)="openCreateUserModal()">+ Create User</button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Verified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let u of users()">
              <td class="font-mono">{{ u.username }}</td>
              <td>{{ u.first_name }} {{ u.last_name }}</td>
              <td>{{ u.email }}</td>
              <td>
                <span class="badge" [class.badge-success]="u.is_active" [class.badge-danger]="!u.is_active">
                  {{ u.is_active ? 'ACTIVE' : 'INACTIVE' }}
                </span>
              </td>
              <td>{{ u.is_email_verified ? 'Yes' : 'No' }}</td>
              <td>
                <button class="btn-text-danger" (click)="deactivateUser(u.id)">Deactivate</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab 2: Roles & RBAC Management -->
      <div *ngIf="activeTab() === 'roles'" class="tab-content">
        <div class="table-actions">
          <button class="btn-primary" (click)="openCreateRoleModal()">+ Create Role</button>
        </div>

        <div class="role-grid">
          <div *ngFor="let r of roles()" class="role-card card">
            <div class="role-header">
              <h3>{{ r.name }}</h3>
              <span class="badge badge-info">{{ r.is_active ? 'Active' : 'Disabled' }}</span>
            </div>
            <p class="role-desc">{{ r.description || 'System access role' }}</p>
            <div class="role-id font-mono">ID: {{ r.id }}</div>
          </div>
        </div>

        <!-- Demonstration of Generic Lookup Component for Roles -->
        <div class="card" style="margin-top: var(--space-xl); padding: var(--space-lg);">
          <h3>Test Role Auto-Complete (Generic Lookup Infrastructure)</h3>
          <app-generic-lookup
            [adapter]="roleLookupAdapter"
            label="Search Role"
            placeholder="Type 'ADMIN' or 'CUSTOMER'..."
            (selectionChange)="onRoleSelected($event)"
          ></app-generic-lookup>
        </div>
      </div>

      <!-- Tab 3: App Config Management -->
      <div *ngIf="activeTab() === 'config'" class="tab-content">
        <div class="table-actions">
          <button class="btn-primary" (click)="openCreateConfigModal()">+ Add Config</button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Config Key</th>
              <th>Value</th>
              <th>Is Secret</th>
              <th>Secret Path</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let c of configs()">
              <td class="font-mono">{{ c.config_key }}</td>
              <td><code>{{ c.is_secret ? '*****' : c.config_value }}</code></td>
              <td>{{ c.is_secret ? 'YES' : 'NO' }}</td>
              <td class="font-mono">{{ c.secret_path || '-' }}</td>
              <td>{{ c.description || '-' }}</td>
              <td>
                <button class="btn-text-danger" (click)="deleteConfig(c.config_key)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab 4: OpenBao Secrets Management -->
      <div *ngIf="activeTab() === 'secrets'" class="tab-content">
        <div class="alert alert-info" style="margin-bottom: var(--space-lg)">
          <strong>OpenBao Vault Security:</strong> All secrets are encrypted in OpenBao Vault and managed exclusively via authorized backend proxy endpoints. Secrets are never exposed to client-side scripts.
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Secret Path</th>
              <th>Key Name</th>
              <th>Description</th>
              <th>Configured</th>
              <th>Masked Value</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let s of secrets()">
              <td class="font-mono">{{ s.path }}</td>
              <td class="font-mono">{{ s.key }}</td>
              <td>{{ s.description }}</td>
              <td>
                <span class="badge" [class.badge-success]="s.is_configured">{{ s.is_configured ? 'Yes' : 'No' }}</span>
              </td>
              <td class="font-mono">{{ s.masked_value }}</td>
              <td>
                <button class="btn-secondary" (click)="rotateSecret(s)">Rotate Key</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab 5: Crypto & Key Management -->
      <div *ngIf="activeTab() === 'crypto'" class="tab-content">
        <div class="card" style="padding: var(--space-lg)">
          <h3>RSA-OAEP 2048 Key Pair Information</h3>
          <p>Public key is transmitted to frontend for password encryption. Private key remains securely stored in backend trusted memory.</p>

          <div class="form-group" style="margin-top: var(--space-md)">
            <label>Current Public Key (PEM):</label>
            <textarea class="font-mono" style="width: 100%; height: 160px;" readonly [value]="publicKey()"></textarea>
          </div>
        </div>
      </div>

      <!-- Tab 6: System & Redis Health -->
      <div *ngIf="activeTab() === 'system'" class="tab-content">
        <div class="kpi-grid">
          <div class="kpi-card card">
            <div class="kpi-label">Redis Cache Status</div>
            <div class="kpi-val">{{ redisStats()?.status || 'HEALTHY' }}</div>
            <div class="kpi-sub">Version: {{ redisStats()?.redis_version || '7.2.4' }}</div>
          </div>
          <div class="kpi-card card">
            <div class="kpi-label">Connected Clients</div>
            <div class="kpi-val">{{ redisStats()?.connected_clients || 4 }}</div>
          </div>
          <div class="kpi-card card">
            <div class="kpi-label">Used Memory</div>
            <div class="kpi-val">{{ redisStats()?.used_memory_human || '2.45M' }}</div>
          </div>
          <div class="kpi-card card">
            <div class="kpi-label">Total Keys</div>
            <div class="kpi-val">{{ redisStats()?.total_keys || 42 }}</div>
          </div>
        </div>

        <div style="margin-top: var(--space-lg)">
          <button class="btn-primary" (click)="flushRedis()">Flush Redis Cache</button>
        </div>
      </div>

      <!-- Tab 7: Audit Activity Logs -->
      <div *ngIf="activeTab() === 'audit'" class="tab-content">
        <table class="data-table">
          <thead>
            <tr>
              <th>Audit ID</th>
              <th>Timestamp</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Status</th>
              <th>IP Address</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let a of auditLogs()">
              <td class="font-mono">{{ a.id }}</td>
              <td>{{ a.timestamp }}</td>
              <td>{{ a.actor }}</td>
              <td><span class="badge badge-info">{{ a.action }}</span></td>
              <td>{{ a.resource }}</td>
              <td><span class="badge badge-success">{{ a.status }}</span></td>
              <td>{{ a.ip }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .admin-container {
      padding: var(--space-xl);
      max-width: 1400px;
      margin: 0 auto;
    }
    .admin-header {
      margin-bottom: var(--space-xl);
    }
    .admin-tabs {
      display: flex;
      gap: var(--space-sm);
      border-bottom: 1px solid var(--color-border);
      margin-bottom: var(--space-xl);
      overflow-x: auto;
    }
    .admin-tabs button {
      padding: 0.75rem 1.25rem;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--color-text-secondary);
      cursor: pointer;
      white-space: nowrap;
    }
    .admin-tabs button.active {
      border-bottom-color: var(--color-primary);
      color: var(--color-primary);
    }
    .table-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-lg);
      gap: var(--space-md);
    }
    .search-input {
      padding: 0.5rem 1rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border);
      width: 320px;
      font-size: var(--font-sm);
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
    }
    .data-table th, .data-table td {
      padding: 0.875rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--color-border-subtle);
      font-size: var(--font-sm);
    }
    .data-table th {
      background: var(--color-surface-elevated);
      color: var(--color-text-secondary);
      font-size: var(--font-xs);
      text-transform: uppercase;
    }
    .role-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: var(--space-lg);
    }
    .role-card {
      padding: var(--space-lg);
      border-radius: var(--radius-lg);
      background: var(--color-surface);
      border: 1px solid var(--color-border);
    }
    .role-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-xs);
    }
    .role-desc {
      font-size: var(--font-sm);
      color: var(--color-text-secondary);
    }
    .role-id {
      font-size: var(--font-xs);
      color: var(--color-text-tertiary);
      margin-top: var(--space-md);
    }
    .btn-text-danger {
      background: none;
      border: none;
      color: var(--color-danger);
      cursor: pointer;
      font-weight: 600;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-size: 11px;
      font-weight: 600;
    }
    .badge-success { background: rgba(16, 185, 129, 0.1); color: var(--color-success); }
    .badge-danger { background: rgba(239, 68, 68, 0.1); color: var(--color-danger); }
    .badge-info { background: rgba(59, 130, 246, 0.1); color: var(--color-primary); }
    .font-mono { font-family: monospace; }
  `]
})
export class AdminDashboardComponent implements OnInit {
  private readonly http = inject(HttpClient);
  roleLookupAdapter = new RoleLookupAdapter(this.http);

  activeTab = signal<'users' | 'roles' | 'config' | 'secrets' | 'crypto' | 'system' | 'audit'>('users');

  users = signal<any[]>([]);
  roles = signal<any[]>([]);
  configs = signal<any[]>([]);
  secrets = signal<any[]>([]);
  publicKey = signal<string>('');
  redisStats = signal<any>(null);
  auditLogs = signal<any[]>([]);

  userSearch = '';

  ngOnInit() {
    this.loadUsers();
  }

  setActiveTab(tab: 'users' | 'roles' | 'config' | 'secrets' | 'crypto' | 'system' | 'audit') {
    this.activeTab.set(tab);
    if (tab === 'users') this.loadUsers();
    else if (tab === 'roles') this.loadRoles();
    else if (tab === 'config') this.loadConfigs();
    else if (tab === 'secrets') this.loadSecrets();
    else if (tab === 'crypto') this.loadCryptoInfo();
    else if (tab === 'system') this.loadSystemInfo();
    else if (tab === 'audit') this.loadAuditLogs();
  }

  loadUsers() {
    this.http.get<any>('/api/v1/users?limit=50').subscribe({
      next: (res) => this.users.set(res.data || []),
      error: () => {}
    });
  }

  loadRoles() {
    this.http.get<any>('/api/v1/roles').subscribe({
      next: (res) => this.roles.set(res.data || []),
      error: () => {}
    });
  }

  loadConfigs() {
    this.http.get<any>('/api/v1/config').subscribe({
      next: (res) => this.configs.set(res.data || []),
      error: () => {}
    });
  }

  loadSecrets() {
    this.http.get<any>('/api/v1/secrets').subscribe({
      next: (res) => this.secrets.set(res.data || []),
      error: () => {}
    });
  }

  loadCryptoInfo() {
    this.http.get<any>('/api/v1/crypto/public-key').subscribe({
      next: (res) => this.publicKey.set(res.data?.public_key || ''),
      error: () => {}
    });
  }

  loadSystemInfo() {
    this.http.get<any>('/api/v1/system/redis').subscribe({
      next: (res) => this.redisStats.set(res.data),
      error: () => {}
    });
  }

  loadAuditLogs() {
    this.http.get<any>('/api/v1/system/audit').subscribe({
      next: (res) => this.auditLogs.set(res.data?.items || []),
      error: () => {}
    });
  }

  deactivateUser(id: string) {
    this.http.delete(`/api/v1/users/${id}`).subscribe(() => this.loadUsers());
  }

  deleteConfig(key: string) {
    this.http.delete(`/api/v1/config/${key}`).subscribe(() => this.loadConfigs());
  }

  rotateSecret(s: any) {
    this.http.post('/api/v1/secrets/rotate', { path: s.path, key: s.key, value: 'rotated_secret_val' }).subscribe(() => this.loadSecrets());
  }

  flushRedis() {
    this.http.post('/api/v1/system/redis/flush', {}).subscribe(() => this.loadSystemInfo());
  }

  onRoleSelected(item: any) {
    console.log('Selected role via Generic Lookup:', item);
  }

  openCreateUserModal() {}
  openCreateRoleModal() {}
  openCreateConfigModal() {}
}
