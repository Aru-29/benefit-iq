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
  templateUrl: './generic-lookup.component.html',
  styleUrl: './generic-lookup.component.css'
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
