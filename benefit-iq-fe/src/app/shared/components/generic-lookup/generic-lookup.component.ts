import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ElementRef, HostListener, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Subject, Observable, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError, takeUntil } from 'rxjs/operators';
import { LookupAdapter, LookupItem } from '../../models/lookup.model';

@Component({
  selector: 'app-generic-lookup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="lookup-container">
      <label *ngIf="label" class="lookup-label">{{ label }}</label>
      
      <div class="lookup-input-wrapper">
        <input
          type="text"
          class="lookup-input"
          [formControl]="searchControl"
          [placeholder]="placeholder"
          (focus)="onFocus()"
          (keydown)="onKeydown($event)"
        />
        
        <span *ngIf="isLoading()" class="lookup-spinner"></span>
        <button *ngIf="searchControl.value" type="button" class="lookup-clear" (click)="clear()">&times;</button>
      </div>

      <!-- Dropdown Results Panel -->
      <div *ngIf="isOpen()" class="lookup-dropdown" (scroll)="onScroll($event)">
        <div *ngIf="items().length === 0 && !isLoading()" class="lookup-empty">
          No results found.
        </div>

        <div
          *ngFor="let item of items(); let i = index"
          class="lookup-item"
          [class.selected]="isSelected(item)"
          [class.highlighted]="i === highlightedIndex()"
          (click)="selectItem(item)"
        >
          <div class="lookup-item-label">{{ item.label }}</div>
          <div *ngIf="item.description" class="lookup-item-desc">{{ item.description }}</div>
        </div>

        <div *ngIf="isLoading() && items().length > 0" class="lookup-loading-more">
          Loading more...
        </div>
      </div>
    </div>
  `,
  styles: [`
    .lookup-container {
      position: relative;
      width: 100%;
    }
    .lookup-label {
      display: block;
      font-size: var(--font-xs);
      font-weight: 600;
      margin-bottom: var(--space-xs);
      color: var(--color-text-secondary);
    }
    .lookup-input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }
    .lookup-input {
      width: 100%;
      padding: 0.625rem 2rem 0.625rem 0.875rem;
      font-size: var(--font-sm);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      background: var(--color-surface);
      color: var(--color-text);
      outline: none;
      transition: border-color var(--transition-fast);
    }
    .lookup-input:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    .lookup-spinner {
      position: absolute;
      right: 2rem;
      width: 1rem;
      height: 1rem;
      border: 2px solid var(--color-border);
      border-top-color: var(--color-primary);
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
    .lookup-clear {
      position: absolute;
      right: 0.5rem;
      background: none;
      border: none;
      font-size: 1.2rem;
      cursor: pointer;
      color: var(--color-text-tertiary);
    }
    .lookup-dropdown {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      z-index: 1000;
      max-height: 240px;
      overflow-y: auto;
      margin-top: 4px;
      background: var(--color-surface-elevated);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
    }
    .lookup-item {
      padding: 0.625rem 0.875rem;
      cursor: pointer;
      border-bottom: 1px solid var(--color-border-subtle);
    }
    .lookup-item:hover, .lookup-item.highlighted {
      background: var(--color-surface-hover);
    }
    .lookup-item.selected {
      background: var(--color-primary-light);
      color: var(--color-primary);
    }
    .lookup-item-label {
      font-weight: 500;
      font-size: var(--font-sm);
    }
    .lookup-item-desc {
      font-size: var(--font-xs);
      color: var(--color-text-secondary);
    }
    .lookup-empty, .lookup-loading-more {
      padding: 0.75rem;
      text-align: center;
      font-size: var(--font-xs);
      color: var(--color-text-secondary);
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class GenericLookupComponent<T = any> implements OnInit, OnDestroy {
  private readonly elementRef = inject(ElementRef);
  private readonly destroy$ = new Subject<void>();

  @Input() adapter!: LookupAdapter<T>;
  @Input() label: string = '';
  @Input() placeholder: string = 'Search and select...';
  @Input() multiSelect: boolean = false;
  @Input() pageSize: number = 20;

  @Output() selectionChange = new EventEmitter<LookupItem<T> | LookupItem<T>[]>();

  searchControl = new FormControl('');
  items = signal<LookupItem<T>[]>([]);
  selectedItems = signal<LookupItem<T>[]>([]);
  isOpen = signal(false);
  isLoading = signal(false);
  hasMore = signal(true);
  currentPage = signal(1);
  highlightedIndex = signal(-1);

  ngOnInit() {
    this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((term) => {
        this.currentPage.set(1);
        this.isLoading.set(true);
        if (!this.adapter) return of({ items: [], total: 0, page: 1, page_size: 20, has_more: false });
        return this.adapter.fetch(term || '', 1, this.pageSize).pipe(
          catchError(() => of({ items: [], total: 0, page: 1, page_size: 20, has_more: false }))
        );
      }),
      takeUntil(this.destroy$)
    ).subscribe((res) => {
      this.isLoading.set(false);
      this.items.set(res.items || []);
      this.hasMore.set(res.has_more ?? false);
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onFocus() {
    this.isOpen.set(true);
    if (this.items().length === 0) {
      this.loadPage(1);
    }
  }

  loadPage(page: number) {
    if (!this.adapter || this.isLoading()) return;
    this.isLoading.set(true);
    this.adapter.fetch(this.searchControl.value || '', page, this.pageSize).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        if (page === 1) {
          this.items.set(res.items || []);
        } else {
          this.items.set([...this.items(), ...(res.items || [])]);
        }
        this.hasMore.set(res.has_more ?? false);
      },
      error: () => this.isLoading.set(false)
    });
  }

  onScroll(event: Event) {
    const target = event.target as HTMLElement;
    if (target.scrollTop + target.clientHeight >= target.scrollHeight - 20 && this.hasMore() && !this.isLoading()) {
      const nextPage = this.currentPage() + 1;
      this.currentPage.set(nextPage);
      this.loadPage(nextPage);
    }
  }

  selectItem(item: LookupItem<T>) {
    if (this.multiSelect) {
      const current = this.selectedItems();
      const idx = current.findIndex(i => i.id === item.id);
      if (idx >= 0) {
        this.selectedItems.set(current.filter(i => i.id !== item.id));
      } else {
        this.selectedItems.set([...current, item]);
      }
      this.selectionChange.emit(this.selectedItems());
    } else {
      this.selectedItems.set([item]);
      this.searchControl.setValue(item.label, { emitEvent: false });
      this.isOpen.set(false);
      this.selectionChange.emit(item);
    }
  }

  isSelected(item: LookupItem<T>): boolean {
    return this.selectedItems().some(i => i.id === item.id);
  }

  clear() {
    this.searchControl.setValue('');
    this.selectedItems.set([]);
    this.selectionChange.emit(this.multiSelect ? [] : undefined);
    this.loadPage(1);
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.isOpen.set(true);
      this.highlightedIndex.set(Math.min(this.highlightedIndex() + 1, this.items().length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.highlightedIndex.set(Math.max(this.highlightedIndex() - 1, 0));
    } else if (event.key === 'Enter' && this.highlightedIndex() >= 0) {
      event.preventDefault();
      const item = this.items()[this.highlightedIndex()];
      if (item) this.selectItem(item);
    } else if (event.key === 'Escape') {
      this.isOpen.set(false);
    }
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }
}
