#!/usr/bin/env python3
"""Test new OpenAI-direct page type detection"""

import sys
import os
sys.path.insert(0, '/Users/1di/kp-real-estate-llm-prototype/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from core.llm.page_type_detection import detect_page_type
import httpx

# Test cases
test_urls = [
    {
        'url': 'https://skyadventures.travel/hanging-bridges/',
        'expected': 'specific',
        'reason': 'Single tour with booking'
    },
    {
        'url': 'https://costarica.org/tours/san-gerardo-de-dota/',
        'expected': 'general',
        'reason': 'Destination guide page'
    },
    {
        'url': 'https://costarica.org/tours/',
        'expected': 'general',
        'reason': 'Tours listing page'
    }
]

print("=" * 80)
print("🧪 TESTING NEW OPENAI-DIRECT PAGE DETECTION")
print("=" * 80)

results = {'pass': 0, 'fail': 0, 'error': 0}

for i, test in enumerate(test_urls, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/3: {test['url']}")
    print(f"Expected: {test['expected']} ({test['reason']})")
    print(f"{'='*80}")
    
    try:
        # Scrape with httpx directly
        print("�� Scraping...")
        response = httpx.get(test['url'], follow_redirects=True, timeout=10)
        html = response.text
        print(f"✅ Got {len(html):,} characters")
        
        # Detect
        print("🤖 Detecting with OpenAI...")
        detection = detect_page_type(test['url'], html, 'tour')  # ✅ FIXED: url, html, content_type
        
        # Results
        detected = detection['page_type']
        confidence = detection['confidence']
        method = detection['method']
        
        success = "✅" if detected == test['expected'] else "❌"
        print(f"\n{success} RESULT:")
        print(f"   Detected: {detected}")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Method: {method}")
        print(f"   Expected: {test['expected']}")
        
        if detected == test['expected']:
            print(f"   ✅ PASS - Correct classification!")
            results['pass'] += 1
        else:
            print(f"   ❌ FAIL - Expected {test['expected']}, got {detected}")
            results['fail'] += 1
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results['error'] += 1

print(f"\n{'='*80}")
print("🏁 TESTS COMPLETE")
print(f"✅ Pass: {results['pass']}")
print(f"❌ Fail: {results['fail']}")
print(f"⚠️  Error: {results['error']}")
print("="*80)
