"""
Test a single URL with detailed logging.
"""

import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.page_type_detection import detect_page_type
from core.scraping.scraper import scrape_url
from core.llm.content_detection import detect_content_type

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def test_single_url(url, expected):
    """Test a single URL with full logging."""
    print("\n" + "="*80)
    print(f"🧪 TESTING URL")
    print("="*80)
    print(f"URL: {url}")
    print(f"Expected: {expected}")
    print("="*80 + "\n")
    
    # Scrape
    print("📥 Scraping...")
    scrape_result = scrape_url(url)
    
    if not scrape_result['success']:
        print(f"❌ Scraping failed: {scrape_result.get('error')}")
        return
    
    html = scrape_result['html']
    print(f"✅ Scraped {len(html):,} characters\n")
    
    # Detect content type
    print("📋 Detecting content type...")
    content_detection = detect_content_type(url=url, html=html, user_override=None, use_llm_fallback=False)
    detected_content_type = content_detection['content_type']
    print(f"✅ Content type: {detected_content_type}\n")
    
    # Detect page type with full logging
    print("🔍 Detecting page type...\n")
    result = detect_page_type(url=url, html=html, content_type=detected_content_type)
    
    # Results
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    print(f"Page Type: {result['page_type']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Method: {result['method']}")
    print(f"Expected: {expected}")
    print(f"Match: {'✅ YES' if result['page_type'] == expected else '❌ NO'}")
    print("="*80)


if __name__ == '__main__':
    # Test the failing case
    test_single_url(
        url='https://skyadventures.travel/tickets/',
        expected='general'
    )
