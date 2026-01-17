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


def detect_page_type(url: str, html: Optional[str] = None, content_type: str = 'tour') -> Dict:
    """
    Cascading detection of page type (specific vs general).
    
    Args:
        url: Page URL
        html: Optional HTML content (if already scraped)
        content_type: Type of content (tour, restaurant, real_estate, etc.)
        
    Returns:
        {
            'page_type': 'specific' | 'general',
            'confidence': 0.0-1.0,
            'method': 'url_pattern' | 'preview_llm' | 'openai_browsing',
            'indicators': [list of reasons],
            'cost': float (USD),
            'time': float (seconds)
        }
    """
    logger.info("=" * 80)
    logger.info("🔍 Starting cascading page type detection")
    logger.info(f"   URL: {url}")
    logger.info(f"   Content type: {content_type}")
    logger.info("=" * 80)
    
    # ========================================================================
    # LEVEL 1: URL PATTERN ANALYSIS (Free, Instant)
    # ========================================================================
    logger.info("📍 LEVEL 1: Analyzing URL patterns...")
    
    url_result = _analyze_url_patterns(url, content_type)
    logger.info(f"   Result: {url_result['page_type']}")
    logger.info(f"   Confidence: {url_result['confidence']:.0%}")
    logger.info(f"   Reason: {url_result['reason']}")
    
    if url_result['confidence'] >= 0.90:
        logger.info(f"✅ HIGH CONFIDENCE from URL pattern - STOPPING CASCADE")
        return {
            'page_type': url_result['page_type'],
            'confidence': url_result['confidence'],
            'method': 'url_pattern',
            'indicators': [url_result['reason']],
            'cost': 0.0,
            'time': 0.1
        }
    
    logger.info(f"⚠️ LOW/MEDIUM confidence from URL - CONTINUING TO LEVEL 2...")
    logger.info("")
    
    # ========================================================================
    # LEVEL 2: HTML PREVIEW + LLM VALIDATION (Cheap, Fast)
    # ========================================================================
    logger.info("📊 LEVEL 2: Analyzing HTML preview with LLM...")
    
    if not html:
        logger.warning("⚠️ No HTML provided, cannot do Level 2 validation")
        logger.info(f"   Using Level 1 result with lower confidence")
        return {
            'page_type': url_result['page_type'],
            'confidence': url_result['confidence'],
            'method': 'url_pattern_only',
            'indicators': [url_result['reason'], 'No HTML for deeper validation'],
            'cost': 0.0,
            'time': 0.1
        }
    
    # Analyze HTML structure
    html_result = _analyze_html_structure(html, content_type)
    logger.info(f"   Result: {html_result['page_type']}")
    logger.info(f"   Confidence: {html_result['confidence']:.0%}")
    logger.info(f"   Reason: {html_result['reason']}")
    logger.info("")
    
    # Combine URL + HTML signals
    logger.info("🔀 COMBINING SIGNALS:")
    logger.info(f"   URL says: {url_result['page_type']} ({url_result['confidence']:.0%})")
    logger.info(f"   HTML says: {html_result['page_type']} ({html_result['confidence']:.0%})")
    
    combined_confidence = (url_result['confidence'] * 0.4) + (html_result['confidence'] * 0.6)
    
    # Determine page type (weighted vote)
    url_weight = url_result['confidence']
    html_weight = html_result['confidence']
    
    if url_result['page_type'] == html_result['page_type']:
        # Agreement = high confidence
        final_type = url_result['page_type']
        final_confidence = min(0.95, combined_confidence + 0.15)  # Bonus for agreement
        agreement = "✅ Both URL and HTML agree"
        logger.info(f"   {agreement} → {final_type}")
    else:
        # Disagreement = trust the stronger signal
        # In case of tie, prefer HTML (more info than URL)
        if html_weight > url_weight:
            final_type = html_result['page_type']
            final_confidence = html_result['confidence']
            agreement = "⚠️ HTML signal stronger than URL"
            logger.info(f"   {agreement} → Using HTML: {final_type}")
        elif url_weight > html_weight:
            final_type = url_result['page_type']
            final_confidence = url_result['confidence']
            agreement = "⚠️ URL signal stronger than HTML"
            logger.info(f"   {agreement} → Using URL: {final_type}")
        else:
            # Perfect tie - prefer HTML as it has more actual content
            final_type = html_result['page_type']
            final_confidence = html_result['confidence'] * 0.9  # Slight penalty for uncertainty
            agreement = "⚠️ TIE - preferring HTML (more information)"
            logger.info(f"   {agreement} → Using HTML: {final_type}")
    
    logger.info(f"   Final confidence: {final_confidence:.0%}")
    logger.info("")
    
    # ========================================================================
    # LEVEL 3: Check if we need OpenAI validation (low/medium confidence)
    # ========================================================================
    if final_confidence < 0.80:
        logger.info(f"⚠️ LOW/MEDIUM CONFIDENCE ({final_confidence:.0%}) - ESCALATING TO LEVEL 3...")
        logger.info("")
        
        openai_result = _analyze_with_openai(url, html, content_type)
        
        # Combine Level 2 + Level 3 (give more weight to OpenAI)
        if openai_result['page_type'] == final_type:
            # Agreement with OpenAI = boost confidence
            logger.info(f"✅ OpenAI AGREES with Level 2 → {final_type}")
            final_confidence = min(0.95, openai_result['confidence'])
            method = 'url_html_openai_agreed'
        else:
            # Disagreement = trust OpenAI (it saw the actual content)
            logger.info(f"⚠️ OpenAI DISAGREES: Level 2={final_type}, OpenAI={openai_result['page_type']}")
            logger.info(f"   → Using OpenAI result (more reliable)")
            final_type = openai_result['page_type']
            final_confidence = openai_result['confidence']
            method = 'url_html_openai_override'
        
        indicators = [
            url_result['reason'],
            html_result['reason'],
            f"OpenAI: {openai_result['reason']}"
        ]
        
        return {
            'page_type': final_type,
            'confidence': final_confidence,
            'method': method,
            'indicators': indicators,
            'cost': openai_result['cost'],
            'time': 0.5 + openai_result['time']
        }
    
    # High confidence from Level 2 - no need for Level 3
    indicators = [
        url_result['reason'],
        html_result['reason'],
        agreement
    ]
    
    logger.info(f"✅ LEVEL 2 Complete - HIGH CONFIDENCE, skipping Level 3")
    logger.info(f"   Decision: {final_type}")
    logger.info(f"   Confidence: {final_confidence:.0%}")
    logger.info(f"   Combined from: URL ({url_result['confidence']:.0%}) + HTML ({html_result['confidence']:.0%})")
    
    return {
        'page_type': final_type,
        'confidence': final_confidence,
        'method': 'url_html_combined',
        'indicators': indicators,
        'cost': 0.0,  # No LLM call
        'time': 0.5   # Quick HTML analysis
    }


# ============================================================================
# LEVEL 1: URL PATTERN ANALYSIS
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
# LEVEL 2: HTML STRUCTURE ANALYSIS
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
        specific_score += 3
        indicators.append(f'Found {booking_found} booking elements')
        logger.info(f"   ✅ SPECIFIC indicator: Multiple booking elements (score +3)")
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
    
    # Truncate HTML to reasonable size (first 8000 chars usually has the key info)
    html_preview = html[:8000] if len(html) > 8000 else html
    
    logger.info(f"Analyzing {len(html_preview):,} characters with OpenAI...")
    logger.info(f"Content type: {content_type}")
    
    prompt = f"""Analyze this webpage and determine if it's a SPECIFIC item page or a GENERAL listing/guide page.

URL: {url}
Content Type: {content_type}

HTML Preview:
{html_preview}

Determine:
1. Is this a SPECIFIC page (single {content_type} item with full details)?
   - Examples: Single tour details, one restaurant page, one property listing
   - Indicators: "Book Now" button, detailed description, single price, reviews for ONE item
   
2. Or is this a GENERAL page (multiple items, guide, or category listing)?
   - Examples: List of tours, restaurant directory, property search results
   - Indicators: Multiple cards/items, filters, pagination, "Browse", "View all"

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
