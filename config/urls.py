"""
URL configuration for Real Estate LLM project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.utils.health import health_check
from apps.ingestion.views import IngestURLView, IngestTextView, IngestBatchView, SavePropertyView
from apps.properties.urls import router as properties_router


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    
    # Rutas simples sin /v1/ prefix (lo más simple)
    path('auth/', include('apps.users.urls')),
    path('tenants/', include('apps.tenants.urls')),
    path('properties/', include('apps.properties.urls')),
    path('documents/', include('apps.documents.urls')),
    path('conversations/', include('apps.conversations.urls')),
    path('chat/', include('apps.chat.urls')),
    path('ingest/', include('apps.ingestion.urls')),
    
    # Rutas adicionales sin prefijo para ingress path stripping
    # Cuando ingress match /ingest, forward como /url/, /text/, etc
    path('url/', IngestURLView.as_view(), name='ingest-url-direct'),
    path('text/', IngestTextView.as_view(), name='ingest-text-direct'),
    path('batch/', IngestBatchView.as_view(), name='ingest-batch-direct'),
    path('save/', SavePropertyView.as_view(), name='save-property-direct'),
    
    # Rutas directas para properties (después de path stripping /properties → /)
    # Cuando ingress match /properties, forward como /, /{id}/, etc
    path('', include(properties_router.urls)),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, serve static files from staticfiles directory
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
