import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterModule } from '@angular/router';
import { AdminApiService, UserResponse } from '../services/admin-api.service';
import { DataTableComponent, TableColumn } from '../../../shared/ui/data-table/data-table.component';
import { HasRoleDirective } from '../../../shared/directives/has-role.directive';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, RouterModule, DataTableComponent, HasRoleDirective],
  templateUrl: './user-list.component.html'
})
export class UserListComponent implements OnInit {
  private readonly adminApi = inject(AdminApiService);

  users = signal<UserResponse[]>([]);
  error = signal<string | null>(null);

  columns: TableColumn[] = [
    { def: 'name', header: 'Name', cell: (row: UserResponse) => `${row.first_name} ${row.last_name}` },
    { def: 'email', header: 'Email', cell: (row: UserResponse) => row.email },
    { def: 'status', header: 'Status', cell: (row: UserResponse) => row.is_active ? 'Active' : 'Inactive' },
    { def: 'verified', header: 'Verified', cell: (row: UserResponse) => row.is_verified ? 'Yes' : 'No' }
  ];
  
  displayedColumns = ['name', 'email', 'status', 'verified'];

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers() {
    this.adminApi.getUsers().subscribe({
      next: (data) => this.users.set(data),
      error: (err) => this.error.set(err.error?.detail || 'Failed to load users.')
    });
  }
}
