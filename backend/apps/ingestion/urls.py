from django.urls import path
from .views import (
    IngestURLView, 
    IngestTextView, 
    IngestBatchView, 
    SavePropertyView, 
    GenerateEmbeddingsView,
    SupportedWebsitesView,
    ContentTypesView,
    IngestionStatsView,
    ProcessGoogleSheetView,
    CreateGoogleSheetTemplateView,
    CancelBatchView,
    BatchExportToSheetsView,
    BatchExportToDatabaseView
)

urlpatterns = [
    path('supported-websites/', SupportedWebsitesView.as_view(), name='supported-websites'),
    path('content-types/', ContentTypesView.as_view(), name='content-types'),
    path('stats/', IngestionStatsView.as_view(), name='ingestion-stats'),
    path('url/', IngestURLView.as_view(), name='ingest-url'),
    path('text/', IngestTextView.as_view(), name='ingest-text'),
    path('batch/', IngestBatchView.as_view(), name='ingest-batch'),
    path('cancel-batch/', CancelBatchView.as_view(), name='cancel-batch'),
    path('save/', SavePropertyView.as_view(), name='save-property'),
    path('generate-embeddings/', GenerateEmbeddingsView.as_view(), name='generate-embeddings'),
    path('google-sheet/', ProcessGoogleSheetView.as_view(), name='process-google-sheet'),
    path('create-sheet-template/', CreateGoogleSheetTemplateView.as_view(), name='create-sheet-template'),
    path('batch-export/sheets/', BatchExportToSheetsView.as_view(), name='batch-export-sheets'),
    path('batch-export/database/', BatchExportToDatabaseView.as_view(), name='batch-export-database'),
]
