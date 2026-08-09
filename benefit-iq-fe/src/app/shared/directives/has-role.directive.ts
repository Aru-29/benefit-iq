import { Directive, Input, TemplateRef, ViewContainerRef, inject, effect } from '@angular/core';
import { AuthStore } from '../../core/state/auth.store';

@Directive({
  selector: '[appHasRole]',
  standalone: true
})
export class HasRoleDirective {
  private readonly templateRef = inject(TemplateRef);
  private readonly viewContainer = inject(ViewContainerRef);
  private readonly authStore = inject(AuthStore);

  private expectedRoles: string[] = [];
  private hasView = false;

  @Input() set appHasRole(roles: string[] | string) {
    this.expectedRoles = Array.isArray(roles) ? roles : [roles];
    this.updateView();
  }

  constructor() {
    // Reactively update when role changes
    effect(() => {
      // Accessing authStore.role() inside effect makes it reactive
      this.authStore.role();
      this.updateView();
    });
  }

  private updateView() {
    const currentRole = this.authStore.role();
    const isAuthorized = currentRole && this.expectedRoles.includes(currentRole);

    if (isAuthorized && !this.hasView) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.hasView = true;
    } else if (!isAuthorized && this.hasView) {
      this.viewContainer.clear();
      this.hasView = false;
    }
  }
}
