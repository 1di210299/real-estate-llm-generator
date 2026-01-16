"""
Content types configuration for multi-domain extraction.
Defines prompts, schemas, and detection rules for different content types.
"""

from typing import Dict, List, Any


# ============================================================================
# EXTRACTION PROMPTS FOR EACH CONTENT TYPE
# ============================================================================

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
        ],
        'keywords': [
            'tour', 'tours', 'excursion', 'excursiones',
            'activity', 'activities', 'actividades',
            'duration', 'duración',
            'guide', 'guía',
            'included', 'incluye', 'includes',
            'pickup', 'recogida',
            'participants', 'participantes',
            'difficulty', 'dificultad',
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


def get_extraction_prompt(content_type: str) -> str:
    """Get the extraction prompt for a content type."""
    from .prompts import PROPERTY_EXTRACTION_PROMPT
    
    config = get_content_type_config(content_type)
    prompt_key = config['prompt_key']
    
    # Map prompt keys to actual prompts
    prompts = {
        'PROPERTY_EXTRACTION_PROMPT': PROPERTY_EXTRACTION_PROMPT,
        'TOUR_EXTRACTION_PROMPT': TOUR_EXTRACTION_PROMPT,
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
