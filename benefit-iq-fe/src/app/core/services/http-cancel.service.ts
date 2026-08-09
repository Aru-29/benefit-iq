import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpCancelService {
  private cancelPendingRequests$ = new Subject<void>();

  /**
   * Cancels all pending HTTP requests.
   * Typically called on NavigationStart.
   */
  public cancelPendingRequests() {
    this.cancelPendingRequests$.next();
  }

  public onCancelPendingRequests() {
    return this.cancelPendingRequests$.asObservable();
  }
}
