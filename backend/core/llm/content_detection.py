"""
Hybrid content type detection system.
Detects the type of content (real_estate, tour, restaurant, etc.) using multiple strategies.
"""

import logging
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .content_types import CONTENT_TYPES

logger = logging.getLogger(__name__)


# ============================================================================
# DETECTION STRATEGIES
# ============================================================================

def detect_by_domain(url: str) -> Optional[str]:
    """
    Detect content type by URL domain.
    
    Args:
        url: The URL to analyze
        
    Returns:
        Content type key or None if no match
    """
    if not url:
        return None
    
    try:
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix
        domain = domain.replace('www.', '')
        
        logger.info(f"🔍 Detecting by domain: {domain}")
        
        # Check each content type's domain list
        for content_type, config in CONTENT_TYPES.items():
            for domain_pattern in config['domains']:
                if domain_pattern.lower() in domain:
                    logger.info(f"✅ Domain match: {domain} → {content_type}")
                    return content_type
        
        logger.info(f"⚠️ No domain match for: {domain}")
        return None
        
    except Exception as e:
        logger.warning(f"Error parsing URL domain: {e}")
        return None


def detect_by_keywords(html: str, min_confidence: float = 0.5) -> Tuple[Optional[str], float]:
    """
    Detect content type by analyzing keywords in the HTML content.
    
    Args:
        html: HTML content to analyze
        min_confidence: Minimum confidence threshold (0.0 to 1.0)
        
    Returns:
        Tuple of (content_type, confidence_score) or (None, 0.0)
    """
    try:
        # Extract text from HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        text = soup.get_text().lower()
        
        logger.info(f"🔍 Detecting by keywords (text length: {len(text)} chars)")
        
        # Count keyword matches for each content type
        scores = {}
        for content_type, config in CONTENT_TYPES.items():
            keyword_matches = sum(1 for keyword in config['keywords'] if keyword.lower() in text)
            total_keywords = len(config['keywords'])
            
            # Calculate confidence as percentage of keywords found
            confidence = keyword_matches / total_keywords if total_keywords > 0 else 0.0
            scores[content_type] = {
                'matches': keyword_matches,
                'total': total_keywords,
                'confidence': confidence
            }
            
            logger.debug(f"  {content_type}: {keyword_matches}/{total_keywords} keywords ({confidence:.2%})")
        
        # Find the type with highest confidence
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1]['confidence'])
            content_type = best_type[0]
            confidence = best_type[1]['confidence']
            matches = best_type[1]['matches']
            
            logger.info(f"🏆 Best keyword match: {content_type} ({matches} keywords, {confidence:.2%} confidence)")
            
            if confidence >= min_confidence:
                logger.info(f"✅ Keyword confidence above threshold ({min_confidence:.2%})")
                return content_type, confidence
            else:
                logger.info(f"⚠️ Keyword confidence below threshold ({min_confidence:.2%})")
                return None, confidence
        
        return None, 0.0
        
    except Exception as e:
        logger.warning(f"Error in keyword detection: {e}")
        return None, 0.0


def classify_with_llm(html: str, url: str = "", client=None) -> Tuple[str, float]:
    """
    Classify content type using LLM (last resort).
    Uses the robust OpenAI-based detection from page_type_detection module.
    
    Args:
        html: HTML content to classify
        url: Source URL (optional but recommended)
        client: OpenAI client (optional, will create if not provided)
        
    Returns:
        Tuple of (content_type, confidence)
    """
    logger.info("🤖 Using advanced LLM content type detection...")
    
    try:
        # Import the robust detection function
        from core.llm.page_type_detection import detect_content_type as detect_ct_openai
        
        result = detect_ct_openai(url=url, html=html)
        
        content_type = result['content_type']
        confidence = result['confidence']
        
        logger.info(f"✅ LLM detected: {content_type} (confidence: {confidence:.2%})")
        
        return content_type, confidence
        
    except ImportError:
        logger.warning("⚠️ Advanced detection not available, using fallback...")
        # Fallback to simple method if module not available
        return _simple_llm_classify(html, client)
        
    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return 'real_estate', 0.3


def _simple_llm_classify(html: str, client=None) -> Tuple[str, float]:
    """Simple LLM classification fallback."""
    import openai
    from django.conf import settings
    
    if client is None:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        # Extract a preview of the content
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()
        text_preview = soup.get_text(separator=' ', strip=True)[:2000]  # First 2000 chars
        
        classification_prompt = f"""Classify the following web content into ONE category. Return ONLY the category key, nothing else.

Categories:
- real_estate (properties for sale/rent)
- tour (tours, activities, excursions)
- restaurant (restaurants, dining, food)
- accommodation (hotels, lodges, rentals)
- local_tips (travel tips, advice, local knowledge)
- transportation (buses, taxis, shuttles, routes)

Content preview:
{text_preview}

Category:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content classification expert. Return only the category key."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0,
            max_tokens=20
        )
        
        content_type = response.choices[0].message.content.strip().lower()
        
        # Validate that it's a known type
        if content_type in CONTENT_TYPES:
            logger.info(f"✅ LLM classified as: {content_type}")
            return content_type, 0.85  # High confidence for LLM classification
        else:
            logger.warning(f"⚠️ LLM returned unknown type: {content_type}, defaulting to real_estate")
            return 'real_estate', 0.5
            
    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return 'real_estate', 0.3


# ============================================================================
# MAIN DETECTION FUNCTION
# ============================================================================

def detect_content_type(
    url: str,
    html: str,
    user_override: Optional[str] = None,
    use_llm_fallback: bool = False
) -> Dict[str, any]:
    """
    Detect content type using hybrid approach.
    
    Detection strategy (in order):
    1. User override (if provided)
    2. Domain matching (fast, reliable)
    3. Keyword analysis (fast, fairly reliable)
    4. LLM classification (slow, expensive, but most accurate) - optional
    
    Args:
        url: Source URL
        html: HTML content
        user_override: User-specified content type (highest priority)
        use_llm_fallback: Whether to use LLM as last resort
        
    Returns:
        Dict with:
            - content_type: Detected type key
            - confidence: Confidence score (0.0 to 1.0)
            - method: Detection method used
            - suggested_type: Best guess for UI pre-selection
    """
    logger.info("=" * 80)
    logger.info("🔎 Starting hybrid content type detection")
    logger.info("=" * 80)
    
    # Strategy 1: User override (100% confidence)
    if user_override:
        if user_override in CONTENT_TYPES:
            logger.info(f"✅ Using user override: {user_override}")
            return {
                'content_type': user_override,
                'confidence': 1.0,
                'method': 'user_override',
                'suggested_type': user_override
            }
        else:
            logger.warning(f"⚠️ Invalid user override: {user_override}, ignoring")
    
    # Strategy 2: Domain detection (instant, reliable for known sites)
    domain_type = detect_by_domain(url)
    if domain_type:
        logger.info(f"✅ Domain detection successful: {domain_type}")
        return {
            'content_type': domain_type,
            'confidence': 0.95,
            'method': 'domain',
            'suggested_type': domain_type
        }
    
    # Strategy 3: Keyword analysis (fast, decent accuracy)
    keyword_type, keyword_confidence = detect_by_keywords(html, min_confidence=0.3)
    
    if keyword_type and keyword_confidence >= 0.7:
        # High confidence from keywords
        logger.info(f"✅ Keyword detection with high confidence: {keyword_type} ({keyword_confidence:.2%})")
        return {
            'content_type': keyword_type,
            'confidence': keyword_confidence,
            'method': 'keywords_high_confidence',
            'suggested_type': keyword_type
        }
    
    # Strategy 4: LLM classification (optional, slow but accurate)
    if use_llm_fallback:
        logger.info("🤖 Using LLM classification as fallback...")
        llm_type, llm_confidence = classify_with_llm(html, url=url)
        return {
            'content_type': llm_type,
            'confidence': llm_confidence,
            'method': 'llm',
            'suggested_type': llm_type
        }
    
    # Fallback: Use keyword detection with lower confidence or default
    if keyword_type:
        logger.info(f"⚠️ Using keyword detection with medium confidence: {keyword_type} ({keyword_confidence:.2%})")
        return {
            'content_type': keyword_type,
            'confidence': keyword_confidence,
            'method': 'keywords_medium_confidence',
            'suggested_type': keyword_type
        }
    
    # Ultimate fallback: real_estate (original purpose)
    logger.warning("⚠️ No detection method succeeded, defaulting to real_estate")
    return {
        'content_type': 'real_estate',
        'confidence': 0.3,
        'method': 'default_fallback',
        'suggested_type': 'real_estate'
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_content_type_label(content_type: str) -> str:
    """Get human-readable label for content type."""
    config = CONTENT_TYPES.get(content_type)
    return config['label'] if config else content_type


def get_content_type_icon(content_type: str) -> str:
    """Get icon for content type."""
    config = CONTENT_TYPES.get(content_type)
    return config['icon'] if config else '📄'
