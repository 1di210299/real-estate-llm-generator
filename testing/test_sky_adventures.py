"""
Quick test for Sky Adventures tickets page (the failing case).
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
logging.basicConfig(level=logging.INFO, format='%(message)s')

url = 'https://skyadventures.travel/tickets/'
print(f"\n🧪 Testing: {url}\n")

# Scrape
print("📥 Scraping...")
result = scrape_url(url)
html = result['html']
print(f"✅ Got {len(html):,} characters\n")

# Detect content type
content_detection = detect_content_type(url=url, html=html, user_override=None, use_llm_fallback=False)
content_type = content_detection['content_type']
print(f"📋 Content type: {content_type}\n")

# Detect page type
page_result = detect_page_type(url=url, html=html, content_type=content_type)

print(f"\n" + "=" * 80)
print(f"RESULT:")
print(f"  Page Type: {page_result['page_type']}")
print(f"  Confidence: {page_result['confidence']:.0%}")
print(f"  Method: {page_result['method']}")
print("=" * 80)
