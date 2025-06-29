# Middleware removed as per user request. No API key enforcement.

import re
from django.middleware.csrf import CsrfViewMiddleware

class CSRFExemptMiddleware:
    """
    Custom middleware to disable CSRF protection for specific API endpoints
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # API paths to be exempted from CSRF (using regex)
        self.csrf_exempt_urls = [
            r'^/api/users/login/',
            r'^/api/users/auth/login/',
            r'^/checks/auth/login/',
        ]

    def __call__(self, request):
        # Skip CSRF checks for specific endpoints
        request._dont_enforce_csrf_checks = any(
            re.match(url, request.path) for url in self.csrf_exempt_urls
        )
        return self.get_response(request)
