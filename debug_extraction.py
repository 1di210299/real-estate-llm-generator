#!/usr/bin/env python3
"""
Debug script to trace exactly where guide fields are lost during extraction.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.scraping.scraper import scrape_url
from core.llm.extraction import extract_content_data
from core.llm.page_type_detection import detect_page_type
from core.llm.content_detection import detect_content_type

def debug_extraction(url: str):
    """Debug extraction step by step."""
    
    print("=" * 80)
    print(f"🔍 DEBUG EXTRACTION: {url}")
    print("=" * 80)
    
    # Step 1: Scrape
    print("\n📥 STEP 1: Scraping...")
    scraped = scrape_url(url)
    html = scraped.get('html', '')
    print(f"   ✅ HTML size: {len(html)} chars")
    
    # Step 2: Detect content type
    print("\n🎯 STEP 2: Detecting content type...")
    content_detection = detect_content_type(url=url, html=html, use_llm_fallback=False)
    content_type = content_detection['content_type']
    print(f"   ✅ Content type: {content_type}")
    print(f"   ✅ Confidence: {content_detection['confidence']:.2%}")
    print(f"   ✅ Method: {content_detection['method']}")
    
    # Step 3: Detect page type
    print("\n📄 STEP 3: Detecting page type...")
    page_detection = detect_page_type(url=url, html=html, content_type=content_type)
    page_type = page_detection['page_type']
    print(f"   ✅ Page type: {page_type}")
    print(f"   ✅ Confidence: {page_detection['confidence']:.2%}")
    print(f"   ✅ Method: {page_detection['method']}")
    
    # Step 4: Extract data
    print("\n🤖 STEP 4: Extracting with LLM...")
    print(f"   Parameters: content_type={content_type}, page_type={page_type}")
    extracted = extract_content_data(
        content=html,
        content_type=content_type,
        page_type=page_type,
        url=url
    )
    
    print(f"\n📦 EXTRACTED DATA (after LLM):")
    print(f"   Total keys: {len(extracted.keys())}")
    print(f"   Keys: {list(extracted.keys())[:20]}")
    
    # Check for guide-specific fields
    guide_fields = [
        'destination', 'overview', 'property_types_available', 'tour_types_available',
        'price_range', 'featured_properties', 'featured_tours', 'market_trends'
    ]
    
    print(f"\n🔎 GUIDE FIELDS CHECK:")
    for field in guide_fields:
        if field in extracted:
            value = extracted[field]
            value_preview = str(value)[:100] if value else 'null'
            print(f"   ✅ {field}: {value_preview}")
        else:
            print(f"   ❌ {field}: NOT FOUND")
    
    # Step 5: Simulate evidence field removal
    print(f"\n🧹 STEP 5: Simulating evidence field removal...")
    evidence_fields = [key for key in list(extracted.keys()) if key.endswith('_evidence')]
    print(f"   Found {len(evidence_fields)} evidence fields to remove")
    
    extracted_copy = extracted.copy()
    for field in evidence_fields:
        extracted_copy.pop(field, None)
    
    print(f"   After removal: {len(extracted_copy.keys())} keys remain")
    
    # Check if guide fields survived
    print(f"\n🔎 GUIDE FIELDS AFTER EVIDENCE REMOVAL:")
    survived = 0
    for field in guide_fields:
        if field in extracted_copy:
            print(f"   ✅ {field}: SURVIVED")
            survived += 1
        else:
            print(f"   ❌ {field}: REMOVED")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Guide fields extracted: {sum(1 for f in guide_fields if f in extracted)}")
    print(f"   Guide fields survived cleaning: {survived}")
    print(f"   Loss: {sum(1 for f in guide_fields if f in extracted) - survived} fields")
    
    # Step 6: Check what validation does
    print(f"\n🔬 STEP 6: Checking PropertyExtractor validation...")
    from core.llm.extraction import PropertyExtractor
    extractor = PropertyExtractor(content_type=content_type, page_type=page_type)
    
    print(f"   Extractor initialized: content_type={extractor.content_type}, page_type={extractor.page_type}")
    
    try:
        validated = extractor._validate_extraction(extracted)
        print(f"   ✅ Validation complete")
        print(f"   Keys after validation: {len(validated.keys())}")
        print(f"   Keys: {list(validated.keys())[:20]}")
        
        print(f"\n🔎 GUIDE FIELDS AFTER VALIDATION:")
        for field in guide_fields:
            if field in validated:
                print(f"   ✅ {field}: SURVIVED VALIDATION")
            else:
                print(f"   ❌ {field}: REMOVED BY VALIDATION")
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 DEBUG COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    url = 'https://skyadventures.travel/tickets/'
    debug_extraction(url)
