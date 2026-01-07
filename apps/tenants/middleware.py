"""
Tenant middleware for multi-tenancy support.
"""

from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied
from .models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to set current tenant from request.
    Expects tenant_id in JWT token or header.
    """
    
    def process_request(self, request):
        """Set current tenant on request."""
        
        print(f"🔍 TenantMiddleware - Path: {request.path}")
        
        # Skip tenant check for admin, auth, health, static, ingest, and properties endpoints
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/api/v1/auth/') or
            request.path.startswith('/api/v1/ingest/') or
            request.path.startswith('/api/v1/properties/') or
            request.path.startswith('/api/health/') or
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            print(f"✅ TenantMiddleware - SKIPPING tenant check for: {request.path}")
            return
        
        print(f"⚠️ TenantMiddleware - Checking tenant for: {request.path}")
        
        tenant_id = None
        
        # Try to get tenant from Authorization header (JWT)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'tenant'):
                tenant_id = request.user.tenant_id
        
        # Try to get tenant from X-Tenant-ID header
        if not tenant_id:
            tenant_id = request.headers.get('X-Tenant-ID')
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                raise PermissionDenied("Invalid tenant")
        else:
            request.tenant = None
