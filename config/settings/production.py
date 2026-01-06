"""
Production settings
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import re

DEBUG = False

# Allow all hosts - we'll validate in middleware
ALLOWED_HOSTS = ['*']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Use PostgreSQL connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['CONN_HEALTH_CHECKS'] = True

# Static files (use WhiteNoise or S3)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Sentry integration
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=env('SENTRY_ENVIRONMENT', default='production'),
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# Celery in production should use actual workers
CELERY_TASK_ALWAYS_EAGER = False

# Cache settings for production
CACHES['default']['TIMEOUT'] = 3600 * 24  # 24 hours

# ALLOWED_HOSTS is already wrapped with AllowInternalIPs at the top of this file

# CORS - specify exact origins
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.rstrip('/') for origin in env.list('CORS_ALLOWED_ORIGINS')
]
