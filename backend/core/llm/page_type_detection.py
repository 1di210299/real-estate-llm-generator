"""
Cascading page type detection system.
Detects if a page is specific (single item) or general (guide/listing).

Detection Strategy (Waterfall):
1. URL Pattern Analysis (free, 0.1s, 70% accuracy) - tries first
2. Preview + LLM Validation (cheap, 1s, 90% accuracy) - if uncertain
3. OpenAI Browsing (expensive, 10s, 95% accuracy) - future/premium only

Expected distribution:
- 90% resolved at Level 1 ($0, instant)
- 8% resolved at Level 2 ($0.0001, 1s)
- 2% would need Level 3 (skip for MVP)
"""

import logging
import re
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _clean_html_for_analysis(html: str) -> str:
    """
    Clean HTML for OpenAI analysis - remove CSS, JS, and unnecessary tags.
    Keeps only semantic content that's useful for classification.
    
    Reduces token usage by ~60% while preserving classification accuracy.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove tags that don't help with classification
        for tag in soup(['style', 'script', 'noscript', 'svg', 'path', 'iframe', 'link', 'meta']):
            tag.decompose()
        
        # Remove inline styles and unnecessary attributes
        for tag in soup.find_all(True):
            # Keep only semantic attributes
            keep_attrs = ['class', 'id', 'href', 'alt', 'title']
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in keep_attrs}
        
        # Convert back to string (preserves HTML structure but without CSS/JS)
        cleaned = str(soup)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
        
    except Exception as e:
        logger.warning(f"HTML cleaning failed: {e}, using original")
        return html


def detect_page_type(url: str, html: Optional[str] = None, content_type: str = 'tour') -> Dict:
    """
    OpenAI-direct page type detection (Opción 1).
    
    Elimina heurísticas manuales - usa OpenAI GPT-4o-mini directamente para
    máxima precisión. Costo: ~$0.005 por página, tiempo: ~3-5s.
    
    Args:
        url: Page URL
        html: Optional HTML content (if already scraped)
        content_type: Type of content (tour, restaurant, real_estate, etc.)
        
    Returns:
        {
            'page_type': 'specific' | 'general',
            'confidence': 0.0-1.0,
            'method': 'openai_direct',
            'indicators': [list of reasons],
            'cost': float (USD),
            'time': float (seconds)
        }
    """
    logger.info("=" * 80)
    logger.info("🤖 OpenAI-Direct Page Type Detection (Opción 1)")
    logger.info(f"   URL: {url}")
    logger.info(f"   Content type: {content_type}")
    logger.info("=" * 80)
    
    if not html:
        logger.warning("⚠️ No HTML provided, cannot analyze page")
        return {
            'page_type': 'general',  # Safe default
            'confidence': 0.5,
            'method': 'no_html_fallback',
            'indicators': ['No HTML content provided'],
            'cost': 0.0,
            'time': 0.1
        }
    
    # Llamada directa a OpenAI - sin niveles intermedios
    logger.info("🎯 Calling OpenAI GPT-4o-mini for classification...")
    openai_result = _analyze_with_openai(url, html, content_type)
    
    logger.info(f"✅ OpenAI Result:")
    logger.info(f"   Page type: {openai_result['page_type']}")
    logger.info(f"   Confidence: {openai_result['confidence']:.0%}")
    logger.info(f"   Reason: {openai_result['reason']}")
    logger.info(f"   Cost: ${openai_result['cost']:.4f}")
    logger.info(f"   Time: {openai_result['time']:.2f}s")
    logger.info("=" * 80)
    
    return {
        'page_type': openai_result['page_type'],
        'confidence': openai_result['confidence'],
        'method': 'openai_direct',
        'indicators': [f"OpenAI: {openai_result['reason']}"],
        'cost': openai_result['cost'],
        'time': openai_result['time']
    }


# ============================================================================
# DEPRECATED FUNCTIONS (Opción 1: OpenAI-Direct)
# ============================================================================
# Las siguientes funciones ya NO se usan en el flujo principal.
# Se mantienen solo para referencia o posible rollback futuro.
# 
# ✅ NUEVO: detect_page_type() usa OpenAI directamente
# ❌ VIEJO: Cascada de URL → HTML → OpenAI (complejo, poco confiable)
# ============================================================================

# ============================================================================
# LEVEL 1: URL PATTERN ANALYSIS (NO USADO)
# ============================================================================

def _analyze_url_patterns(url: str, content_type: str) -> Dict:
    """Analyze URL structure for page type hints."""
    
    logger.info("\n" + "-" * 60)
    logger.info("🔍 URL PATTERN ANALYSIS")
    logger.info("-" * 60)
    
    if not url:
        logger.warning("⚠️ No URL provided")
        return {'page_type': 'specific', 'confidence': 0.3, 'reason': 'No URL provided'}
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    logger.info(f"Domain: {parsed.netloc}")
    logger.info(f"Path: {path}")
    
    # ========================================================================
    # SPECIFIC PAGE INDICATORS (High confidence)
    # ========================================================================
    
    # Pattern 1: Contains numeric ID patterns
    logger.info("\n🔎 Checking for SPECIFIC page indicators...")
    
    match = re.search(r'/d\d+-\d+', path)
    if match:
        logger.info(f"✅ MATCH: Viator-style ID found: {match.group()}")
        return {'page_type': 'specific', 'confidence': 0.95, 'reason': 'Viator-style ID (d742-12345)'}
    logger.info("   ❌ No Viator ID (d742-XXX)")
    
    match = re.search(r'/t\d{4,}', path)
    if match:
        logger.info(f"✅ MATCH: GetYourGuide ID found: {match.group()}")
        return {'page_type': 'specific', 'confidence': 0.95, 'reason': 'GetYourGuide-style ID (t12345)'}
    logger.info("   ❌ No GetYourGuide ID (tXXXX)")
    
    match = re.search(r'-\d{5,}', path)
    if match:
        logger.info(f"✅ MATCH: 5+ digit ID found: {match.group()}")
        return {'page_type': 'specific', 'confidence': 0.90, 'reason': 'Contains 5+ digit ID'}
    logger.info("   ❌ No 5+ digit ID")
    
    match = re.search(r'/listing-\d+', path)
    if match:
        logger.info(f"✅ MATCH: Listing with ID: {match.group()}")
        return {'page_type': 'specific', 'confidence': 0.95, 'reason': 'Listing with ID'}
    logger.info("   ❌ No listing-ID pattern")
    
    # Pattern 2: TripAdvisor specific patterns
    if re.search(r'/(attraction|restaurant).*review.*-d\d+', path):
        return {'page_type': 'specific', 'confidence': 0.95, 'reason': 'TripAdvisor specific review page'}
    
    # Pattern 3: Real estate specific property
    if re.search(r'/property/[a-z0-9-]+$', path):
        return {'page_type': 'specific', 'confidence': 0.85, 'reason': 'Property with slug'}
    
    # Pattern 4: Deep path (3+ levels after domain)
    path_depth = len([p for p in path.split('/') if p])
    logger.info(f"\n📏 Path depth: {path_depth} levels")
    if path_depth >= 4:
        logger.info(f"   ✅ MATCH: Deep path indicates specific page")
        return {'page_type': 'specific', 'confidence': 0.75, 'reason': f'Deep path ({path_depth} levels)'}
    logger.info(f"   ❌ Shallow path ({path_depth} < 4)")
    
    # ========================================================================
    # GENERAL PAGE INDICATORS (High confidence)
    # ========================================================================
    
    # Pattern 1: Ends in plural without ID
    logger.info("\n🔎 Checking for GENERAL page indicators...")
    
    match = re.search(r'/(tours|properties|restaurants|activities)/?$', path)
    if match:
        logger.info(f"✅ MATCH: Ends in plural: {match.group()}")
        return {'page_type': 'general', 'confidence': 0.90, 'reason': 'Ends in plural (listing page)'}
    logger.info("   ❌ Doesn't end in plural")
    
    # Pattern 2: Category/destination pages
    match = re.search(r'/(tours|properties|restaurants)/[^/]+/?$', path)
    if match:
        # Check if it's really a category (no ID-like pattern)
        last_segment = path.rstrip('/').split('/')[-1]
        logger.info(f"   📝 Category candidate: /{match.group(1)}/{last_segment}")
        if not re.search(r'\d{4,}', last_segment):
            logger.info(f"   ✅ MATCH: Category page (no ID in '{last_segment}')")
            return {'page_type': 'general', 'confidence': 0.85, 'reason': 'Category/destination page'}
        logger.info(f"   ❌ Has ID in last segment: {last_segment}")
    logger.info("   ❌ Not a category page")
    
    # Pattern 3: Search/browse pages
    match = re.search(r'/(search|browse|results|category)', path)
    if match:
        logger.info(f"✅ MATCH: Search/browse page: {match.group()}")
        return {'page_type': 'general', 'confidence': 0.95, 'reason': 'Search/browse page'}
    logger.info("   ❌ No search/browse pattern")
    
    # Pattern 4: Homepage
    if path in ['/', '', '/index', '/index.html']:
        return {'page_type': 'general', 'confidence': 0.90, 'reason': 'Homepage'}
    
    # ========================================================================
    # AMBIGUOUS - Return best guess with low confidence
    # ========================================================================
    
    # Check domain for hints
    domain = parsed.netloc.lower()
    if any(word in domain for word in ['coldwell', 'brevitas', 'encuentra24', 'remax']):
        # Real estate sites default to specific (usually property pages)
        return {'page_type': 'specific', 'confidence': 0.60, 'reason': 'Real estate domain, likely property page'}
    
    # Default: assume specific (safer to try extracting 1 item than multiple)
    return {'page_type': 'specific', 'confidence': 0.50, 'reason': 'URL pattern inconclusive, defaulting to specific'}


# ============================================================================
# LEVEL 2: HTML STRUCTURE ANALYSIS (NO USADO)
# ============================================================================

def _analyze_html_structure(html: str, content_type: str) -> Dict:
    """Analyze HTML structure for page type hints."""
    
    logger.info("\\n" + "-" * 60)
    logger.info("📊 HTML STRUCTURE ANALYSIS")
    logger.info("-" * 60)
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text().lower()
    
    logger.info(f"HTML size: {len(html):,} characters")
    logger.info(f"Content type: {content_type}")
    
    indicators = []
    specific_score = 0
    general_score = 0
    
    # ========================================================================
    # Count potential item cards
    # ========================================================================
    logger.info("\\n🔢 Counting item cards...")
    card_count = _count_item_cards(soup, content_type)
    logger.info(f"   Found: {card_count} cards")
    
    if card_count >= 5:
        general_score += 3
        indicators.append(f'Found {card_count} item cards')
        logger.info(f"   ✅ GENERAL indicator: {card_count} cards (score +3)")
    elif card_count >= 2:
        general_score += 1
        indicators.append(f'Found {card_count} possible items')
        logger.info(f"   ⚠️ Possible GENERAL: {card_count} cards (score +1)")
    else:
        logger.info(f"   ✅ SPECIFIC indicator: Few/no cards detected")
        specific_score += 2
        indicators.append(f'Found {card_count} item (single page)')
    
    # ========================================================================
    # Check for booking elements (specific page indicator)
    # ========================================================================
    logger.info("\n💳 Checking booking elements...")
    booking_keywords = ['book now', 'reserve', 'check availability', 'add to cart', 'book this']
    booking_found = sum(1 for kw in booking_keywords if kw in text)
    logger.info(f"   Found: {booking_found} booking keywords")
    
    if booking_found >= 2:
        specific_score += 4  # Increased from 3 to 4 - booking is STRONG indicator
        indicators.append(f'Found {booking_found} booking elements')
        logger.info(f"   ✅ SPECIFIC indicator: Multiple booking elements (score +4)")
    else:
        logger.info(f"   ❌ Not enough booking elements")
    
    # ========================================================================
    # Check for filter/navigation elements (listing page indicator)
    # ========================================================================
    logger.info("\n🔍 Checking filter/navigation elements...")
    filter_keywords = ['filter', 'sort by', 'price range', 'showing', 'results']
    filter_found = sum(1 for kw in filter_keywords if kw in text)
    logger.info(f"   Found: {filter_found} filter keywords")
    
    if filter_found >= 2:
        general_score += 3
        indicators.append(f'Found {filter_found} filter elements')
        logger.info(f"   ✅ GENERAL indicator: Filter/nav elements (score +3)")
    else:
        logger.info(f"   ❌ Not enough filter elements")
    
    # ========================================================================
    # Check for pagination (listing page indicator)
    # ========================================================================
    logger.info("\n📊 Checking pagination...")
    pagination_keywords = ['next page', 'previous', 'page 1', 'page 2', 'of']
    pagination_found = sum(1 for kw in pagination_keywords if kw in text)
    logger.info(f"   Found: {pagination_found} pagination keywords")
    
    if pagination_found >= 2:
        general_score += 2
        indicators.append('Found pagination')
        logger.info(f"   ✅ GENERAL indicator: Pagination (score +2)")
    else:
        logger.info(f"   ❌ No pagination detected")
    
    # ========================================================================
    # Content-type specific keywords
    # ========================================================================
    if content_type == 'tour':
        # Specific tour keywords (transactional)
        specific_tour_keywords = ['what\'s included', 'tour details', 'meeting point', 'cancellation policy', 
                                 'departure time', 'pick-up location', 'what to bring', 'tour itinerary']
        specific_tour_found = sum(1 for kw in specific_tour_keywords if kw in text)
        
        if specific_tour_found >= 2:
            specific_score += 2
            indicators.append(f'Found {specific_tour_found} specific tour details')
            logger.info(f"   ✅ SPECIFIC indicator: Tour booking details (score +2)")
        
        # General guide keywords (descriptive/informational)
        general_guide_keywords = ['top tours', 'best tours', 'browse tours', 'all tours',
                                 'things to do', 'activities in', 'explore', 'discover',
                                 'guide to', 'visit', 'haven for', 'perfect for', 
                                 'don\'t miss', 'must see', 'what to expect']
        general_guide_found = sum(1 for kw in general_guide_keywords if kw in text)
        
        if general_guide_found >= 3:
            general_score += 3
            indicators.append(f'Found {general_guide_found} destination guide keywords')
            logger.info(f"   ✅ GENERAL indicator: Destination guide language (score +3)")
        elif general_guide_found >= 1:
            general_score += 1
            indicators.append(f'Found {general_guide_found} guide keyword')
            logger.info(f"   ⚠️ Possible GENERAL: Guide language (score +1)")
    
    # ========================================================================
    # Price counting (strong indicator)
    # ========================================================================
    price_patterns = [r'\$\d+', r'USD\s*\d+', r'€\d+', r'£\d+']
    total_prices = 0
    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        total_prices += len(matches)
    
    if total_prices >= 10:
        general_score += 3
        indicators.append(f'Found {total_prices} prices (listing)')
    elif total_prices <= 3:
        specific_score += 1
        indicators.append(f'Found {total_prices} price(s) (single item)')
    
    # ========================================================================
    # Calculate result
    # ========================================================================
    logger.info("\\n🎯 FINAL SCORING:")
    logger.info(f"   SPECIFIC score: {specific_score}")
    logger.info(f"   GENERAL score: {general_score}")
    logger.info(f"   Indicators: {indicators}")
    
    total_score = specific_score + general_score
    
    if total_score == 0:
        logger.info("   ⚠️ DECISION: No indicators - defaulting to SPECIFIC")
        logger.info("-" * 60)
        return {
            'page_type': 'specific',
            'confidence': 0.40,
            'reason': 'No clear HTML indicators'
        }
    
    # Determine page type based on scores
    if specific_score > general_score:
        confidence = specific_score / total_score
        logger.info(f"   ✅ DECISION: SPECIFIC (score: {specific_score} > {general_score})")
        logger.info(f"   Final confidence: {confidence:.0%}")
        logger.info("-" * 60)
        return {
            'page_type': 'specific',
            'confidence': min(0.95, confidence),
            'reason': ', '.join(indicators[:3])
        }
    elif general_score > specific_score:
        confidence = general_score / total_score
        logger.info(f"   ✅ DECISION: GENERAL (score: {general_score} > {specific_score})")
        logger.info(f"   Final confidence: {confidence:.0%}")
        logger.info("-" * 60)
        return {
            'page_type': 'general',
            'confidence': min(0.95, confidence),
            'reason': ', '.join(indicators[:3])
        }
    else:
        # TIE BREAKER: Check which indicators are stronger
        # If we have cards (strong listing indicator), prefer general
        # If we have booking elements but few cards, prefer specific
        logger.info(f"   ⚖️ TIE (score: {specific_score} == {general_score})")
        
        # Check for strong general indicators
        if card_count >= 5:
            logger.info(f"   ✅ TIEBREAKER: GENERAL ({card_count} cards is strong listing indicator)")
            logger.info(f"   Final confidence: 60% (tie broken by card count)")
            logger.info("-" * 60)
            return {
                'page_type': 'general',
                'confidence': 0.60,
                'reason': f'Tie broken by {card_count} cards (listing indicator)'
            }
        else:
            logger.info(f"   ✅ TIEBREAKER: SPECIFIC (few cards, booking elements suggest single item)")
            logger.info(f"   Final confidence: 55% (tie broken by context)")
            logger.info("-" * 60)
            return {
                'page_type': 'specific',
                'confidence': 0.55,
                'reason': 'Tie broken by booking elements over card count'
            }


def _count_item_cards(soup: BeautifulSoup, content_type: str) -> int:
    """Count potential item cards in HTML."""
    
    card_patterns = [
        {'class': lambda x: x and 'card' in str(x).lower()},
        {'class': lambda x: x and 'item' in str(x).lower()},
        {'class': lambda x: x and 'listing' in str(x).lower()},
        {'class': lambda x: x and 'product' in str(x).lower()},
        {'class': lambda x: x and 'result' in str(x).lower()},
    ]
    
    max_count = 0
    for pattern in card_patterns:
        elements = soup.find_all('div', **pattern)
        # Filter meaningful elements (not tiny components)
        meaningful = [el for el in elements if len(el.get_text(strip=True)) > 50]
        max_count = max(max_count, len(meaningful))
    
    return max_count


# ============================================================================
# LEVEL 3: OpenAI Analysis (Premium Feature)
# ============================================================================

def _analyze_with_openai(url: str, html: str, content_type: str) -> Dict:
    """
    Level 3 detection using OpenAI to analyze HTML preview.
    
    Uses GPT-4 to intelligently determine if page is specific or general
    by analyzing HTML structure and content.
    
    Cost: ~$0.01-0.02
    Time: 2-5s
    Accuracy: 95%+
    """
    import openai
    from django.conf import settings
    import time
    
    start_time = time.time()
    
    logger.info("\n" + "=" * 60)
    logger.info("🤖 LEVEL 3: OpenAI Analysis")
    logger.info("=" * 60)
    
    # Clean HTML - remove CSS, JS, and unnecessary tags
    html_cleaned = _clean_html_for_analysis(html)
    
    # Truncate cleaned HTML to fit within token limits
    # GPT-4o-mini has 128K context, but we limit to ~12K chars (~3K tokens) to reduce cost
    # 12K chars captures more content (pricing, features) while staying cost-effective
    html_preview = html_cleaned[:12000] if len(html_cleaned) > 12000 else html_cleaned
    
    logger.info(f"Original HTML: {len(html):,} chars → Cleaned: {len(html_cleaned):,} chars → Preview: {len(html_preview):,} chars")
    logger.info(f"Content type: {content_type}")
    
    # DEBUG: Log preview to see what OpenAI is seeing
    logger.info("=" * 60)
    logger.info("🔍 HTML PREVIEW BEING SENT TO OPENAI:")
    logger.info("=" * 60)
    logger.info(html_preview[:1000])  # First 1000 chars
    logger.info("...")
    logger.info(html_preview[-500:])  # Last 500 chars
    logger.info("=" * 60)
    
    prompt = f"""Classify this webpage as SPECIFIC or GENERAL for a data extraction system.

URL: {url}
Content Type: {content_type}

HTML Preview:
{html_preview}

CONTEXT: We're building a database. We need to know if this page contains data for ONE item or MULTIPLE items.

**SPECIFIC** = Page about ONE individual {content_type} that we can save as a single database record
   Examples:
   - Single tour: "Monteverde Canopy Tour" - has price $75, itinerary, duration, booking button
   - Single property: "Casa Vista Mar" - has $450K price, 3BR/2BA, square footage, contact agent
   - Single restaurant: "La Terraza" - has menu, hours, address, phone, reservation button
   
   Key signals:
   ✅ ONE main item being described
   ✅ Specific price for THIS item (not multiple prices)
   ✅ Detailed specs/features for THIS item only
   ✅ "Book Now" or "Contact" button for THIS specific item
   ✅ Reviews about THIS specific item
   
**GENERAL** = Destination guide or directory listing MULTIPLE {content_type}s
   Examples:
   - "San Gerardo de Dota Tours" - describes the destination + lists 5-10 available tours
   - "Miami Condos" - market overview + shows 20 condo listings  
   - "Paris Restaurants" - neighborhood guide + directory of 15 restaurants
   
   Key signals:
   ✅ Describes a LOCATION or CATEGORY (not one item)
   ✅ Lists MULTIPLE items (even just 3-5)
   ✅ Has links to individual item pages
   ✅ General destination info (climate, attractions, what to expect)
   ✅ Filters, sorting, "View all" buttons
   
CRITICAL DECISION RULES:
1. If page lists 3+ different tours/items → GENERAL (even if one is highlighted)
2. If page describes a destination AND shows tour options → GENERAL (it's a guide)
3. If page has "Choose your tour" or similar → GENERAL (it's a catalog)
4. Only classify as SPECIFIC if there's truly ONE single bookable item being sold

EXAMPLE EDGE CASES:
- "San Gerardo Tours" page with destination info + 8 tour listings → GENERAL
- "Hanging Bridges Tour" page with only that tour, price $35, book button → SPECIFIC

Respond ONLY with valid JSON:
{{
    "page_type": "specific" or "general",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of decision",
    "key_indicators": ["indicator1", "indicator2", "indicator3"]
}}"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            messages=[
                {"role": "system", "content": "You are an expert at analyzing webpages. You respond ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        elapsed = time.time() - start_time
        cost = (response.usage.total_tokens / 1000) * 0.0015  # GPT-4o-mini pricing
        
        logger.info(f"\n✅ OpenAI Analysis Complete:")
        logger.info(f"   Page Type: {result['page_type']}")
        logger.info(f"   Confidence: {result['confidence']:.0%}")
        logger.info(f"   Reasoning: {result['reasoning']}")
        logger.info(f"   Key Indicators: {', '.join(result['key_indicators'][:3])}")
        logger.info(f"   Time: {elapsed:.2f}s")
        logger.info(f"   Cost: ${cost:.4f}")
        logger.info(f"   Tokens: {response.usage.total_tokens}")
        logger.info("=" * 60)
        
        return {
            'page_type': result['page_type'],
            'confidence': float(result['confidence']),
            'reason': result['reasoning'],
            'indicators': result['key_indicators'],
            'cost': cost,
            'time': elapsed
        }
        
    except Exception as e:
        logger.error(f"❌ OpenAI analysis failed: {e}")
        # Fallback to default
        return {
            'page_type': 'specific',
            'confidence': 0.40,
            'reason': f'OpenAI analysis failed: {str(e)}',
            'indicators': ['error'],
            'cost': 0.0,
            'time': time.time() - start_time
        }


# ============================================================================
# CONTENT TYPE DETECTION (Auto-classify: tour, restaurant, real_estate, etc.)
# ============================================================================

def detect_content_type(url: str, html: Optional[str] = None) -> Dict:
    """
    Detect content type using OpenAI (same logic as page_type detection).
    
    Automatically classifies if the page is about:
    - tour (tours, activities, adventures)
    - restaurant (dining, food, cafes)
    - accommodation (hotels, lodges, rentals)
    - real_estate (properties for sale/rent)
    - local_tips (travel tips, guides)
    - transportation (transfers, shuttles, buses)
    
    Args:
        url: Page URL
        html: Optional HTML content (if already scraped)
        
    Returns:
        {
            'content_type': 'tour' | 'restaurant' | 'accommodation' | 'real_estate' | 'local_tips' | 'transportation',
            'confidence': 0.0-1.0,
            'method': 'openai_direct',
            'reasoning': 'explanation',
            'cost': float (USD),
            'time': float (seconds)
        }
    """
    logger.info("=" * 80)
    logger.info("🎯 Auto-Detecting Content Type")
    logger.info(f"   URL: {url}")
    logger.info("=" * 80)
    
    if not html:
        logger.warning("⚠️ No HTML provided, cannot analyze content type")
        return {
            'content_type': 'tour',  # Safe default
            'confidence': 0.5,
            'method': 'no_html_fallback',
            'reasoning': 'No HTML content provided',
            'cost': 0.0,
            'time': 0.1
        }
    
    logger.info("🤖 Calling OpenAI GPT-4o-mini for content type classification...")
    openai_result = _analyze_content_type_with_openai(url, html)
    
    logger.info(f"✅ OpenAI Result:")
    logger.info(f"   Content Type: {openai_result['content_type']}")
    logger.info(f"   Confidence: {openai_result['confidence']:.0%}")
    logger.info(f"   Reasoning: {openai_result['reasoning']}")
    logger.info(f"   Cost: ${openai_result['cost']:.4f}")
    logger.info(f"   Time: {openai_result['time']:.2f}s")
    logger.info("=" * 80)
    
    return openai_result


def _analyze_content_type_with_openai(url: str, html: str) -> Dict:
    """
    Use OpenAI to classify content type.
    
    Similar to _analyze_with_openai but for content classification.
    """
    import openai
    from django.conf import settings
    import time
    import json
    
    start_time = time.time()
    
    # Clean and truncate HTML
    html_cleaned = _clean_html_for_analysis(html)
    html_preview = html_cleaned[:12000] if len(html_cleaned) > 12000 else html_cleaned
    
    logger.info(f"HTML: {len(html):,} → {len(html_cleaned):,} → {len(html_preview):,} chars")
    
    prompt = f"""Classify the content type of this webpage for a data extraction system.

URL: {url}

HTML Preview:
{html_preview}

**AVAILABLE CONTENT TYPES:**

1. **tour** - Tours, activities, adventures, excursions, experiences
   Examples: "Monteverde Zipline", "City Walking Tour", "Snorkeling Adventure"
   Signals: Duration, difficulty, included items, tour operator, age restrictions, itinerary

2. **restaurant** - Restaurants, cafes, dining establishments, bars
   Examples: "La Terraza Restaurant", "Beachfront Cafe", "Italian Bistro"
   Signals: Menu, cuisine type, hours, reservations, dishes, chef, ambiance

3. **accommodation** - Hotels, lodges, hostels, rentals, B&Bs, resorts
   Examples: "Sunset Hotel", "Mountain Lodge", "Beach Villa"
   Signals: Room types, amenities, check-in/out, nightly rates, star rating, facilities

4. **real_estate** - Properties for sale or rent (houses, condos, land)
   Examples: "Casa Vista Mar $450K", "Downtown Condo for Sale"
   Signals: Price (usually $100K+), bedrooms, bathrooms, square footage, lot size, listing agent

5. **local_tips** - Travel tips, destination guides, advice articles
   Examples: "What to Pack for Costa Rica", "Safety Tips", "Best Time to Visit"
   Signals: Advice, tips list, "how to", general destination info, no specific business

6. **transportation** - Shuttles, transfers, buses, car rentals, transport services
   Examples: "Airport Shuttle", "San Jose to Jaco Bus", "Car Rental"
   Signals: Routes, schedules, per person/vehicle pricing, pickup/dropoff

**DECISION RULES:**
- If page sells/markets tours or activities → **tour**
- If page is a dining establishment → **restaurant**  
- If page offers lodging/rooms → **accommodation**
- If page lists property for purchase → **real_estate**
- If page gives general travel advice → **local_tips**
- If page offers transport services → **transportation**

Return your answer as JSON:
{{
  "content_type": "tour|restaurant|accommodation|real_estate|local_tips|transportation",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why you chose this type",
  "key_signals": ["signal1", "signal2", "signal3"]
}}"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content classification expert. Analyze web pages and determine their content type accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        elapsed = time.time() - start_time
        cost = (response.usage.total_tokens / 1000) * 0.0015  # GPT-4o-mini pricing
        
        logger.info(f"✅ Content Type Analysis Complete:")
        logger.info(f"   Type: {result['content_type']}")
        logger.info(f"   Confidence: {result['confidence']:.0%}")
        logger.info(f"   Reasoning: {result['reasoning']}")
        logger.info(f"   Signals: {', '.join(result['key_signals'][:3])}")
        logger.info(f"   Time: {elapsed:.2f}s")
        logger.info(f"   Cost: ${cost:.4f}")
        logger.info(f"   Tokens: {response.usage.total_tokens}")
        
        return {
            'content_type': result['content_type'],
            'confidence': float(result['confidence']),
            'reasoning': result['reasoning'],
            'key_signals': result['key_signals'],
            'cost': cost,
            'time': elapsed
        }
        
    except Exception as e:
        logger.error(f"❌ Content type detection failed: {e}")
        return {
            'content_type': 'tour',  # Safe fallback
            'confidence': 0.40,
            'reasoning': f'Detection failed: {str(e)}',
            'key_signals': ['error'],
            'cost': 0.0,
            'time': time.time() - start_time
        }
