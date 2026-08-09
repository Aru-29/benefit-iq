import { Observable } from 'rxjs';

export interface LookupItem<T = any> {
  id: string;
  label: string;
  value: string;
  description?: string;
  metadata?: Record<string, any>;
  data?: T;
}

export interface GenericLookupResponse<T = any> {
  items: LookupItem<T>[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  next_cursor?: string;
}

export interface LookupAdapter<T = any> {
  fetch(search: string, page: number, pageSize: number): Observable<GenericLookupResponse<T>>;
}
