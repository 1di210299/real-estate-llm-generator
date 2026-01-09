from django.urls import path
from .views import (
    IngestURLView, 
    IngestTextView, 
    IngestBatchView, 
    SavePropertyView, 
    GenerateEmbeddingsView,
    SupportedWebsitesView
)

urlpatterns = [
    path('supported-websites/', SupportedWebsitesView.as_view(), name='supported-websites'),
    path('url/', IngestURLView.as_view(), name='ingest-url'),
    path('text/', IngestTextView.as_view(), name='ingest-text'),
    path('batch/', IngestBatchView.as_view(), name='ingest-batch'),
    path('save/', SavePropertyView.as_view(), name='save-property'),
    path('generate-embeddings/', GenerateEmbeddingsView.as_view(), name='generate-embeddings'),
]
