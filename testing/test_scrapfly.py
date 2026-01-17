#!/usr/bin/env python
"""
Test script for Scrapfly implementation
Run: python test_scrapfly.py
"""

import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from core.scraping.scraper import WebScraper


async def test_scrapfly():
    """Test Scrapfly scraping"""
    
    print("=" * 60)
    print("🧪 Testing Scrapfly Implementation")
    print("=" * 60)
    
    scraper = WebScraper()
    
    # Test 1: Simple site (should NOT use Scrapfly)
    print("\n1️⃣ Test: Simple site (httpbin.org)")
    print("-" * 60)
    try:
        result = await scraper.scrape('https://httpbin.org/html')
        print(f"✅ Success!")
        print(f"   Method: {result['method']}")
        print(f"   Title: {result['title'][:50]}")
        assert result['method'] != 'scrapfly', "Should not use Scrapfly for simple sites"
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Cloudflare-protected site (should use Scrapfly)
    print("\n2️⃣ Test: Cloudflare site (encuentra24.com)")
    print("-" * 60)
    try:
        result = await scraper.scrape('https://encuentra24.com/costa-rica-es/bienes-raices-venta-casas')
        print(f"✅ Success!")
        print(f"   Method: {result['method']}")
        print(f"   API Cost: {result.get('api_cost', 'N/A')} credits")
        print(f"   HTML length: {len(result['html'])} chars")
        print(f"   Title: {result['title'][:80]}")
        
        if result['method'] == 'scrapfly':
            print("   🎉 Scrapfly is working correctly!")
        else:
            print("   ⚠️  Warning: Not using Scrapfly (check API key)")
    except Exception as e:
        print(f"❌ Failed: {e}")
        print(f"   Note: If this is an API key error, add SCRAPFLY_API_KEY to .env")
    
    # Test 3: Check configuration
    print("\n3️⃣ Configuration Check")
    print("-" * 60)
    print(f"   Scrapfly Enabled: {scraper.scrapfly_enabled}")
    print(f"   Scrapfly Client: {'✅ Configured' if scraper.scrapfly_client else '❌ Not configured'}")
    print(f"   API Key: {'✅ Present' if scraper.scrapfly_api_key else '❌ Missing'}")
    print(f"   Residential Proxy: {'✅ Configured' if scraper.residential_proxy else '❌ Not configured'}")
    
    print("\n" + "=" * 60)
    print("🏁 Tests completed!")
    print("=" * 60)
    
    # Usage reminder
    print("\n📝 Next Steps:")
    print("   1. Add SCRAPFLY_API_KEY to your .env file")
    print("   2. Get your key from: https://scrapfly.io/dashboard")
    print("   3. Run: pip install -r backend/requirements.txt")
    print("   4. Test again to verify Scrapfly is working")
    print()


if __name__ == '__main__':
    asyncio.run(test_scrapfly())
