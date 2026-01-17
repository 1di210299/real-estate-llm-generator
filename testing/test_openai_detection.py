"""
Test Level 3 OpenAI detection for edge cases.
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
from core.llm.content_detection import detect_content_type
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_with_openai(url, expected_type, description):
    """Test a single URL with OpenAI Level 3."""
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {description}")
    print(f"URL: {url}")
    print(f"Expected: {expected_type}")
    print(f"{'='*80}\n")
    
    try:
        # Scrape
        print("📥 Scraping URL...")
        scrape_result = scrape_url(url)
        
        if not scrape_result['success']:
            print(f"❌ Scraping failed: {scrape_result.get('error', 'Unknown error')}")
            return False
        
        html = scrape_result['html']
        print(f"✅ Scraped {len(html):,} characters\n")
        
        # Detect content type
        content_detection = detect_content_type(url=url, html=html, user_override=None, use_llm_fallback=False)
        detected_content_type = content_detection['content_type']
        print(f"📋 Content Type: {detected_content_type}\n")
        
        # Detect page type (will use Level 3 if confidence < 65%)
        result = detect_page_type(url=url, html=html, content_type=detected_content_type)
        
        # Display results
        print(f"\n{'='*80}")
        print(f"📊 FINAL RESULTS:")
        print(f"{'='*80}")
        print(f"   Page Type: {result['page_type']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Method: {result['method']}")
        print(f"   Cost: ${result.get('cost', 0):.4f}")
        print(f"   Time: {result.get('time', 0):.2f}s")
        
        if result.get('indicators'):
            print(f"\n   Reasoning:")
            for i, indicator in enumerate(result['indicators'][:5], 1):
                print(f"      {i}. {indicator}")
        
        # Check result
        success = result['page_type'] == expected_type
        
        print(f"\n{'='*80}")
        if success:
            print(f"✅ TEST PASSED: Correctly detected as '{result['page_type']}'")
        else:
            print(f"❌ TEST FAILED: Expected '{expected_type}' but got '{result['page_type']}'")
        print(f"{'='*80}\n")
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run OpenAI detection tests on edge cases."""
    
    print("\n" + "="*80)
    print("🤖 LEVEL 3 OpenAI DETECTION TEST SUITE")
    print("Testing edge cases where Level 1+2 struggle")
    print("="*80)
    
    tests = [
        # The problematic case from before
        {
            'url': 'https://skyadventures.travel/tickets/',
            'expected': 'general',
            'description': 'Sky Adventures - Tickets page (was failing at Level 2)'
        },
        
        # Another potential edge case
        {
            'url': 'https://www.desafiocostarica.com/',
            'expected': 'general',
            'description': 'Desafío homepage - Multiple tours'
        },
        
        # Clear specific case for comparison
        {
            'url': 'https://www.desafiocostarica.com/tour-detail/rafting-balsa-river-costa-rica-2-3',
            'expected': 'specific',
            'description': 'Desafío - Specific tour (should still be fast at Level 1/2)'
        },
    ]
    
    results = []
    total_cost = 0.0
    total_time = 0.0
    
    for i, test in enumerate(tests, 1):
        print(f"\n\n{'#'*80}")
        print(f"TEST {i}/{len(tests)}")
        print(f"{'#'*80}")
        
        success = test_with_openai(
            url=test['url'],
            expected_type=test['expected'],
            description=test['description']
        )
        
        results.append({
            'test': test['description'],
            'success': success
        })
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}\n")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {passed/len(results)*100:.1f}%")
    
    print(f"\n{'='*80}")
    print("DETAILED RESULTS:")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status} - {result['test']}")
    
    return passed == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
