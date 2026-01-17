#!/usr/bin/env python
"""
Test script for content type detection system.
Tests the hybrid detection approach with different URLs and content.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.llm.content_detection import detect_content_type, detect_by_domain, detect_by_keywords
from core.llm.content_types import get_all_content_types, CONTENT_TYPES


# ============================================================================
# TEST URLS
# ============================================================================

TEST_URLS = {
    'real_estate': [
        'https://www.coldwellbankercostarica.com/property/oceanview-villa-jaco',
        'https://www.brevitas.com/costa-rica/properties/12345',
        'https://www.encuentra24.com/costa-rica-es/bienes-raices-venta',
    ],
    'tour': [
        'https://www.viator.com/tours/Costa-Rica/Zip-Line-Adventure/d742-12345',
        'https://www.getyourguide.com/costa-rica-l123/zipline-tour-t98765',
        'https://www.tripadvisor.com/Attraction_Review-g309293-d123456',
    ],
    'restaurant': [
        'https://www.yelp.com/biz/restaurante-costarica',
        'https://www.tripadvisor.com/Restaurant_Review-g309293',
        'https://www.opentable.com/r/costa-rica-restaurant',
    ],
    'transportation': [
        'https://www.rome2rio.com/map/San-Jose/Jaco',
        'https://www.uber.com/cr/en/',
    ],
}


# Sample HTML for keyword testing
SAMPLE_HTML = {
    'real_estate': """
    <html>
        <head><title>Beautiful 3 Bedroom House for Sale</title></head>
        <body>
            <h1>Stunning Property in Jaco</h1>
            <div class="property-details">
                <p>Price: $250,000 USD</p>
                <p>3 bedrooms, 2 bathrooms</p>
                <p>Property size: 150 m² (1,615 sqft)</p>
                <p>Lot size: 500 m²</p>
                <p>This beautiful house for sale features modern amenities...</p>
            </div>
        </body>
    </html>
    """,
    'tour': """
    <html>
        <head><title>Zipline Canopy Tour Adventure</title></head>
        <body>
            <h1>Amazing Zipline Tour in Costa Rica</h1>
            <div class="tour-details">
                <p>Price: $85 per person</p>
                <p>Duration: 3 hours</p>
                <p>Difficulty: Moderate</p>
                <p>Includes: Pickup, guide, equipment, lunch</p>
                <p>Join our exciting zipline excursion through the rainforest...</p>
                <p>Maximum 12 participants per tour</p>
            </div>
        </body>
    </html>
    """,
    'restaurant': """
    <html>
        <head><title>El Pescador Seafood Restaurant</title></head>
        <body>
            <h1>El Pescador - Fine Dining</h1>
            <div class="restaurant-info">
                <p>Cuisine: Fresh Seafood & Costa Rican</p>
                <p>Price Range: $$-$$$</p>
                <p>Hours: 11am - 10pm daily</p>
                <p>Reservations recommended</p>
                <p>Signature dishes: Grilled Mahi-Mahi, Ceviche, Casado</p>
                <p>Menu available online. Beachfront dining with stunning views.</p>
            </div>
        </body>
    </html>
    """,
}


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def test_available_content_types():
    """Test: List all available content types."""
    print_header("Available Content Types")
    
    types = get_all_content_types()
    for ct in types:
        print(f"{ct['icon']} {ct['label']}")
        print(f"   Key: {ct['key']}")
        print(f"   Description: {ct['description']}")
        print()


def test_domain_detection():
    """Test: Domain-based detection."""
    print_header("Domain Detection Tests")
    
    for content_type, urls in TEST_URLS.items():
        print(f"\n{CONTENT_TYPES[content_type]['icon']} Testing {content_type.upper()} URLs:")
        for url in urls:
            detected = detect_by_domain(url)
            status = "✅" if detected == content_type else "❌"
            print(f"  {status} {url}")
            print(f"      Detected: {detected}")


def test_keyword_detection():
    """Test: Keyword-based detection."""
    print_header("Keyword Detection Tests")
    
    for content_type, html in SAMPLE_HTML.items():
        print(f"\n{CONTENT_TYPES[content_type]['icon']} Testing {content_type.upper()} HTML:")
        detected_type, confidence = detect_by_keywords(html, min_confidence=0.3)
        status = "✅" if detected_type == content_type else "❌"
        print(f"  {status} Detected: {detected_type}")
        print(f"      Confidence: {confidence:.2%}")


def test_hybrid_detection():
    """Test: Full hybrid detection."""
    print_header("Hybrid Detection Tests")
    
    print("Testing with DOMAIN + KEYWORDS:\n")
    
    # Test 1: Domain match
    print("Test 1: Known domain (should use domain detection)")
    url = "https://www.coldwellbankercostarica.com/property/test"
    html = SAMPLE_HTML['real_estate']
    result = detect_content_type(url, html, use_llm_fallback=False)
    print(f"  URL: {url}")
    print(f"  Result: {result['content_type']}")
    print(f"  Method: {result['method']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print()
    
    # Test 2: Unknown domain, good keywords
    print("Test 2: Unknown domain but clear keywords (should use keywords)")
    url = "https://www.unknown-site.com/property"
    html = SAMPLE_HTML['tour']
    result = detect_content_type(url, html, use_llm_fallback=False)
    print(f"  URL: {url}")
    print(f"  Result: {result['content_type']}")
    print(f"  Method: {result['method']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print()
    
    # Test 3: User override
    print("Test 3: User override (should always win)")
    url = "https://www.viator.com/tours/zipline"
    html = SAMPLE_HTML['tour']
    result = detect_content_type(url, html, user_override='restaurant', use_llm_fallback=False)
    print(f"  URL: {url}")
    print(f"  User override: restaurant")
    print(f"  Result: {result['content_type']}")
    print(f"  Method: {result['method']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print()


def test_extraction_prompts():
    """Test: Show extraction prompts for each type."""
    print_header("Extraction Prompts Preview")
    
    from core.llm.content_types import get_extraction_prompt
    
    for content_type in CONTENT_TYPES.keys():
        prompt = get_extraction_prompt(content_type)
        preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        print(f"\n{CONTENT_TYPES[content_type]['icon']} {content_type.upper()}:")
        print(f"  Prompt length: {len(prompt)} chars")
        print(f"  Preview: {preview}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests."""
    print("\n")
    print("🧪 CONTENT TYPE DETECTION TEST SUITE")
    print("=" * 80)
    
    try:
        test_available_content_types()
        test_domain_detection()
        test_keyword_detection()
        test_hybrid_detection()
        test_extraction_prompts()
        
        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
