#!/usr/bin/env python3
"""Test full extraction with new _clean_content improvements"""

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
print("🧪 TESTING FULL EXTRACTION WITH IMPROVED _clean_content")
print("=" * 80)
print(f"\nURL: {test_url}")
print("\n" + "=" * 80)

# Step 1: Scrape
print("📥 Step 1: Scraping...")
scraped = scrape_url(test_url)
if not scraped.get('success'):
    print("❌ Scraping failed!")
    sys.exit(1)

html = scraped.get('html', '')
print(f"✅ Got {len(html):,} characters of HTML")

# Step 1.5: Show cleaned content that goes to LLM
print("\n🧹 Step 1.5: Cleaning content for LLM...")
print("=" * 80)
extractor = PropertyExtractor(content_type='tour', page_type='specific')
cleaned_content = extractor._clean_content(html)
print(f"✅ Cleaned content: {len(cleaned_content):,} characters")
print("\n📄 CLEANED CONTENT PREVIEW (first 2000 chars):")
print("-" * 80)
print(cleaned_content[:2000])
print("-" * 80)
print("\n📄 CLEANED CONTENT PREVIEW (chars 5000-7000):")
print("-" * 80)
print(cleaned_content[5000:7000])
print("-" * 80)
print("\n📄 CLEANED CONTENT PREVIEW (last 1000 chars):")
print("-" * 80)
print(cleaned_content[-1000:])
print("-" * 80)

# Export cleaned content to file for full inspection
cleaned_file = '/Users/1di/kp-real-estate-llm-prototype/test_cleaned_content.txt'
with open(cleaned_file, 'w', encoding='utf-8') as f:
    f.write(cleaned_content)
print(f"\n💾 Full cleaned content saved to: {cleaned_file}")

# Step 2: Extract
print("\n📊 Step 2: Extracting with LLM...")
print("=" * 80)
extracted = extract_content_data(html, content_type='tour', page_type='specific', url=test_url)

# Step 3: Display results
print("\n" + "=" * 80)
print("✅ EXTRACTION RESULTS")
print("=" * 80)

# Core fields
print(f"\n🏷️  BASIC INFO:")
print(f"   Tour Name: {extracted.get('property_name', 'N/A')}")
print(f"   Tour Type: {extracted.get('property_type', 'N/A')}")
print(f"   Location: {extracted.get('location', 'N/A')}")
print(f"   Description: {extracted.get('description', 'N/A')[:100]}...")

# Pricing
print(f"\n💰 PRICING:")
print(f"   Price USD: ${extracted.get('price_usd', 'N/A')}")

# Tour-specific fields (should be in extracted data if detected properly)
tour_fields = [
    'duration_hours', 'difficulty_level', 'included_items', 'excluded_items',
    'max_participants', 'languages_available', 'pickup_included', 
    'minimum_age', 'cancellation_policy'
]

print(f"\n🎯 TOUR-SPECIFIC FIELDS:")
for field in tour_fields:
    value = extracted.get(field, 'N/A')
    if isinstance(value, list):
        value = ', '.join(str(v) for v in value[:3])
    print(f"   {field}: {value}")

# Metadata
print(f"\n📈 METADATA:")
print(f"   Extraction Confidence: {extracted.get('extraction_confidence', 0):.0%}")
print(f"   Content Type: {extracted.get('content_type', 'N/A')}")
print(f"   Page Type: {extracted.get('page_type', 'N/A')}")
print(f"   Tokens Used: {extracted.get('tokens_used', 'N/A')}")

# Count filled fields
filled_fields = sum(1 for k, v in extracted.items() 
                   if v not in [None, '', [], {}, 'N/A'] 
                   and not k.endswith('_evidence')
                   and k not in ['raw_html', 'field_confidence', 'extracted_at', 'tokens_used'])
total_fields = len([k for k in extracted.keys() 
                   if not k.endswith('_evidence') 
                   and k not in ['raw_html', 'field_confidence', 'extracted_at', 'tokens_used']])

print(f"\n📊 COVERAGE:")
print(f"   Filled fields: {filled_fields}/{total_fields} ({filled_fields/total_fields*100:.0f}%)")

# List all non-null fields
print(f"\n✅ ALL NON-NULL FIELDS:")
for key, value in sorted(extracted.items()):
    if not key.endswith('_evidence') and key not in ['raw_html', 'field_confidence', 'extracted_at']:
        if value not in [None, '', [], {}]:
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"   • {key}: {value}")

print("\n" + "=" * 80)
print("🏁 TEST COMPLETE")
print("=" * 80)

# Export full result to JSON for inspection
output_file = '/Users/1di/kp-real-estate-llm-prototype/test_extraction_output.json'
with open(output_file, 'w') as f:
    # Remove raw_html to make it readable
    export_data = {k: v for k, v in extracted.items() if k != 'raw_html'}
    json.dump(export_data, f, indent=2, default=str)
print(f"\n💾 Full results saved to: {output_file}")
