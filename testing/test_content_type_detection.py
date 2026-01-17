#!/usr/bin/env python3
"""
Test automatic content type detection for batch processing
"""
import sys
import os
sys.path.insert(0, '/Users/1di/kp-real-estate-llm-prototype/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.page_type_detection import detect_content_type, detect_page_type
from core.scraping.scraper import scrape_url

# Test URLs from different content types
test_urls = [
    {
        'url': 'https://skyadventures.travel/hanging-bridges/',
        'expected_content': 'tour',
        'expected_page': 'specific',
        'description': 'Single tour page'
    },
    {
        'url': 'https://www.coldwellbankercostarica.com/property/32652-Ocean-View-Lot-Flamingo-Guanacaste/',
        'expected_content': 'real_estate',
        'expected_page': 'specific',
        'description': 'Real estate listing'
    },
    {
        'url': 'https://costarica.org/restaurants/',
        'expected_content': 'restaurant',
        'expected_page': 'general',
        'description': 'Restaurant directory'
    },
]

print("=" * 100)
print("🧪 TESTING AUTOMATIC CONTENT TYPE DETECTION FOR BATCH PROCESSING")
print("=" * 100)
print()
print("SCENARIO: User uploads 50 mixed URLs (tours, restaurants, properties)")
print("GOAL: Auto-classify each URL without manual input")
print("=" * 100)

total_cost = 0.0
results = []

for i, test in enumerate(test_urls, 1):
    print(f"\n{'=' * 100}")
    print(f"TEST {i}/{len(test_urls)}: {test['description']}")
    print(f"URL: {test['url']}")
    print(f"Expected: content_type={test['expected_content']}, page_type={test['expected_page']}")
    print("=" * 100)
    
    # Step 1: Scrape
    print("\n📥 Step 1: Scraping...")
    scraped = scrape_url(test['url'])
    if not scraped.get('success'):
        print("❌ Scraping failed!")
        continue
    
    html = scraped.get('html', '')
    print(f"✅ Got {len(html):,} characters")
    
    # Step 2: Detect Content Type (NEW!)
    print("\n🎯 Step 2: Auto-detecting content type...")
    content_result = detect_content_type(test['url'], html)
    
    detected_content = content_result['content_type']
    content_confidence = content_result['confidence']
    content_cost = content_result['cost']
    
    print(f"\n✅ CONTENT TYPE RESULT:")
    print(f"   Detected: {detected_content}")
    print(f"   Confidence: {content_confidence:.0%}")
    print(f"   Reasoning: {content_result['reasoning']}")
    print(f"   Cost: ${content_cost:.4f}")
    print(f"   Expected: {test['expected_content']}")
    
    content_match = detected_content == test['expected_content']
    if content_match:
        print(f"   ✅ PASS - Correct content type!")
    else:
        print(f"   ❌ FAIL - Expected {test['expected_content']}, got {detected_content}")
    
    # Step 3: Detect Page Type
    print("\n📄 Step 3: Detecting page type...")
    page_result = detect_page_type(test['url'], html, detected_content)
    
    detected_page = page_result['page_type']
    page_confidence = page_result['confidence']
    page_cost = page_result['cost']
    
    print(f"\n✅ PAGE TYPE RESULT:")
    print(f"   Detected: {detected_page}")
    print(f"   Confidence: {page_confidence:.0%}")
    print(f"   Cost: ${page_cost:.4f}")
    print(f"   Expected: {test['expected_page']}")
    
    page_match = detected_page == test['expected_page']
    if page_match:
        print(f"   ✅ PASS - Correct page type!")
    else:
        print(f"   ❌ FAIL - Expected {test['expected_page']}, got {detected_page}")
    
    # Summary
    test_cost = content_cost + page_cost
    total_cost += test_cost
    
    print(f"\n💰 TOTAL COST FOR THIS URL: ${test_cost:.4f}")
    
    results.append({
        'url': test['url'],
        'content_match': content_match,
        'page_match': page_match,
        'cost': test_cost
    })

# Final Summary
print("\n" + "=" * 100)
print("🏁 FINAL RESULTS")
print("=" * 100)

content_passes = sum(1 for r in results if r['content_match'])
page_passes = sum(1 for r in results if r['page_match'])
both_passes = sum(1 for r in results if r['content_match'] and r['page_match'])

print(f"\n📊 Accuracy:")
print(f"   Content Type: {content_passes}/{len(results)} ({content_passes/len(results)*100:.0f}%)")
print(f"   Page Type: {page_passes}/{len(results)} ({page_passes/len(results)*100:.0f}%)")
print(f"   Both Correct: {both_passes}/{len(results)} ({both_passes/len(results)*100:.0f}%)")

print(f"\n💰 Cost Analysis:")
print(f"   Total Cost: ${total_cost:.4f}")
print(f"   Avg per URL: ${total_cost/len(results):.4f}")
print(f"   Est. for 50 URLs: ${(total_cost/len(results))*50:.2f}")

print("\n" + "=" * 100)
if both_passes == len(results):
    print("✅ ALL TESTS PASSED - System ready for batch processing!")
else:
    print(f"⚠️  {len(results) - both_passes} tests failed - Review results above")
print("=" * 100)
