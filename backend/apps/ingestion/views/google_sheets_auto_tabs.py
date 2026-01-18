"""
Google Sheets integration with automatic tab creation.
Reads URLs from a Google Sheet and creates classified tabs automatically.
"""

import logging
import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.tenants.models import Tenant
from apps.properties.models import Property

from core.scraping.scraper import scrape_url
from core.llm.extraction import extract_content_data
from core.llm.content_detection import detect_content_type
from core.llm.page_type_detection import detect_page_type

from ..google_sheets import GoogleSheetsService
from ..email_notifications import send_batch_completion_email, send_error_notification

logger = logging.getLogger(__name__)


class ProcessGoogleSheetView(APIView):
    """
    Endpoint to process URLs from a Google Sheet with automatic classification and tab creation.
    
    POST /ingest/google-sheet/
    {
        "spreadsheet_id": "1abc...",
        "notify_email": "assistant@example.com"
    }
    
    This endpoint:
    1. Reads URLs from the provided Google Sheet
    2. Processes each URL (scraping + extraction + classification)
    3. Creates Property objects in database
    4. Automatically creates tabs in the sheet based on content_type + page_type
    5. Exports results to appropriate tabs (e.g., "real_estate_specific", "tour_general")
    """
    
    permission_classes = [AllowAny]
    
    def _get_column_schema(self, content_type: str, page_type: str) -> dict:
        """
        Define column schemas for different content types and page types.
        Returns: {'headers': [...], 'field_keys': [...]}
        """
        
        # TOUR - SPECIFIC PAGE
        if content_type == 'tour' and page_type == 'specific':
            return {
                'headers': [
                    'Nombre del Tour', 'Tipo de Tour', 'Precio (USD)', 'Precio Adults', 'Precio Children',
                    'Precio Students', 'Precio Nationals', 'Precio Groups', 'Precio Range',
                    'Duración (horas)', 'Nivel de Dificultad', 'Ubicación', 'Descripción',
                    'Qué Incluye', 'Qué Excluye', 'Máx. Participantes', 'Idiomas Disponibles',
                    'Pickup Incluido', 'Edad Mínima', 'Política de Cancelación',
                    'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'tour_name', 'tour_type', 'price_usd', 'price_details.adults', 'price_details.children',
                    'price_details.students', 'price_details.nationals', 'price_details.groups', 'price_details.range',
                    'duration_hours', 'difficulty_level', 'location', 'description',
                    'included_items', 'excluded_items', 'max_participants', 'languages_available',
                    'pickup_included', 'minimum_age', 'cancellation_policy',
                    'extraction_confidence', 'source_url'
                ]
            }
        
        # TOUR - GENERAL PAGE (GUIDE)
        elif content_type == 'tour' and page_type == 'general':
            return {
                'headers': [
                    'Destino', 'Ubicación', 'Resumen General', 'Tipos de Tours Disponibles',
                    'Regiones', 'Precio Mín (USD)', 'Precio Máx (USD)', 'Precio Típico (USD)',
                    'Mejor Temporada', 'Mejor Hora del Día', 'Rango de Duración',
                    'Consejos', 'Qué Llevar', 'Tours Destacados', 'Total Tours Mencionados',
                    'Consejos de Reserva', 'Actividades por Temporada', 'FAQs',
                    'Apto para Familias', 'Info de Accesibilidad', 'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'destination', 'location', 'overview', 'tour_types_available',
                    'regions', 'price_range.min_usd', 'price_range.max_usd', 'price_range.typical_usd',
                    'best_season', 'best_time_of_day', 'duration_range',
                    'tips', 'things_to_bring', 'featured_tours', 'total_tours_mentioned',
                    'booking_tips', 'seasonal_activities', 'faqs',
                    'family_friendly', 'accessibility_info', 'extraction_confidence', 'source_url'
                ]
            }
        
        # REAL ESTATE - SPECIFIC PAGE
        elif content_type == 'real_estate' and page_type == 'specific':
            return {
                'headers': [
                    'Título', 'Precio (USD)', 'Ubicación', 'Ciudad', 'Provincia', 'País',
                    'Tipo de Propiedad', 'Tipo de Listado', 'Habitaciones', 'Baños',
                    'Área (m²)', 'Tamaño Lote (m²)', 'Espacios de Estacionamiento',
                    'Descripción', 'Amenidades', 'Fecha de Listado', 'Estado',
                    'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'property_name', 'price_usd', 'location', 'city', 'province', 'country',
                    'property_type', 'listing_type', 'bedrooms', 'bathrooms',
                    'square_meters', 'lot_size_m2', 'parking_spaces',
                    'description', 'amenities', 'date_listed', 'listing_status',
                    'extraction_confidence', 'source_url'
                ]
            }
        
        # REAL ESTATE - GENERAL PAGE
        elif content_type == 'real_estate' and page_type == 'general':
            return {
                'headers': [
                    'Destino', 'Ubicación', 'Resumen General', 'Tipos de Propiedades',
                    'Precio Mín (USD)', 'Precio Máx (USD)', 'Propiedades Destacadas',
                    'Total Propiedades', 'Regiones', 'Consejos', 'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'destination', 'location', 'overview', 'property_types',
                    'price_range.min_usd', 'price_range.max_usd', 'featured_items',
                    'total_items_mentioned', 'regions', 'tips', 'extraction_confidence', 'source_url'
                ]
            }
        
        # RESTAURANT - SPECIFIC PAGE
        elif content_type == 'restaurant' and page_type == 'specific':
            return {
                'headers': [
                    'Nombre', 'Tipo de Cocina', 'Rango de Precio', 'Precio Promedio (USD)',
                    'Ubicación', 'Horario', 'Ambiente', 'Reservas Requeridas',
                    'Platillos Destacados', 'Opciones Dietéticas', 'Código de Vestimenta',
                    'Teléfono', 'Descripción', 'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'restaurant_name', 'cuisine_type', 'price_range', 'average_price_usd',
                    'location', 'hours', 'ambiance', 'reservations_required',
                    'signature_dishes', 'dietary_options', 'dress_code',
                    'phone', 'description', 'extraction_confidence', 'source_url'
                ]
            }
        
        # RESTAURANT - GENERAL PAGE
        elif content_type == 'restaurant' and page_type == 'general':
            return {
                'headers': [
                    'Destino', 'Ubicación', 'Resumen General', 'Tipos de Cocina',
                    'Precio Mín (USD)', 'Precio Máx (USD)', 'Restaurantes Destacados',
                    'Total Restaurantes', 'Consejos', 'Confianza Extracción', 'URL'
                ],
                'field_keys': [
                    'destination', 'location', 'overview', 'cuisine_types',
                    'price_range.min_usd', 'price_range.max_usd', 'featured_items',
                    'total_items_mentioned', 'tips', 'extraction_confidence', 'source_url'
                ]
            }
        
        # DEFAULT - Try to extract common fields
        else:
            return {
                'headers': ['Título', 'Ubicación', 'Precio (USD)', 'Descripción', 'URL'],
                'field_keys': ['title', 'location', 'price_usd', 'description', 'url']
            }
    
    def _extract_field_value(self, obj, key_path: str) -> str:
        """
        Extract value from Property object or dict using dot notation.
        Handles Property model fields, JSONField nested data, arrays, and None values.
        """
        keys = key_path.split('.')
        value = obj
        
        # Start by getting the base attribute from Property model if it's a model instance
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Property':
            # Get first key as model attribute
            first_key = keys[0]
            
            # First try direct model field
            if hasattr(obj, first_key):
                value = getattr(obj, first_key)
                keys = keys[1:]  # Remove first key since we already got it
            # If not found in model, try in price_details JSONField
            elif hasattr(obj, 'price_details') and isinstance(obj.price_details, dict):
                if first_key in obj.price_details:
                    value = obj.price_details[first_key]
                    keys = keys[1:]  # Remove first key
                else:
                    return 'N/A'
            else:
                return 'N/A'
        
        # Now traverse remaining keys for nested dict/JSON data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return 'N/A'
        
        # Format value
        if value is None:
            return 'N/A'
        elif isinstance(value, list):
            if len(value) == 0:
                return 'N/A'
            # Format arrays nicely
            if all(isinstance(item, str) for item in value):
                return ', '.join(value)
            elif all(isinstance(item, dict) for item in value):
                # Special formatting for different types of objects
                formatted_items = []
                for item in value:
                    # FAQs: "Q: ... A: ..."
                    if 'question' in item and 'answer' in item:
                        formatted_items.append(f"Q: {item['question']} | A: {item['answer']}")
                    # Seasonal activities: "Season: ... Activities: ..."
                    elif 'season' in item and 'recommended_activities' in item:
                        activities = ', '.join(item.get('recommended_activities', []))
                        formatted_items.append(f"{item['season']}: {activities}")
                    # Featured tours/items with name
                    elif 'name' in item:
                        formatted_items.append(item['name'])
                    elif 'tour_name' in item:
                        formatted_items.append(item['tour_name'])
                    # Price details
                    elif 'adults' in item or 'children' in item:
                        parts = []
                        if 'adults' in item:
                            parts.append(f"Adultos: ${item['adults']}")
                        if 'children' in item:
                            parts.append(f"Niños: ${item['children']}")
                        if 'students' in item:
                            parts.append(f"Estudiantes: ${item['students']}")
                        formatted_items.append(' | '.join(parts))
                    # Default: convert to string
                    else:
                        formatted_items.append(str(item))
                
                return ' || '.join(formatted_items)
            else:
                return ', '.join(str(v) for v in value)
        elif isinstance(value, bool):
            return 'Sí' if value else 'No'
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)
    
    def _get_sheet_name(self, page_type: str) -> str:
        """Get friendly sheet name for page type."""
        names = {
            'specific': 'Específicos',
            'general': 'Generales'
        }
        return names.get(page_type, page_type.capitalize())
    
    def _write_property_to_sheet_immediately(self, sheets_service, spreadsheet_id, property_obj, content_type, page_type):
        """
        Write a single property to Google Sheet immediately after processing.
        Creates sheet tab if needed and appends a single row.
        """
        try:
            # Get schema for this content/page type combination
            schema = self._get_column_schema(content_type, page_type)
            headers = schema['headers']
            field_keys = schema['field_keys']
            
            # Create sheet name: real_estate_Específicos, tour_Generales, etc.
            sheet_name = f"{content_type}_{self._get_sheet_name(page_type)}"
            
            # Check if sheet already exists
            try:
                sheets_service.get_sheet_metadata(spreadsheet_id, sheet_name)
                sheet_exists = True
            except:
                sheet_exists = False
            
            # Create sheet if it doesn't exist
            if not sheet_exists:
                logger.info(f"📋 Creating new sheet: {sheet_name}")
                sheets_service.create_sheet(spreadsheet_id, sheet_name)
                
                # Write headers
                header_row = [headers]
                sheets_service.append_rows(
                    spreadsheet_id,
                    f"{sheet_name}!A1",
                    header_row,
                    sheet_name=sheet_name
                )
                logger.info(f"   Headers written to {sheet_name}")
            
            # Format property data row
            data_row = []
            for key in field_keys:
                value = self._extract_field_value(property_obj, key)
                data_row.append(value)
            
            # Append single row to sheet
            sheets_service.append_rows(
                spreadsheet_id,
                f"{sheet_name}!A:Z",
                [data_row],
                sheet_name=sheet_name
            )
            
            logger.info(f"✅ Property written to {sheet_name}: {property_obj.property_name or 'N/A'}")
            return True, sheet_name
            
        except Exception as e:
            logger.error(f"❌ Error writing property to sheet: {e}")
            return False, None
    
    def post(self, request):
        """Process properties from Google Sheet."""
        import uuid
        
        spreadsheet_id = request.data.get('spreadsheet_id')
        notify_email = request.data.get('notify_email')
        run_async = request.data.get('async', True)
        create_results_sheet = request.data.get('create_results_sheet', False)
        results_sheet_id = request.data.get('results_sheet_id')
        
        # Generate unique task ID for WebSocket tracking
        task_id = str(uuid.uuid4())
        
        if not spreadsheet_id:
            return Response(
                {'error': 'spreadsheet_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not notify_email:
            return Response(
                {'error': 'notify_email is required for notifications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Define processing callback with progress updates
        def process_url(url: str, index: int = 0, total: int = 1):
            """Process a single URL and return success status."""
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            
            try:
                # Send progress update: Starting scraping
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'progress_{task_id}',
                        {
                            'type': 'progress_update',
                            'progress': int((index / total) * 100),
                            'status': f'scraping',
                            'message': f'Procesando {index + 1} de {total}',
                            'stage': 'scraping',
                            'substage': f'Descargando: {url[:60]}...',
                            'step': index + 1,
                            'total_steps': total,
                            'url': url
                        }
                    )
                
                scraped_data = scrape_url(url)
                
                if not scraped_data.get('success'):
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f'progress_{task_id}',
                            {
                                'type': 'task_error',
                                'message': f'Failed to scrape: {url}',
                                'error': 'Scraping failed'
                            }
                        )
                    return False, {'error': 'Failed to scrape URL'}
                
                # Send progress update: Extracting data
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'progress_{task_id}',
                        {
                            'type': 'progress_update',
                            'progress': int(((index + 0.33) / total) * 100),
                            'status': 'extracting',
                            'message': f'Extrayendo datos {index + 1} de {total}',
                            'stage': 'extracting',
                            'substage': 'Analizando contenido con IA...',
                            'step': index + 1,
                            'total_steps': total,
                            'url': url
                        }
                    )
                
                html_content = scraped_data.get('html', scraped_data.get('text', ''))
                
                # Detect content type (real_estate, tour, restaurant, etc.)
                content_detection = detect_content_type(
                    url=url,
                    html=html_content,
                    user_override=None,
                    use_llm_fallback=True  # Use LLM for accurate detection
                )
                detected_content_type = content_detection['content_type']
                content_type_confidence = content_detection['confidence']
                logger.info(f"✅ Content type: {detected_content_type} (confidence: {content_type_confidence:.2%})")
                
                # Detect page type (specific vs general)
                page_type_detection = detect_page_type(
                    url=url,
                    html=html_content,
                    content_type=detected_content_type
                )
                detected_page_type = page_type_detection['page_type']
                page_type_confidence = page_type_detection['confidence']
                logger.info(f"✅ Page type: {detected_page_type} (confidence: {page_type_confidence:.2%})")
                
                # Extract data using detected content_type and page_type
                extracted_data = extract_content_data(
                    html_content, 
                    content_type=detected_content_type,
                    page_type=detected_page_type,
                    url=url
                )
                
                # Store ALL extracted data in price_details for later export
                # Convert Decimal objects to float and clean invalid Unicode for JSON serialization
                def clean_for_json(obj):
                    """Recursively convert Decimals and remove invalid Unicode characters for JSON/PostgreSQL"""
                    from decimal import Decimal
                    import re
                    
                    if isinstance(obj, Decimal):
                        return float(obj)
                    elif isinstance(obj, str):
                        # Remove control characters and invalid Unicode sequences
                        # Keep only printable characters and common whitespace
                        return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', obj)
                    elif isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    return obj
                
                all_extracted_data = clean_for_json(dict(extracted_data))  # Make a copy and clean data
                
                # Set tenant
                if request.user.is_authenticated:
                    extracted_data['tenant'] = request.user.tenant
                else:
                    extracted_data['tenant'] = Tenant.objects.first()
                
                extracted_data['user_roles'] = ['buyer', 'staff', 'admin']
                
                # Store ALL extracted data in price_details JSONField for export
                extracted_data['price_details'] = all_extracted_data
                
                # Clean metadata
                metadata_fields = ['tokens_used', 'raw_html', 'confidence_reasoning', 
                                 'extracted_at', 'field_confidence']
                for field in metadata_fields:
                    extracted_data.pop(field, None)
                    all_extracted_data.pop(field, None)
                
                evidence_fields = [key for key in extracted_data.keys() if key.endswith('_evidence')]
                for field in evidence_fields:
                    extracted_data.pop(field, None)
                
                evidence_fields = [key for key in all_extracted_data.keys() if key.endswith('_evidence')]
                for field in evidence_fields:
                    all_extracted_data.pop(field, None)
                
                # Send progress update: Saving to database
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'progress_{task_id}',
                        {
                            'type': 'progress_update',
                            'progress': int(((index + 0.66) / total) * 100),
                            'status': 'saving',
                            'message': f'Guardando {index + 1} de {total}',
                            'stage': 'saving',
                            'substage': f'Tipo detectado: {detected_content_type} | Página: {detected_page_type}',
                            'step': index + 1,
                            'total_steps': total,
                            'url': url
                        }
                    )
                
                # Create or update property
                tenant = extracted_data.get('tenant')
                source_url = extracted_data.get('source_url')
                
                # Filter only valid Property model fields
                property_model_fields = {
                    'tenant', 'property_name', 'price_usd', 'price_details', 'bedrooms', 'bathrooms',
                    'property_type', 'status', 'location', 'latitude', 'longitude', 'description',
                    'square_meters', 'lot_size_m2', 'hoa_fee_monthly', 'property_tax_annual',
                    'amenities', 'year_built', 'parking_spaces', 'user_roles', 'source_website',
                    'source_url', 'listing_id', 'internal_property_id', 'listing_status',
                    'date_listed', 'raw_html', 'extraction_confidence', 'content_type',
                    'page_type', 'field_confidence', 'extracted_at', 'last_verified',
                    'verified_by_id', 'is_active', 'embedding', 'content_for_search'
                }
                
                # Prepare data for Property model (only valid fields)
                property_data = {
                    key: value for key, value in extracted_data.items()
                    if key in property_model_fields
                }
                
                # Ensure price_details contains ALL extracted data
                property_data['price_details'] = all_extracted_data
                
                # Try to find existing property
                existing_property = Property.objects.filter(
                    tenant=tenant,
                    source_url=source_url
                ).first()
                
                if existing_property:
                    # Update existing property
                    logger.info(f"Property already exists (ID: {existing_property.id}), updating...")
                    for key, value in property_data.items():
                        if key not in ['id', 'tenant', 'created_at']:
                            setattr(existing_property, key, value)
                    existing_property.save()
                    property_obj = existing_property
                else:
                    # Create new property
                    property_obj = Property.objects.create(**property_data)
                
                # Send progress update: Complete for this property
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'progress_{task_id}',
                        {
                            'type': 'progress_update',
                            'progress': int(((index + 1) / total) * 100),
                            'status': 'completed',
                            'message': f'✅ Completado {index + 1} de {total}',
                            'stage': 'completed',
                            'substage': f'Guardado: {extracted_data.get("property_type", "N/A")} en {extracted_data.get("location", "N/A")}',
                            'step': index + 1,
                            'total_steps': total,
                            'url': url
                        }
                    )
                
                return True, {
                    'property_id': str(property_obj.id),
                    'title': extracted_data.get('title', ''),
                    'price_usd': extracted_data.get('price_usd'),
                    'bedrooms': extracted_data.get('bedrooms'),
                    'bathrooms': extracted_data.get('bathrooms'),
                    'square_meters': extracted_data.get('square_meters'),
                    'location': extracted_data.get('location'),
                    'property_type': extracted_data.get('property_type', '')
                }
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'progress_{task_id}',
                        {
                            'type': 'task_error',
                            'message': f'Error processing {url}',
                            'error': str(e)
                        }
                    )
                return False, {'error': str(e)}
        
        if run_async:
            # Process asynchronously
            from apps.ingestion.tasks import process_google_sheet_task
            
            task = process_google_sheet_task.delay(
                spreadsheet_id=spreadsheet_id,
                notify_email=notify_email,
                task_id=task_id,
                create_results_sheet=create_results_sheet,
                results_sheet_id=results_sheet_id
            )
            
            response_data = {
                'status': 'queued',
                'message': 'Google Sheet processing queued',
                'task_id': task_id,
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit'
            }
            
            if create_results_sheet:
                response_data['message'] += ' - Se creará un Google Sheet con los resultados'
            
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        
        else:
            # Process synchronously with classification and auto-tabs
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                
                channel_layer = get_channel_layer()
                
                # Read URLs from the sheet
                sheets_service = GoogleSheetsService()
                pending_rows = sheets_service.read_pending_rows(spreadsheet_id)
                
                if not pending_rows:
                    return Response({
                        'status': 'completed',
                        'total': 0,
                        'processed': 0,
                        'failed': 0,
                        'message': 'No pending URLs to process',
                        'tabs': []
                    }, status=status.HTTP_200_OK)
                
                # Process all URLs and classify them
                classified_results = {}  # {content_type_page_type: [objects]}
                processed_count = 0
                failed_count = 0
                total_urls = len(pending_rows)
                
                for index, row in enumerate(pending_rows):
                    try:
                        url = row['url']
                        logger.info(f"Processing {index + 1}/{total_urls}: {url}")
                        
                        # Process URL
                        success, result = process_url(url, index, total_urls)
                        
                        if success:
                            # Get the Property object to extract classification
                            property_id = result.get('property_id')
                            logger.info(f"✅ Success! Property ID: {property_id}")
                            
                            if property_id:
                                try:
                                    property_obj = Property.objects.get(id=property_id)
                                    content_type = property_obj.content_type or 'unknown'
                                    page_type = property_obj.page_type or 'general'
                                    
                                    logger.info(f"📊 Classification - content_type: '{content_type}', page_type: '{page_type}'")
                                    
                                    # Create tab name: tour_general, real_estate_specific, etc.
                                    tab_key = f"{content_type}_{page_type}"
                                    
                                    logger.info(f"🏷️  Tab key created: '{tab_key}'")
                                    
                                    if tab_key not in classified_results:
                                        classified_results[tab_key] = []
                                        logger.info(f"📁 Created new classification group: '{tab_key}'")
                                    
                                    # Add property to its classification group
                                    classified_results[tab_key].append(property_obj)
                                    logger.info(f"➕ Added property to '{tab_key}' group (total: {len(classified_results[tab_key])})")
                                    
                                    # 🔥 NEW: Write property to Google Sheet IMMEDIATELY
                                    sheets_service = GoogleSheetsService()
                                    write_success, sheet_name = self._write_property_to_sheet_immediately(
                                        sheets_service,
                                        spreadsheet_id,
                                        property_obj,
                                        content_type,
                                        page_type
                                    )
                                    
                                    if write_success:
                                        logger.info(f"📝 Property written immediately to sheet: {sheet_name}")
                                        # Send progress update with sheet name
                                        if channel_layer:
                                            async_to_sync(channel_layer.group_send)(
                                                f'progress_{task_id}',
                                                {
                                                    'type': 'progress_update',
                                                    'progress': int(((index + 1) / total_urls) * 100),
                                                    'status': 'completed',
                                                    'message': f'✅ Guardado {index + 1} de {total_urls}',
                                                    'stage': 'completed',
                                                    'substage': f'Escrito en pestaña: {sheet_name}',
                                                    'step': index + 1,
                                                    'total_steps': total_urls,
                                                    'url': url
                                                }
                                            )
                                    
                                    # DO NOT update original sheet - keep URLs page intact
                                    
                                    processed_count += 1
                                    
                                    # DO NOT update original sheet - keep URLs page intact
                                    
                                    processed_count += 1
                                    
                                except Property.DoesNotExist:
                                    logger.error(f"Property {property_id} not found after creation")
                                    failed_count += 1
                            else:
                                failed_count += 1
                        else:
                            # DO NOT update sheet with error - keep URLs page intact
                            failed_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing row {row['row_index']}: {e}")
                        # DO NOT update sheet with error - keep URLs page intact
                        failed_count += 1
                
                # Now export each classification group to its own tab
                tabs_created = []
                
                logger.info(f"\n{'='*80}")
                logger.info(f"📤 EXPORTING CLASSIFIED RESULTS TO TABS")
                logger.info(f"{'='*80}")
                logger.info(f"Total classification groups: {len(classified_results)}")
                for key, props in classified_results.items():
                    logger.info(f"  - {key}: {len(props)} properties")
                
                if create_results_sheet and results_sheet_id:
                    # Use provided results sheet
                    target_spreadsheet_id = results_sheet_id
                    logger.info(f"📊 Target: Results sheet ({results_sheet_id})")
                else:
                    # Use original spreadsheet
                    target_spreadsheet_id = spreadsheet_id
                    logger.info(f"📊 Target: Original sheet ({spreadsheet_id})")
                
                for tab_key, properties in classified_results.items():
                    try:
                        logger.info(f"\n{'─'*80}")
                        logger.info(f"📑 Processing tab: '{tab_key}'")
                        logger.info(f"   Properties count: {len(properties)}")
                        
                        # Parse tab_key (e.g., "tour_general" -> content_type="tour", page_type="general")
                        # Split from the RIGHT to handle multi-word types like "real_estate"
                        parts = tab_key.rsplit('_', 1)  # Use rsplit to split from the right
                        logger.info(f"   Split parts: {parts}")
                        
                        if len(parts) == 2:
                            content_type, page_type = parts
                        else:
                            content_type = tab_key
                            page_type = 'general'
                        
                        logger.info(f"   Parsed - content_type: '{content_type}', page_type: '{page_type}'")
                        
                        # Create tab name (e.g., "tour_general")
                        sheet_name = tab_key
                        logger.info(f"   Sheet name: '{sheet_name}'")
                        
                        # Get or create the sheet tab
                        logger.info(f"   Creating/getting sheet tab...")
                        sheets_service.get_or_create_sheet(target_spreadsheet_id, sheet_name)
                        
                        # Clear the sheet
                        logger.info(f"   Clearing sheet...")
                        sheets_service.clear_sheet(target_spreadsheet_id, sheet_name)
                        
                        # Get column schema for this content type and page type
                        logger.info(f"   Getting column schema for: content_type='{content_type}', page_type='{page_type}'")
                        schema = self._get_column_schema(content_type, page_type)
                        headers = schema['headers']
                        field_keys = schema['field_keys']
                        logger.info(f"   Schema has {len(headers)} columns")
                        
                        # Prepare header row
                        header_row = headers
                        logger.info(f"   Header row: {header_row[:3]}...")
                        
                        # Prepare data rows
                        data_rows = []
                        logger.info(f"   Extracting data from {len(properties)} properties...")
                        
                        for prop_idx, obj in enumerate(properties):
                            row = []
                            for col_idx, field_key in enumerate(field_keys):
                                value = self._extract_field_value(obj, field_key)
                                row.append(value)
                                if prop_idx == 0 and col_idx < 3:  # Log first 3 values of first property
                                    logger.info(f"      [{headers[col_idx]}] ({field_key}) = {str(value)[:50]}")
                            data_rows.append(row)
                        
                        logger.info(f"   Prepared {len(data_rows)} data rows")
                        
                        # Write to sheet
                        all_rows = [header_row] + data_rows
                        logger.info(f"   Writing {len(all_rows)} total rows to sheet...")
                        
                        sheets_service.append_rows(
                            target_spreadsheet_id,
                            f"{sheet_name}!A1",
                            all_rows,
                            sheet_name=sheet_name
                        )
                        
                        tabs_created.append({
                            'name': sheet_name,
                            'count': len(properties),
                            'columns': len(headers),
                            'content_type': content_type,
                            'page_type': page_type
                        })
                        
                        logger.info(f"✅ Created tab '{sheet_name}': {len(properties)} items, {len(headers)} columns")
                        
                    except Exception as e:
                        logger.error(f"Error creating tab for {tab_key}: {e}")
                
                # Send notification email
                admin_panel_url = request.build_absolute_uri('/admin/properties/property/')
                send_batch_completion_email(
                    recipient_email=notify_email,
                    results={
                        'total': total_urls,
                        'processed': processed_count,
                        'failed': failed_count,
                        'results': []
                    },
                    spreadsheet_id=spreadsheet_id,
                    admin_panel_url=admin_panel_url
                )
                
                response_data = {
                    'status': 'completed',
                    'total': total_urls,
                    'processed': processed_count,
                    'failed': failed_count,
                    'task_id': task_id,
                    'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit',
                    'tabs': tabs_created
                }
                
                if create_results_sheet and results_sheet_id:
                    response_data['results_spreadsheet'] = {
                        'spreadsheet_id': results_sheet_id,
                        'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{results_sheet_id}/edit',
                        'tabs': tabs_created
                    }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error processing Google Sheet: {e}", exc_info=True)
                
                # Send error notification
                send_error_notification(
                    recipient_email=notify_email,
                    error_message=str(e),
                    spreadsheet_id=spreadsheet_id
                )
                
                return Response(
                    {'error': f'Failed to process Google Sheet: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


