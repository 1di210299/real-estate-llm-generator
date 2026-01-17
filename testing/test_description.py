#!/usr/bin/env python3
"""Test description extraction length"""

import sys
import os
sys.path.insert(0, '/Users/1di/kp-real-estate-llm-prototype/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.extraction import extract_content_data, PropertyExtractor
from core.scraping.scraper import scrape_url
import json

# Test URL
test_url = 'https://skyadventures.travel/hanging-bridges/'

print("=" * 80)
print("🧪 TESTING DESCRIPTION EXTRACTION")
print("=" * 80)

# Step 1: Scrape
print("\n📥 Scraping...")
scraped = scrape_url(test_url)
if not scraped.get('success'):
    print("❌ Scraping failed!")
    sys.exit(1)

html = scraped.get('html', '')
print(f"✅ Got {len(html):,} characters of HTML")

# Step 2: Extract
print("\n🔍 Extracting...")
extractor = PropertyExtractor(content_type='tour', page_type='specific')
result = extractor.extract_from_html(html, test_url)

# Step 3: Show description
print("\n" + "=" * 80)
print("📝 DESCRIPTION FIELD")
print("=" * 80)

if result.get('description'):
    desc = result['description']
    print(f"\n✅ Description Length: {len(desc)} characters")
    print(f"✅ Word Count: {len(desc.split())} words")
    print("\n📄 FULL DESCRIPTION:")
    print("-" * 80)
    print(desc)
    print("-" * 80)
else:
    print("❌ No description found!")

print("\n" + "=" * 80)
