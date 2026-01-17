"""
Test page type detection (specific vs general) for different URLs.
Tests the cascading detection system: URL patterns → HTML structure analysis.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.page_type_detection import detect_page_type
from core.scraping.scraper import scrape_url
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_url(url, expected_page_type, description):
    """Test page type detection for a URL."""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {description}")
    print(f"URL: {url}")
    print(f"Expected: {expected_page_type}")
    print(f"{'='*80}")
    
    try:
        # Scrape the URL
        print("\n📥 Scraping URL...")
        scrape_result = scrape_url(url)
        
        if not scrape_result['success']:
            print(f"❌ Scraping failed: {scrape_result.get('error', 'Unknown error')}")
            return False
        
        html = scrape_result['html']
        print(f"✅ Scraped {len(html)} characters")
        
        # Detect content type first (tours, real_estate, etc.)
        from core.llm.content_detection import detect_content_type
        content_detection = detect_content_type(url=url, html=html, user_override=None, use_llm_fallback=False)
        detected_content_type = content_detection['content_type']
        
        print(f"\n📋 Content Type: {detected_content_type}")
        
        # Detect page type
        print(f"\n🔍 Detecting page type...")
        result = detect_page_type(url=url, html=html, content_type=detected_content_type)
        
        # Display results
        print(f"\n📊 DETECTION RESULTS:")
        print(f"   Page Type: {result['page_type']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Method: {result['method']}")
        print(f"   Detection Time: {result.get('time_seconds', result.get('detection_time_seconds', 0)):.2f}s")
        print(f"   Cost: ${result.get('cost', result.get('detection_cost', 0)):.4f}")
        
        if result.get('indicators') and isinstance(result['indicators'], dict):
            print(f"\n   Indicators:")
            for key, value in result['indicators'].items():
                if value is not None:
                    print(f"      {key}: {value}")
        
        # Check if matches expected
        success = result['page_type'] == expected_page_type
        
        if success:
            print(f"\n✅ TEST PASSED: Detected '{result['page_type']}' as expected")
        else:
            print(f"\n❌ TEST FAILED: Expected '{expected_page_type}' but got '{result['page_type']}'")
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all page type detection tests."""
    
    print("\n" + "="*80)
    print("🎯 PAGE TYPE DETECTION TEST SUITE")
    print("="*80)
    
    tests = [
        # SPECIFIC TOUR PAGES (single tour details)
        {
            'url': 'https://www.viator.com/tours/Costa-Rica/Arenal-Volcano-and-Hot-Springs-Day-Trip/d742-3876SANJOSE',
            'expected': 'specific',
            'description': 'Viator - Specific tour (has d742-XXXX pattern)'
        },
        {
            'url': 'https://www.desafiocostarica.com/tour-detail/rafting-balsa-river-costa-rica-2-3',
            'expected': 'specific',
            'description': 'Desafío - Specific tour (has /tour-detail/ path)'
        },
        {
            'url': 'https://costarica.org/tours/arenal/',
            'expected': 'general',
            'description': 'CostaRica.org - Arenal tours guide (category page)'
        },
        
        # GENERAL TOUR PAGES (listings/guides)
        {
            'url': 'https://costarica.org/tours/',
            'expected': 'general',
            'description': 'CostaRica.org - All tours listing'
        },
        {
            'url': 'https://www.anywhere.com/costa-rica/tours',
            'expected': 'general',
            'description': 'Anywhere - Tours listing (plural /tours)'
        },
        {
            'url': 'https://www.desafiocostarica.com/',
            'expected': 'general',
            'description': 'Desafío - Homepage (likely has multiple tours)'
        },
        {
            'url': 'https://skyadventures.travel/tickets/',
            'expected': 'general',
            'description': 'Sky Adventures - Tickets page (multiple options)'
        },
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n\n{'#'*80}")
        print(f"TEST {i}/{len(tests)}")
        print(f"{'#'*80}")
        
        success = test_url(
            url=test['url'],
            expected_page_type=test['expected'],
            description=test['description']
        )
        
        results.append({
            'test': test['description'],
            'url': test['url'],
            'expected': test['expected'],
            'success': success
        })
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {passed/len(results)*100:.1f}%")
    
    print(f"\n{'='*80}")
    print("DETAILED RESULTS:")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status} - {result['test']}")
        print(f"   Expected: {result['expected']}")
        print(f"   URL: {result['url']}\n")
    
    return passed == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
