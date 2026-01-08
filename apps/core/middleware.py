from django.http import Http404
from apps.core.models import Tenant


class TenantMiddleware:
    """
    Middleware to identify and attach tenant to request based on URL pattern.
    URL format: /tenant/{tenant_slug}/...

    The tenant is extracted from the URL and attached to the request object
    as request.tenant and request.tenant_slug for use in views and services.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract tenant slug from URL: /tenant/{slug}/...
        path_parts = request.path.strip('/').split('/')

        tenant = None
        tenant_slug = None

        if len(path_parts) >= 2 and path_parts[0] == 'tenant':
            tenant_slug = path_parts[1]
            try:
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                raise Http404(f"Tenant '{tenant_slug}' not found or inactive")

        # Attach tenant to request for use in views
        request.tenant = tenant
        request.tenant_slug = tenant_slug

        response = self.get_response(request)
        return response
