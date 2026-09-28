// Static role → action map. Mirrors the @roles_required(...) decorators on
// the backend (backend/src/crm/view/*.py) — keep both in sync when adding an
// endpoint. The backend is the real gate; this only hides UI the current
// role could not use anyway.
export const ROLES = ['superuser', 'admin', 'operator']

export const PERMISSIONS = {
  'users.view': ['superuser', 'admin'],
  'users.create': ['superuser', 'admin'],
  'users.edit': ['superuser', 'admin'],
  'users.lock': ['superuser'],
  'users.resetPassword': ['superuser'],
  'users.delete': ['superuser'],
  'categories.view': ['superuser', 'admin', 'operator'],
  'categories.create': ['superuser', 'admin'],
  'categories.edit': ['superuser', 'admin'],
  'categories.delete': ['superuser', 'admin'],
  'slider.view': ['superuser', 'admin', 'operator'],
  'slider.create': ['superuser', 'admin'],
  'slider.edit': ['superuser', 'admin'],
  'slider.delete': ['superuser', 'admin'],
  'banners.view': ['superuser', 'admin', 'operator'],
  'banners.create': ['superuser', 'admin'],
  'banners.edit': ['superuser', 'admin'],
  'banners.delete': ['superuser', 'admin'],
  'products.view': ['superuser', 'admin', 'operator'],
  'products.create': ['superuser', 'admin'],
  'products.edit': ['superuser', 'admin'],
  'products.delete': ['superuser', 'admin'],
  // Single row: created once, then only edited — no delete.
  'company.view': ['superuser', 'admin', 'operator'],
  'company.create': ['superuser', 'admin'],
  'company.edit': ['superuser', 'admin'],
  // Messages come from the public website form; the console never creates them.
  'contact.view': ['superuser', 'admin', 'operator'],
  'contact.status': ['superuser', 'admin', 'operator'],
  'contact.delete': ['superuser', 'admin'],
  'media.upload': ['superuser', 'admin'],
}

export function hasPermission(role, permission) {
  return !!role && (PERMISSIONS[permission] || []).includes(role)
}
