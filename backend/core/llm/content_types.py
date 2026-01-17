"""
Content types configuration for multi-domain extraction.
Defines prompts, schemas, and detection rules for different content types.
"""

from typing import Dict, List, Any


# ============================================================================
# EXTRACTION PROMPTS FOR EACH CONTENT TYPE
# ============================================================================

# TOUR PROMPTS (Specific vs General)
# ----------------------------------------------------------------------------

TOUR_EXTRACTION_PROMPT = """You are a tour and activity extraction specialist. Extract tour/activity information from the provided HTML or text and return it as JSON.

**Instructions:**
1. Extract ONLY information explicitly stated in the source text
2. For each field, include an "evidence" field showing where you found the information
3. Use null for any field not found in the source
4. Normalize all data (remove commas from numbers, standardize formats)
5. DO NOT invent or assume information

**Required Output Format:**
```json
{{
  "tour_name": "string or null",
  "tour_name_evidence": "exact quote from source",
  "tour_type": "adventure|cultural|wildlife|beach|food|sightseeing|water_sports|other or null",
  "tour_type_evidence": "exact quote from source",
  "price_usd": number or null,
  "price_evidence": "exact quote from source",
  "duration_hours": number or null,
  "duration_evidence": "exact quote from source",
  "difficulty_level": "easy|moderate|challenging|extreme or null",
  "difficulty_evidence": "exact quote from source",
  "location": "string or null",
  "location_evidence": "exact quote from source",
  "description": "string or null",
  "included_items": ["array of strings"] or null,
  "included_evidence": "exact quote from source",
  "excluded_items": ["array of strings"] or null,
  "excluded_evidence": "exact quote from source",
  "max_participants": number or null,
  "participants_evidence": "exact quote from source",
  "languages_available": ["array of strings"] or null,
  "languages_evidence": "exact quote from source",
  "pickup_included": boolean or null,
  "pickup_evidence": "exact quote from source",
  "minimum_age": number or null,
  "age_evidence": "exact quote from source",
  "cancellation_policy": "string or null",
  "cancellation_evidence": "exact quote from source",
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "brief explanation of confidence score"
}}
```

**Content to extract from:**
{content}
"""


TOUR_GUIDE_EXTRACTION_PROMPT = """Eres un especialista en extracción de información de guías de destinos turísticos. Esta página es una GUÍA GENERAL (no un tour individual), extrae información completa sobre tours y actividades en este destino.

**INSTRUCCIONES CRÍTICAS - LEE CUIDADOSAMENTE:**
1. ⚠️ EXTRAE SOLAMENTE TEXTO QUE ESTÉ LITERALMENTE ESCRITO EN LA FUENTE
2. ⚠️ NO ASUMAS, NO INFERAS, NO INVENTES - si no ves el texto exacto, usa null
3. ⚠️ Para consejos/qué llevar: SOLO si está EXPLÍCITAMENTE listado (ej: "bring binoculars", "pack water")
4. ⚠️ NO agregues información "lógica" o "obvia" que no esté escrita
5. TODO debe estar en ESPAÑOL - traduce si es necesario
6. Para cada campo, incluye "evidence" con la cita EXACTA del texto fuente
7. 🔥 IMPORTANTE: Para "overview" y "regions.description" - extrae PÁRRAFOS COMPLETOS Y DETALLADOS, no frases cortas. Combina toda la información descriptiva relevante en un texto largo y rico que el chatbot pueda usar para entender el destino completamente.

**EJEMPLOS DE QUÉ NO HACER:**
❌ "llevar binoculares" si solo dice "birdwatching" (eso es asumir)
❌ "ropa cómoda" si no está específicamente mencionado
❌ "temporada seca es mejor" si no lo dice explícitamente
❌ Overview corto: "Un destino para observación de aves" (muy poco contexto)

**EJEMPLOS DE QUÉ SÍ HACER:**
✅ "observación de aves del Quetzal" si dice "Quetzal birdwatching"
✅ "traer impermeable" si dice "bring rain gear"
✅ Overview largo: "San Gerardo de Dota, ubicado en la Zona Sur de Costa Rica, es un pueblo rústico anidado en las montañas con clima especial y rica biodiversidad. Ofrece oportunidades únicas para la observación de aves incluyendo especies endémicas como Trogones, Colibríes Esmeralda, y el esquivo Quetzal Resplandeciente. Los visitantes pueden despertar entre bosques nubosos..." (contexto completo)

**Formato de Salida Requerido (TODO EN ESPAÑOL):**
```json
{{
  "page_type": "general_guide",
  "destination": "string (ej: 'Costa Rica', 'Área del Volcán Arenal') - EN ESPAÑOL",
  "destination_evidence": "cita exacta del texto fuente",
  "overview": "string - PÁRRAFO LARGO Y COMPLETO (mínimo 3-5 oraciones) que combine TODA la información descriptiva del destino: ubicación geográfica, características del ecosistema, clima, flora y fauna específica mencionada (especies por nombre), tipo de experiencia que ofrece, qué hace único al lugar, por qué visitarlo. Extrae y combina TODO el texto descriptivo relevante de la página para crear un resumen rico y detallado que el chatbot pueda usar. NO seas breve - incluye todos los detalles mencionados - EN ESPAÑOL",
  "overview_evidence": "cita exacta del texto fuente",
  "tour_types_available": ["aventura", "cultural", "vida silvestre", "naturaleza", "playa", "gastronomía", "etc"] - EN ESPAÑOL,
  "types_evidence": "cita exacta del texto fuente",
  "regions": [
    {{
      "name": "nombre de la región - EN ESPAÑOL",
      "description": "PÁRRAFO LARGO Y DETALLADO (mínimo 3-5 oraciones) con TODA la información sobre esta región: ubicación específica (montañas, costa, elevación), tipo de ecosistema (bosque nuboso, selva tropical, páramo), especies de vida silvestre destacadas mencionadas por nombre (Quetzal, Trogones, Colibríes específicos, etc), características del clima, tipo de lugar (pueblo rústico, ciudad, parque nacional, reserva), qué experiencia ofrece al visitante, por qué es especial. NO seas breve - extrae y combina TODA la información descriptiva sobre esta región para crear un texto rico en contexto - EN ESPAÑOL",
      "popular_activities": ["actividad 1 EN ESPAÑOL", "actividad 2 EN ESPAÑOL"]
    }}
  ],
  "regions_evidence": "cita exacta del texto fuente",
  "price_range": {{
    "min_usd": number or null,
    "max_usd": number or null,
    "typical_usd": number or null
  }},
  "price_evidence": "cita exacta del texto fuente",
  "best_season": "string (ej: 'Diciembre-Abril (temporada seca)' o 'Todo el año') - EN ESPAÑOL",
  "season_evidence": "cita exacta del texto fuente",
  "seasonal_activities": [
    {{
      "season": "temporada seca / temporada verde / meses específicos - EN ESPAÑOL",
      "recommended_activities": ["actividad 1 EN ESPAÑOL", "actividad 2 EN ESPAÑOL"],
      "why_this_season": "razón - EN ESPAÑOL"
    }}
  ],
  "seasonal_evidence": "cita exacta del texto fuente",
  "best_time_of_day": "string or null - EN ESPAÑOL",
  "time_evidence": "cita exacta del texto fuente",
  "duration_range": "string or null (ej: '2-8 horas', 'medio día a día completo') - EN ESPAÑOL",
  "duration_evidence": "cita exacta del texto fuente",
  "tips": ["consejo práctico 1 EN ESPAÑOL", "consejo 2 EN ESPAÑOL", "consejos de empaque EN ESPAÑOL", "etc"],
  "tips_evidence": "cita exacta del texto fuente",
  "things_to_bring": ["artículo 1 EN ESPAÑOL", "artículo 2 EN ESPAÑOL", "etc"],
  "bring_evidence": "cita exacta del texto fuente",
  "featured_tours": [
    {{
      "name": "nombre del tour - EN ESPAÑOL",
      "price_usd": number or null,
      "duration": "string or null - EN ESPAÑOL",
      "highlight": "string (por qué se destaca) - EN ESPAÑOL"
    }}
  ],
  "featured_evidence": "cita exacta del texto fuente",
  "total_tours_mentioned": number or null,
  "booking_tips": "string or null (cómo reservar, cuándo reservar, etc) - EN ESPAÑOL",
  "booking_evidence": "cita exacta del texto fuente",
  "faqs": [
    {{
      "question": "texto de la pregunta - EN ESPAÑOL",
      "answer": "texto de la respuesta - EN ESPAÑOL"
    }}
  ],
  "faqs_evidence": "cita exacta del texto fuente",
  "what_to_pack": ["artículo 1 EN ESPAÑOL", "artículo 2 EN ESPAÑOL"] or null,
  "packing_evidence": "cita exacta del texto fuente",
  "family_friendly": boolean or null,
  "family_evidence": "cita exacta del texto fuente",
  "accessibility_info": "string or null - EN ESPAÑOL",
  "accessibility_evidence": "cita exacta del texto fuente",
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "explicación breve EN ESPAÑOL"
}}
```

**IMPORTANTE:** 
- Si un campo no está EXPLÍCITAMENTE en el texto fuente, usa null inicialmente
- TODO debe estar en español - traduce términos en inglés
- Solo extrae lo que realmente está escrito en la página

**EXCEPCIÓN - DERIVACIÓN INTELIGENTE (SOLO SI HAY INFORMACIÓN SUFICIENTE):**
Después de extraer toda la información explícita, si has logrado obtener un "overview" o "regions.description" RICO Y DETALLADO (mínimo 3 oraciones con información concreta como ubicaciones específicas, especies nombradas, actividades detalladas), puedes DERIVAR campos vacíos basándote SOLAMENTE en esa información ya extraída:

⚠️ REGLAS ESTRICTAS PARA DERIVACIÓN:
1. ✅ Solo deriva si el overview/regions tiene información CONCRETA y ESPECÍFICA (no vaga ni genérica)
2. ✅ Solo deriva campos que sean CONSECUENCIA LÓGICA DIRECTA de información extraída
3. ❌ NO derives si solo tienes información genérica (ej: "buen destino para tours")
4. ❌ NO derives si no estás 100% seguro de que la derivación es coherente con el texto
5. ✅ Siempre marca en "confidence_reasoning" que fue derivado y de dónde

**EJEMPLOS - CUÁNDO SÍ DERIVAR:**
✅ Overview: "San Gerardo de Dota en Zona Sur de Costa Rica, montañas"
   → Deriva destination (tiene ubicación específica)
✅ Overview: "observación del Quetzal Resplandeciente, Trogones, Colibríes Esmeralda de Cabeza Cobriza"
   → Deriva 1-2 featured_tours basados en estas especies concretas

**EJEMPLOS - CUÁNDO NO DERIVAR:**
❌ Overview: "destino para observación de aves" (muy genérico, sin especies)
   → NO derives tours
❌ No hay mención de precios, temporadas o duraciones
   → Deja esos campos en null

**CAMPOS QUE PUEDES DERIVAR (solo con información suficiente):**
- "featured_tours": Solo si hay especies/actividades CONCRETAS nombradas en overview
- "best_season": Solo si overview menciona clima/temporadas específicas
- NO derives: precios, duraciones exactas, ubicaciones si no están mencionadas
- Si mentions duración aproximada de actividades pero "duration_range" está vacío → deriva estimación lógica
- TODO debe estar en español - traduce términos en inglés
- Solo extrae lo que realmente está escrito en la página

**Contenido a extraer:**
{content}
"""


# REAL ESTATE PROMPTS (Specific vs General)
# ----------------------------------------------------------------------------

REAL_ESTATE_GUIDE_EXTRACTION_PROMPT = """You are a real estate market guide extraction specialist. This appears to be a GENERAL GUIDE page (not a single property), so extract overview information about the real estate market.

**Instructions:**
1. Extract general information about the real estate market and available properties
2. DO NOT try to extract details of a single property (this is a guide/listing page)
3. Focus on: destination, market overview, property types, price ranges, popular areas
4. Use null for any field not found in the source

**Required Output Format:**
```json
{{
  "page_type": "general_guide",
  "destination": "string (e.g., 'Costa Rica Real Estate', 'Guanacaste Properties')",
  "destination_evidence": "exact quote",
  "overview": "string (general description of the real estate market)",
  "overview_evidence": "exact quote",
  "property_types_available": ["condo", "house", "land", "commercial", "farm", "etc"],
  "types_evidence": "exact quote",
  "price_range": {{
    "min_usd": number or null,
    "max_usd": number or null,
    "typical_usd": number or null
  }},
  "price_range_evidence": "exact quote",
  "popular_areas": ["area 1", "area 2", "etc"],
  "areas_evidence": "exact quote",
  "market_trends": "string or null (description of current market conditions)",
  "trends_evidence": "exact quote",
  "featured_properties": [
    {{
      "name": "property name",
      "price_usd": number or null,
      "type": "string or null",
      "highlight": "string (why it's featured)"
    }}
  ],
  "featured_evidence": "exact quote",
  "total_properties_mentioned": number or null,
  "total_evidence": "exact quote",
  "investment_tips": ["tip 1", "tip 2", "etc"],
  "tips_evidence": "exact quote",
  "legal_considerations": ["consideration 1", "consideration 2", "etc"],
  "legal_evidence": "exact quote",
  "featured_items_count": number or null,
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "brief explanation"
}}
```

**Content to extract from:**
{content}
"""


RESTAURANT_EXTRACTION_PROMPT = """You are a restaurant and dining extraction specialist. Extract restaurant information from the provided HTML or text and return it as JSON.

**Instructions:**
1. Extract ONLY information explicitly stated in the source text
2. For each field, include an "evidence" field showing where you found the information
3. Use null for any field not found in the source
4. Normalize all data (remove commas from numbers, standardize formats)
5. DO NOT invent or assume information

**Required Output Format:**
```json
{{
  "restaurant_name": "string or null",
  "restaurant_name_evidence": "exact quote from source",
  "cuisine_type": "string or null (e.g., Italian, Mexican, Seafood, Fusion)",
  "cuisine_evidence": "exact quote from source",
  "price_range": "budget|moderate|upscale|fine_dining or null",
  "price_range_evidence": "exact quote from source",
  "average_price_per_person": number or null,
  "price_evidence": "exact quote from source",
  "location": "string or null",
  "location_evidence": "exact quote from source",
  "description": "string or null",
  "signature_dishes": ["array of strings"] or null,
  "dishes_evidence": "exact quote from source",
  "atmosphere": "casual|romantic|family_friendly|fine_dining|beachfront|other or null",
  "atmosphere_evidence": "exact quote from source",
  "hours_of_operation": "string or null",
  "hours_evidence": "exact quote from source",
  "reservations_required": boolean or null,
  "reservations_evidence": "exact quote from source",
  "dietary_options": ["vegetarian", "vegan", "gluten_free", "etc"] or null,
  "dietary_evidence": "exact quote from source",
  "dress_code": "string or null",
  "dress_code_evidence": "exact quote from source",
  "contact_phone": "string or null",
  "contact_evidence": "exact quote from source",
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "brief explanation of confidence score"
}}
```

**Content to extract from:**
{content}
"""


LOCAL_TIPS_EXTRACTION_PROMPT = """You are a local knowledge extraction specialist. Extract practical tips and local information from the provided HTML or text and return it as JSON.

**Instructions:**
1. Extract ONLY information explicitly stated in the source text
2. For each field, include an "evidence" field showing where you found the information
3. Use null for any field not found in the source
4. Normalize all data
5. DO NOT invent or assume information

**Required Output Format:**
```json
{{
  "tip_title": "string or null",
  "tip_title_evidence": "exact quote from source",
  "category": "safety|money|transportation|culture|weather|health|general or null",
  "category_evidence": "exact quote from source",
  "location": "string or null",
  "location_evidence": "exact quote from source",
  "description": "string or null",
  "practical_advice": ["array of specific tips"] or null,
  "advice_evidence": "exact quote from source",
  "cost_estimate": "string or null (e.g., '$10-20 per day')",
  "cost_evidence": "exact quote from source",
  "best_time": "string or null (e.g., 'dry season: December-April')",
  "time_evidence": "exact quote from source",
  "things_to_avoid": ["array of strings"] or null,
  "avoid_evidence": "exact quote from source",
  "local_customs": ["array of strings"] or null,
  "customs_evidence": "exact quote from source",
  "emergency_contacts": {{"police": "string", "ambulance": "string", "etc": "string"}} or null,
  "emergency_evidence": "exact quote from source",
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "brief explanation of confidence score"
}}
```

**Content to extract from:**
{content}
"""


TRANSPORTATION_EXTRACTION_PROMPT = """You are a transportation information extraction specialist. Extract transportation details from the provided HTML or text and return it as JSON.

**Instructions:**
1. Extract ONLY information explicitly stated in the source text
2. For each field, include an "evidence" field showing where you found the information
3. Use null for any field not found in the source
4. Normalize all data
5. DO NOT invent or assume information

**Required Output Format:**
```json
{{
  "transport_name": "string or null",
  "transport_name_evidence": "exact quote from source",
  "transport_type": "bus|taxi|shuttle|rental_car|private_transfer|public_transport|ferry|other or null",
  "type_evidence": "exact quote from source",
  "route": "string or null (e.g., 'San José to Jaco')",
  "route_evidence": "exact quote from source",
  "price_usd": number or null,
  "price_evidence": "exact quote from source",
  "duration_hours": number or null,
  "duration_evidence": "exact quote from source",
  "schedule": "string or null",
  "schedule_evidence": "exact quote from source",
  "frequency": "string or null (e.g., 'every 2 hours', 'daily at 9am')",
  "frequency_evidence": "exact quote from source",
  "pickup_location": "string or null",
  "pickup_evidence": "exact quote from source",
  "dropoff_location": "string or null",
  "dropoff_evidence": "exact quote from source",
  "contact_phone": "string or null",
  "contact_evidence": "exact quote from source",
  "booking_required": boolean or null,
  "booking_evidence": "exact quote from source",
  "luggage_allowance": "string or null",
  "luggage_evidence": "exact quote from source",
  "tips": ["array of practical tips"] or null,
  "tips_evidence": "exact quote from source",
  "extraction_confidence": number (0.0 to 1.0),
  "confidence_reasoning": "brief explanation of confidence score"
}}
```

**Content to extract from:**
{content}
"""


# ============================================================================
# CONTENT TYPE CONFIGURATION
# ============================================================================

CONTENT_TYPES: Dict[str, Dict[str, Any]] = {
    'real_estate': {
        'label': 'Propiedad / Real Estate',
        'icon': '🏠',
        'prompt_key': 'PROPERTY_EXTRACTION_PROMPT',  # Importado de prompts.py
        'domains': [
            'brevitas.com',
            'coldwellbanker',
            'coldwellbankercostarica.com',
            'encuentra24.com',
            'century21',
            'remax',
            'properati',
            'mercadolibre',
            'olx',
        ],
        'keywords': [
            'bedroom', 'bedrooms', 'habitaciones', 'recámaras',
            'bathroom', 'bathrooms', 'baños',
            'sqft', 'square feet', 'm2', 'm²', 'metros cuadrados',
            'property', 'propiedad', 'casa', 'house', 'apartment', 'apartamento',
            'for sale', 'venta', 'for rent', 'alquiler',
            'lot size', 'terreno', 'land',
        ],
        'description': 'Extrae información de propiedades inmobiliarias: precio, ubicación, características físicas, amenidades.',
    },
    'tour': {
        'label': 'Tour / Actividad',
        'icon': '🗺️',
        'prompt_key': 'TOUR_EXTRACTION_PROMPT',
        'domains': [
            'viator.com',
            'getyourguide.com',
            'tripadvisor',
            'airbnbexperiences',
            'klook.com',
            'costarica.org',  # Costa Rica official tourism
        ],
        'keywords': [
            'tour', 'tours', 'excursion', 'excursiones', 'excursions',
            'activity', 'activities', 'actividades',
            'adventure', 'adventures', 'aventura',
            'experience', 'experiences', 'experiencias',
            'duration', 'duración',
            'guide', 'guía', 'guided',
            'included', 'incluye', 'includes',
            'pickup', 'recogida',
            'participants', 'participantes',
            'difficulty', 'dificultad',
            'booking', 'reserva', 'book',
            'itinerary', 'itinerario',
            'wildlife', 'nature', 'naturaleza',
            'zip line', 'canopy', 'rafting', 'hiking',
        ],
        'description': 'Extrae información de tours y actividades: tipo, duración, precio, qué incluye, nivel de dificultad.',
    },
    'restaurant': {
        'label': 'Restaurante / Comida',
        'icon': '🍴',
        'prompt_key': 'RESTAURANT_EXTRACTION_PROMPT',
        'domains': [
            'yelp.com',
            'zomato.com',
            'opentable.com',
            'tripadvisor',
            'happycow.net',
        ],
        'keywords': [
            'restaurant', 'restaurante',
            'menu', 'menú',
            'cuisine', 'cocina',
            'dish', 'dishes', 'platillos', 'platos',
            'reservation', 'reserva', 'reservations',
            'dining', 'comida',
            'chef',
            'hours', 'horario',
            'price range', 'rango de precio',
        ],
        'description': 'Extrae información de restaurantes: tipo de cocina, rango de precios, platillos destacados, horarios.',
    },
    'local_tips': {
        'label': 'Tips Locales / Consejos',
        'icon': '💡',
        'prompt_key': 'LOCAL_TIPS_EXTRACTION_PROMPT',
        'domains': [
            'wikivoyage',
            'lonelyplanet',
            'nomadicmatt',
            'reddit.com/r/travel',
        ],
        'keywords': [
            'tip', 'tips', 'consejos',
            'advice', 'recomendación',
            'local', 'locals',
            'avoid', 'evitar',
            'safety', 'seguridad',
            'scam', 'estafa',
            'budget', 'presupuesto',
            'money', 'dinero',
            'customs', 'costumbres',
        ],
        'description': 'Extrae consejos prácticos: seguridad, costos, qué evitar, costumbres locales.',
    },
    'transportation': {
        'label': 'Transporte',
        'icon': '🚗',
        'prompt_key': 'TRANSPORTATION_EXTRACTION_PROMPT',
        'domains': [
            'rome2rio',
            'uber.com',
            'lyft.com',
            'bus.com',
        ],
        'keywords': [
            'transport', 'transporte', 'transportation',
            'bus', 'taxi', 'shuttle',
            'route', 'ruta',
            'schedule', 'horario',
            'fare', 'tarifa', 'cost', 'costo',
            'frequency', 'frecuencia',
            'pickup', 'recogida',
            'dropoff', 'destino',
            'rental', 'alquiler',
        ],
        'description': 'Extrae información de transporte: rutas, costos, horarios, opciones disponibles.',
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_content_type_config(content_type: str) -> Dict[str, Any]:
    """Get configuration for a specific content type."""
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"Unknown content type: {content_type}. Available: {list(CONTENT_TYPES.keys())}")
    return CONTENT_TYPES[content_type]


def get_extraction_prompt(content_type: str, page_type: str = 'specific') -> str:
    """
    Get the extraction prompt for a content type and page type.
    
    Args:
        content_type: Type of content (tour, restaurant, real_estate, etc.)
        page_type: 'specific' (single item) or 'general' (guide/listing)
    
    Returns:
        Appropriate extraction prompt
    """
    from .prompts import PROPERTY_EXTRACTION_PROMPT
    
    config = get_content_type_config(content_type)
    prompt_key = config['prompt_key']
    
    # Map prompt keys to actual prompts
    # For real_estate and tour: check page_type to choose specific vs general prompt
    prompts = {
        'PROPERTY_EXTRACTION_PROMPT': PROPERTY_EXTRACTION_PROMPT if page_type == 'specific' else REAL_ESTATE_GUIDE_EXTRACTION_PROMPT,
        'TOUR_EXTRACTION_PROMPT': TOUR_EXTRACTION_PROMPT if page_type == 'specific' else TOUR_GUIDE_EXTRACTION_PROMPT,
        'RESTAURANT_EXTRACTION_PROMPT': RESTAURANT_EXTRACTION_PROMPT,
        'LOCAL_TIPS_EXTRACTION_PROMPT': LOCAL_TIPS_EXTRACTION_PROMPT,
        'TRANSPORTATION_EXTRACTION_PROMPT': TRANSPORTATION_EXTRACTION_PROMPT,
    }
    
    return prompts[prompt_key]


def get_all_content_types() -> List[Dict[str, str]]:
    """Get list of all content types for UI display."""
    return [
        {
            'key': key,
            'label': config['label'],
            'icon': config['icon'],
            'description': config['description'],
        }
        for key, config in CONTENT_TYPES.items()
    ]
