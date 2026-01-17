#!/usr/bin/env python
"""
Test price extraction with multiple price categories
"""
import os
import sys
import django
import json

# Configure Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.scraping.scraper import scrape_url
from core.llm.extraction import PropertyExtractor

def test_price_extraction():
    """Test that price_details captures multiple price categories"""
    
    print("=" * 80)
    print("🧪 TESTING PRICE EXTRACTION WITH MULTIPLE CATEGORIES")
    print("=" * 80)
    
    # Test URL with multiple price categories
    test_url = "https://skyadventures.travel/hanging-bridges/"
    
    print(f"\n📍 URL: {test_url}")
    print("-" * 80)
    
    # Step 1: Scrape
    print("\n🌐 Step 1: Scraping...")
    scrape_result = scrape_url(test_url)
    html = scrape_result.get('html', '')
    print(f"✅ Got {len(html):,} characters")
    
    # Step 2: Extract with content_type = 'tour'
    print("\n🔍 Step 2: Extracting with PropertyExtractor...")
    extractor = PropertyExtractor(content_type='tour', page_type='specific')
    result = extractor.extract(html, test_url)
    
    # Step 3: Show results
    print("\n" + "=" * 80)
    print("📊 EXTRACTION RESULTS")
    print("=" * 80)
    
    print(f"\n🏷️  Tour Name: {result.get('tour_name', 'N/A')}")
    print(f"📍 Location: {result.get('location', 'N/A')}")
    
    print(f"\n💰 Price Fields:")
    print(f"   price_usd: ${result.get('price_usd', 'N/A')}")
    
    if result.get('price_details'):
        print(f"\n💳 Price Details (JSON):")
        price_details = result['price_details']
        print(json.dumps(price_details, indent=2))
        
        # Analyze coverage
        categories = ['adults', 'children', 'students', 'nationals', 'seniors', 'groups']
        filled = [cat for cat in categories if price_details.get(cat)]
        print(f"\n📈 Price Categories Found: {len(filled)}/{len(categories)}")
        for cat in filled:
            print(f"   ✅ {cat.capitalize()}: ${price_details[cat]}")
        
        if price_details.get('range'):
            print(f"\n📊 Price Range: {price_details['range']}")
        
        if price_details.get('note'):
            print(f"\n📝 Note: {price_details['note']}")
    else:
        print("   ❌ No price_details found")
    
    # Show evidence
    if result.get('price_evidence'):
        print(f"\n🔍 Evidence:")
        print(f"   {result['price_evidence'][:200]}...")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    
    return result

if __name__ == '__main__':
    test_price_extraction()
