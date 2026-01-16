# Multi-Content Type Extraction System

Sistema híbrido de detección y extracción de contenido para múltiples dominios: propiedades, tours, restaurantes, tips locales y transporte.

## 🎯 Objetivo

Transformar el sistema de extracción de un "one-size-fits-all" a uno especializado por contexto, donde cada tipo de contenido tiene su propio "experto virtual" con prompt y schema específicos.

## 📋 Content Types Soportados

| Tipo | Icon | Descripción |
|------|------|-------------|
| `real_estate` | 🏠 | Propiedades inmobiliarias: precio, ubicación, características físicas, amenidades |
| `tour` | 🗺️ | Tours y actividades: tipo, duración, precio, qué incluye, nivel de dificultad |
| `restaurant` | 🍴 | Restaurantes: tipo de cocina, rango de precios, platillos destacados, horarios |
| `local_tips` | 💡 | Consejos prácticos: seguridad, costos, qué evitar, costumbres locales |
| `transportation` | 🚗 | Transporte: rutas, costos, horarios, opciones disponibles |

## 🔍 Sistema de Detección Híbrida

La detección usa una estrategia en cascada (del más rápido/confiable al más lento):

### 1. **User Override** (Prioridad Máxima)
- Si el usuario especifica el tipo, se usa ese
- Confidence: 100%

### 2. **Domain Detection** (Rápido y Confiable)
- Detecta por dominio conocido (ej: `coldwellbanker` → `real_estate`)
- Instantáneo, sin costo
- Confidence: 95%

Dominios conocidos:
```python
real_estate: ['brevitas.com', 'coldwellbanker', 'encuentra24.com', 'century21', 'remax']
tour: ['viator.com', 'getyourguide.com', 'tripadvisor']
restaurant: ['yelp.com', 'zomato.com', 'opentable.com']
transportation: ['rome2rio.com', 'uber.com']
local_tips: ['wikivoyage', 'lonelyplanet']
```

### 3. **Keyword Analysis** (Rápido, Gratis)
- Analiza palabras clave en el HTML
- No usa LLM
- Confidence: 30-70% (depende de matches)

### 4. **LLM Classification** (Lento, Preciso) - OPCIONAL
- Solo si `use_llm_fallback=True`
- Usa gpt-4o-mini para clasificar
- Costo extra
- Confidence: 85%

### 5. **Fallback Default**
- Si todo falla: `real_estate` (propósito original)
- Confidence: 30%

## 🚀 Uso

### Detección Automática

```python
from core.llm.content_detection import detect_content_type

# Detectar tipo de contenido
result = detect_content_type(
    url='https://www.viator.com/tours/zipline',
    html=html_content,
    use_llm_fallback=False  # No usar LLM por defecto (más barato)
)

print(result)
# {
#     'content_type': 'tour',
#     'confidence': 0.95,
#     'method': 'domain',
#     'suggested_type': 'tour'
# }
```

### Extracción con Tipo Específico

```python
from core.llm.extraction import extract_content_data

# Extraer datos de un tour
data = extract_content_data(
    content=html_content,
    content_type='tour',
    url='https://viator.com/tours/...'
)

# Datos extraídos según schema de tours
print(data['tour_name'])
print(data['duration_hours'])
print(data['price_usd'])
print(data['included_items'])
```

### Extracción de Propiedades (backward compatible)

```python
from core.llm.extraction import extract_property_data

# Función existente sigue funcionando igual
data = extract_property_data(html_content, url='https://...')
```

### Flujo Completo con Detección + Extracción

```python
from core.llm.content_detection import detect_content_type
from core.llm.extraction import extract_content_data

# 1. Detectar tipo
detection = detect_content_type(url, html)

# 2. Extraer con el tipo detectado
extracted_data = extract_content_data(
    content=html,
    content_type=detection['content_type'],
    url=url
)

# 3. Usar datos
print(f"Detected as: {detection['content_type']}")
print(f"Confidence: {detection['confidence']:.2%}")
print(f"Method: {detection['method']}")
print(f"Extracted data: {extracted_data}")
```

## 🧪 Testing

Ejecutar test suite:

```bash
python test_content_detection.py
```

Tests incluidos:
- ✅ Lista de content types disponibles
- ✅ Detección por dominio (URLs reales)
- ✅ Detección por keywords (HTML samples)
- ✅ Detección híbrida (casos combinados)
- ✅ Preview de prompts de extracción

## 📁 Archivos Creados

```
backend/core/llm/
├── content_types.py         # Configuración de tipos, prompts, keywords
├── content_detection.py     # Sistema de detección híbrida
├── extraction.py            # Modificado: soporta múltiples tipos
└── prompts.py              # Ya existía (PROPERTY_EXTRACTION_PROMPT)

test_content_detection.py    # Test suite
```

## 🔄 Integración con Ingestion API

### Próximos pasos:

1. **Modificar ingestion view** para aceptar `content_type` parameter
2. **Agregar campo `content_type`** al modelo Property (o crear modelos por tipo)
3. **Agregar endpoint de detección**: `POST /api/detect-content-type`
4. **UI Frontend**: Dropdown con tipos + auto-suggestion

### Ejemplo de endpoint:

```python
# En apps/ingestion/views.py

class IngestURLView(APIView):
    def post(self, request):
        url = request.data.get('url')
        user_content_type = request.data.get('content_type')  # Optional
        
        # Scrape
        result = scrape_url(url)
        html = result['html']
        
        # Detect content type
        detection = detect_content_type(
            url=url,
            html=html,
            user_override=user_content_type
        )
        
        # Extract with correct type
        extracted_data = extract_content_data(
            content=html,
            content_type=detection['content_type'],
            url=url
        )
        
        return Response({
            'detection': detection,
            'extracted_data': extracted_data
        })
```

## 📊 Schemas de Extracción

### Real Estate
```json
{
  "property_name": "string",
  "price_usd": number,
  "bedrooms": number,
  "bathrooms": number,
  "square_meters": number,
  "lot_size_m2": number,
  "property_type": "house|condo|villa|land",
  "location": "string",
  ...
}
```

### Tour
```json
{
  "tour_name": "string",
  "tour_type": "adventure|cultural|wildlife|...",
  "price_usd": number,
  "duration_hours": number,
  "difficulty_level": "easy|moderate|challenging",
  "included_items": ["array"],
  "max_participants": number,
  ...
}
```

### Restaurant
```json
{
  "restaurant_name": "string",
  "cuisine_type": "string",
  "price_range": "budget|moderate|upscale|fine_dining",
  "signature_dishes": ["array"],
  "hours_of_operation": "string",
  ...
}
```

### Local Tips
```json
{
  "tip_title": "string",
  "category": "safety|money|transportation|...",
  "practical_advice": ["array"],
  "things_to_avoid": ["array"],
  "emergency_contacts": {},
  ...
}
```

### Transportation
```json
{
  "transport_name": "string",
  "transport_type": "bus|taxi|shuttle|rental_car|...",
  "route": "string",
  "price_usd": number,
  "duration_hours": number,
  "schedule": "string",
  ...
}
```

## 🎨 UI/UX Flow Recomendado

```
Usuario pega URL
      ↓
Sistema analiza (dominio + keywords) ← Instantáneo
      ↓
UI muestra: "Parece ser: 🏠 Propiedad" (pre-seleccionado)
      ↓
Dropdown visible para cambiar:
  ⚪ 🏠 Propiedad / Real Estate
  ⚪ 🗺️ Tour / Actividad  
  ⚪ 🍴 Restaurante
  ⚪ 💡 Tips Locales
  ⚪ 🚗 Transporte
      ↓
Usuario puede cambiar si está mal
      ↓
Click "Extraer" → usa el tipo seleccionado
      ↓
Extrae con el prompt correcto
```

## 💰 Cost Optimization

- **Domain detection**: Gratis, instantáneo
- **Keyword detection**: Gratis, <1ms
- **LLM classification**: ~$0.0001 por detección (solo si se habilita)
- **Extraction**: ~$0.001-0.003 por página (una sola llamada)

**Recomendación**: No usar `use_llm_fallback=True` a menos que sea crítico. El sistema domain+keywords es suficiente en >90% de casos.

## 🔧 Configuración

Para agregar nuevos dominios o keywords:

```python
# En backend/core/llm/content_types.py

CONTENT_TYPES = {
    'tour': {
        'domains': [
            'viator.com',
            'getyourguide.com',
            'tu-nuevo-dominio.com',  # ← Agregar aquí
        ],
        'keywords': [
            'tour',
            'excursion',
            'nueva-keyword',  # ← O agregar keywords
        ],
        ...
    }
}
```

## ✅ Beneficios

- ✨ **Especialización**: Cada tipo tiene su experto con vocabulario correcto
- 🚀 **Rápido**: Domain/keyword detection es instantánea
- 💰 **Económico**: Una sola llamada LLM (no classification si no es necesario)
- 🎯 **Preciso**: Prompts optimizados para cada dominio
- 🔧 **Extensible**: Fácil agregar nuevos tipos
- 🧠 **Inteligente**: Aprende con dominios/keywords sin LLM
- 👥 **User-friendly**: Usuario puede override si el sistema se equivoca

## 📝 Notas

- Sistema es **backward compatible**: `extract_property_data()` sigue funcionando
- Default type es `real_estate` para mantener compatibilidad
- Todo el código existente sigue funcionando sin cambios
