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
    
    # Direct routes - simple and clean
    path('auth/', include('apps.users.urls')),
    path('tenants/', include('apps.tenants.urls')),
    path('properties/', include('apps.properties.urls')),
    path('documents/', include('apps.documents.urls')),
    path('conversations/', include('apps.conversations.urls')),
    path('chat/', include('apps.chat.urls')),
    path('ingest/', include('apps.ingestion.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, serve static files from staticfiles directory
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
