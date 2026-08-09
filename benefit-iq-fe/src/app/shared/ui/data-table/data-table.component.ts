import { Component, Input, ViewChild, AfterViewInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

export interface TableColumn {
  def: string;
  header: string;
  cell: (element: any) => string;
}

@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatPaginatorModule, MatSortModule, MatInputModule, MatFormFieldModule],
  template: `
    <div class="table-container">
      <div class="table-header-controls" *ngIf="showFilter">
        <mat-form-field appearance="outline" style="width: 100%; max-width: 300px;">
          <mat-label>Filter</mat-label>
          <input matInput (keyup)="applyFilter($event)" placeholder="Search..." #input>
        </mat-form-field>
      </div>

      <div style="overflow-x: auto; width: 100%;">
        <table mat-table [dataSource]="dataSource" matSort>
          <ng-container *ngFor="let column of columns" [matColumnDef]="column.def">
            <th mat-header-cell *matHeaderCellDef mat-sort-header> {{ column.header }} </th>
            <td mat-cell *matCellDef="let row"> {{ column.cell(row) }} </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;" class="table-row-hover"></tr>

          <tr class="mat-row" *matNoDataRow>
            <td class="mat-cell" style="padding: var(--space-xl); text-align: center;" [attr.colspan]="displayedColumns.length">
              No data matching the filter
            </td>
          </tr>
        </table>
      </div>

      <mat-paginator [pageSizeOptions]="pageSizeOptions" aria-label="Select page"></mat-paginator>
    </div>
  `,
  styles: [`
    table { width: 100%; }
    .mat-mdc-row .mat-mdc-cell {
      border-bottom: 1px solid transparent;
      border-top: 1px solid transparent;
    }
  `]
})
export class DataTableComponent<T> implements AfterViewInit, OnChanges {
  @Input() data: T[] = [];
  @Input() columns: TableColumn[] = [];
  @Input() displayedColumns: string[] = [];
  @Input() pageSizeOptions: number[] = [5, 10, 25, 100];
  @Input() showFilter: boolean = true;

  dataSource: MatTableDataSource<T>;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor() {
    this.dataSource = new MatTableDataSource(this.data);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data'] && changes['data'].currentValue) {
      this.dataSource.data = this.data;
    }
  }

  ngAfterViewInit() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }
}
