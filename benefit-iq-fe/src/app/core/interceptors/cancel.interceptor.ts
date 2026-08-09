import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, takeUntil } from 'rxjs';
import { HttpCancelService } from '../services/http-cancel.service';

export const cancelInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  const cancelService = inject(HttpCancelService);
  return next(req).pipe(
    takeUntil(cancelService.onCancelPendingRequests())
  );
};
