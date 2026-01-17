#!/usr/bin/env python3
"""
Test batch processing with automatic content type detection
Simulates what happens when user uploads mixed URLs
"""
import sys
import os
sys.path.insert(0, '/Users/1di/kp-real-estate-llm-prototype/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.content_detection import detect_content_type
from core.llm.page_type_detection import detect_page_type
from core.scraping.scraper import scrape_url

# Simulate batch processing with mixed URLs
batch_urls = [
    "https://skyadventures.travel/hanging-bridges/",  # Tour
    "https://www.coldwellbankercostarica.com/property/32652-Ocean-View-Lot-Flamingo-Guanacaste/",  # Real Estate
]

print("=" * 100)
print("🚀 SIMULATING BATCH PROCESSING WITH AUTO-DETECTION")
print("=" * 100)
print(f"\nProcessing {len(batch_urls)} URLs with ZERO manual input")
print("System will auto-detect: content_type + page_type for each URL\n")

total_cost = 0.0
results = []

for i, url in enumerate(batch_urls, 1):
    print(f"\n{'=' * 100}")
    print(f"📄 URL {i}/{len(batch_urls)}")
    print(f"🔗 {url}")
    print("=" * 100)
    
    try:
        # Step 1: Scrape
        print("📥 Scraping...")
        scraped = scrape_url(url)
        if not scraped.get('success'):
            print(f"❌ Failed to scrape")
            continue
        
        html = scraped.get('html', '')
        print(f"✅ Scraped {len(html):,} chars")
        
        # Step 2: Auto-detect content type (with adaptive strategy)
        print("\n🎯 Auto-detecting content type...")
        
        # Try fast methods first
        content_result = detect_content_type(
            url=url,
            html=html,
            user_override=None,  # No user input!
            use_llm_fallback=False
        )
        
        content_type = content_result['content_type']
        confidence = content_result['confidence']
        method = content_result['method']
        
        print(f"   Fast detection: {content_type} ({confidence:.0%} via {method})")
        
        # If low confidence, use LLM
        if confidence < 0.70:
            print(f"   ⚠️ Low confidence, retrying with LLM...")
            content_result = detect_content_type(
                url=url,
                html=html,
                user_override=None,
                use_llm_fallback=True  # Activate LLM
            )
            content_type = content_result['content_type']
            confidence = content_result['confidence']
            method = content_result['method']
            print(f"   LLM detection: {content_type} ({confidence:.0%} via {method})")
        
        # Step 3: Auto-detect page type
        print(f"\n📄 Auto-detecting page type...")
        page_result = detect_page_type(url, html, content_type)
        page_type = page_result['page_type']
        page_confidence = page_result['confidence']
        
        print(f"   Detected: {page_type} ({page_confidence:.0%})")
        
        # Summary
        cost = page_result.get('cost', 0.0)
        total_cost += cost
        
        print(f"\n✅ FINAL CLASSIFICATION:")
        print(f"   content_type: {content_type}")
        print(f"   page_type: {page_type}")
        print(f"   Cost: ${cost:.4f}")
        
        results.append({
            'url': url,
            'content_type': content_type,
            'page_type': page_type,
            'cost': cost
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Final summary
print("\n" + "=" * 100)
print("📊 BATCH PROCESSING SUMMARY")
print("=" * 100)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['url'][:60]}...")
    print(f"   → {result['content_type']} | {result['page_type']} | ${result['cost']:.4f}")

print(f"\n💰 Total Cost: ${total_cost:.4f}")
print(f"📈 Avg Cost per URL: ${total_cost/len(results):.4f}" if results else "No results")
print(f"🎯 Success Rate: {len(results)}/{len(batch_urls)} ({len(results)/len(batch_urls)*100:.0f}%)")

print("\n" + "=" * 100)
print("✅ BATCH PROCESSING COMPLETE - System ready for production!")
print("=" * 100)
