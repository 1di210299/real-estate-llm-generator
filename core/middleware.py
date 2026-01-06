"""
Custom middleware for production security
"""
import re
from django.core.exceptions import DisallowedHost
from django.conf import settings


class HostValidationMiddleware:
    """
    Validates HTTP_HOST against allowed patterns.
    Allows internal/private IPs (10.x, 172.x, 192.168.x, 100.127.x)
    and configured domains from CORS_ALLOWED_ORIGINS.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get domains from CORS_ALLOWED_ORIGINS
        self.allowed_domains = []
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        for origin in cors_origins:
            # Extract domain from https://domain.com format
            domain = origin.replace('https://', '').replace('http://', '').split(':')[0]
            self.allowed_domains.append(domain)
        
        # Add .ondigitalocean.app wildcard
        self.allowed_domains.append('.ondigitalocean.app')
        self.allowed_domains.append('localhost')
        self.allowed_domains.append('127.0.0.1')
    
    def __call__(self, request):
        host = request.get_host().split(':')[0]
        
        # Allow internal/private IPs
        if re.match(r'^(10\.|172\.|192\.168\.|100\.127\.)', host):
            return self.get_response(request)
        
        # Check if host matches any allowed domain
        for domain in self.allowed_domains:
            if domain.startswith('.'):
                # Wildcard domain: .ondigitalocean.app matches anything.ondigitalocean.app
                if host.endswith(domain[1:]) or host == domain[1:]:
                    return self.get_response(request)
            elif host == domain:
                return self.get_response(request)
        
        # If we get here, host is not allowed
        raise DisallowedHost(f"Invalid HTTP_HOST header: '{request.get_host()}'")
