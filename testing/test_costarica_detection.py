import sys
import os
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.scraping.scraper import scrape_url
from core.llm.content_detection import detect_content_type
from core.llm.page_type_detection import detect_page_type

url = 'https://costarica.org/tours/'
print(f"�� Testing: {url}\n")

scraped = scrape_url(url)
html = scraped.get('html', '')
print(f"✅ HTML size: {len(html)} chars\n")

# Content type
content = detect_content_type(url=url, html=html, use_llm_fallback=False)
print(f"📌 Content Type: {content['content_type']}")
print(f"   Confidence: {content['confidence']:.2%}")
print(f"   Method: {content['method']}\n")

# Page type
page = detect_page_type(url=url, html=html, content_type=content['content_type'])
print(f"📄 Page Type: {page['page_type']}")
print(f"   Confidence: {page['confidence']:.2%}")
print(f"   Method: {page['method']}")
