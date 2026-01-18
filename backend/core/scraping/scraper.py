"""
Web scraping utility using Playwright for JavaScript-heavy sites.
Falls back to requests for simple HTML pages.
"""

import asyncio
import logging
import random
import sys
from typing import Dict, Optional
from urllib.parse import urlparse

# Force Proactor event loop on Windows for Playwright/Subprocess support
if sys.platform == 'win32':
    try:
        from asyncio import WindowsProactorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    except ImportError:
        pass

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False
    logger.warning("Scrapfly SDK not installed. Run: pip install scrapfly-sdk")


async def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Convert GPS coordinates to human-readable address using Google Maps Geocoding API.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        Formatted address string or None if failed
    """
    try:
        # Extract Google Maps API key from the HTML (it's embedded in the page)
        # For now, we'll return a simple format until we set up the API
        return f"{lat}, {lng} (Geocoding API not configured)"
    except Exception as e:
        logger.warning(f"Failed to reverse geocode: {e}")
        return None


class ScraperError(Exception):
    """Base exception for scraping errors."""
    pass


class WebScraper:
    """
    Intelligent web scraper that chooses the best method.
    Uses Playwright for JS-heavy sites, httpx for static HTML.
    """
    
    # Sites known to be JavaScript-heavy
    JS_HEAVY_DOMAINS = [
        'encuentra24.com',
        're.cr',
    ]
    
    # Sites with Cloudflare or strong anti-bot (require residential proxy)
    CLOUDFLARE_PROTECTED_DOMAINS = [
        'brevitas.com',  # Has anti-bot protection (403 Forbidden)
        'encuentra24.com',  # Has Cloudflare protection
        # Add more as needed: 'example.com', 'another-site.com'
    ]
    
    # Sites that need external scraping service (ultra-protected)
    EXTERNAL_SERVICE_DOMAINS = [
        # Add sites that fail even with proxies: 'ultra-protected.com'
    ]
    
    # Pool of realistic user agents
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    ]
    
    def __init__(self):
        self.timeout = settings.SCRAPING_TIMEOUT_SECONDS
        self.user_agent = settings.SCRAPING_USER_AGENT
        self.rate_limit = settings.SCRAPING_RATE_LIMIT_PER_SECOND
        self.last_request_time = {}
        
        # Scrapfly configuration (preferred for Cloudflare bypass)
        self.scrapfly_enabled = getattr(settings, 'SCRAPFLY_ENABLED', False) and SCRAPFLY_AVAILABLE
        self.scrapfly_api_key = getattr(settings, 'SCRAPFLY_API_KEY', None)
        
        if self.scrapfly_enabled and self.scrapfly_api_key:
            self.scrapfly_client = ScrapflyClient(key=self.scrapfly_api_key)
            logger.info("🚀 Scrapfly enabled - Anti-bot bypass ready")
        else:
            self.scrapfly_client = None
            if not SCRAPFLY_AVAILABLE:
                logger.info("⚠️ Scrapfly SDK not available - install with: pip install scrapfly-sdk")
        
        # Proxy configuration (fallback for Cloudflare-protected sites)
        self.residential_proxy = getattr(settings, 'RESIDENTIAL_PROXY_URL', None)
        logger.info(f"🔧 Scraper initialized - Residential proxy: {'✅ Configured' if self.residential_proxy else '❌ Not configured'}")
    
    def _get_random_user_agent(self):
        """Get a random user agent from the pool."""
        return random.choice(self.USER_AGENTS)
    
    def _needs_cloudflare_bypass(self, url: str) -> bool:
        """Check if URL requires Cloudflare bypass (Scrapfly or proxy)."""
        domain = urlparse(url).netloc
        logger.info(f"🔍 [BYPASS CHECK] Checking domain: {domain}")
        logger.info(f"🔍 [BYPASS CHECK] Protected domains list: {self.CLOUDFLARE_PROTECTED_DOMAINS}")
        needs_bypass = any(protected_domain in domain for protected_domain in self.CLOUDFLARE_PROTECTED_DOMAINS)
        if needs_bypass:
            logger.info(f"🛡️ Cloudflare-protected site detected: {domain}")
        else:
            logger.info(f"✅ Domain not in protected list: {domain}")
        return needs_bypass
    
    def _should_use_scrapfly(self, url: str) -> bool:
        """Determine if should use Scrapfly for this URL."""
        domain = urlparse(url).netloc
        logger.info(f"🔍 [SCRAPFLY CHECK] Domain: {domain}")
        logger.info(f"🔍 [SCRAPFLY CHECK] Enabled: {self.scrapfly_enabled}")
        logger.info(f"🔍 [SCRAPFLY CHECK] Client available: {self.scrapfly_client is not None}")
        
        if not self.scrapfly_enabled or not self.scrapfly_client:
            logger.warning(f"❌ [SCRAPFLY] Not available - enabled={self.scrapfly_enabled}, client={self.scrapfly_client is not None}")
            return False
        
        # In production (if Scrapfly is enabled), use it for ALL protected sites
        needs_bypass = self._needs_cloudflare_bypass(url)
        logger.info(f"🔍 [SCRAPFLY CHECK] Needs Cloudflare bypass: {needs_bypass}")
        
        # If Scrapfly is available and site needs bypass, use it
        if needs_bypass:
            logger.info(f"✅ [SCRAPFLY] Will use Scrapfly for protected site: {domain}")
        
        return needs_bypass
    
    def _needs_residential_proxy(self, url: str) -> bool:
        """Check if URL requires residential proxy (fallback if Scrapfly not available)."""
        if self._should_use_scrapfly(url):
            return False  # Scrapfly handles it
        return self._needs_cloudflare_bypass(url) and self.residential_proxy is not None
    
    async def _should_use_playwright(self, url: str) -> bool:
        """Determine if URL requires Playwright (JavaScript rendering)."""
        domain = urlparse(url).netloc
        return any(js_domain in domain for js_domain in self.JS_HEAVY_DOMAINS)
    
    async def _scrape_with_playwright(self, url: str) -> Dict[str, any]:
        """Scrape using Playwright for JavaScript-heavy sites."""
        logger.info(f"Scraping with Playwright: {url}")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                # Add anti-detection scripts if needed
                page = await context.new_page()
                
                # Set timeout
                page.set_default_timeout(self.timeout * 1000)
                
                # Navigate
                response = await page.goto(url, wait_until='domcontentloaded')
                
                if not response:
                    raise ScraperError(f"Failed to load page: {url}")
                
                if response.status >= 400:
                    raise ScraperError(f"HTTP error {response.status} scraping {url}")
                
                # Wait for some content to load
                await page.wait_for_timeout(2000)  # Simple wait for JS to execute
                
                # Get content
                html_content = await page.content()
                title = await page.title()
                
                # Extract text
                # We can use evaluating JS to get text or use BS4 on the html_content
                # For consistency with other methods, let's use BS4 on the extracted HTML
                soup = BeautifulSoup(html_content, 'lxml')
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Extract images using JS for better reliability on lazy loaded ones
                images = await page.eval_on_selector_all('img', 'imgs => imgs.map(img => img.src).filter(src => src)')
                images = images[:10]  # Limit to 10
                
                await browser.close()
                
                return {
                    'success': True,
                    'html': html_content,
                    'text': text_content,
                    'title': title,
                    'images': images,
                    'url': url,
                    'method': 'playwright'
                }
                
            except PlaywrightTimeout:
                logger.error(f"Playwright timeout scraping {url}")
                raise ScraperError(f"Timeout scraping {url}")
            except Exception as e:
                logger.error(f"Playwright error: {e}")
                raise ScraperError(f"Playwright error scraping {url}: {str(e)}")
    
    async def _scrape_with_httpx(self, url: str) -> Dict[str, any]:
        """Scrape using httpx for static HTML pages."""
        logger.info(f"Scraping with httpx: {url}")
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                html_content = response.text
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Extract text
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Extract images
                images = []
                for img in soup.find_all('img', limit=10):
                    src = img.get('src')
                    if src:
                        images.append(src)
                
                # Get title
                title_tag = soup.find('title')
                title = title_tag.text if title_tag else ''
                
                return {
                    'success': True,
                    'html': html_content,
                    'text': text_content,
                    'title': title,
                    'images': images,
                    'url': url,
                    'method': 'httpx'
                }
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise ScraperError(f"HTTP error scraping {url}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Scraping error: {e}")
                raise ScraperError(f"Error scraping {url}: {str(e)}")
    
    async def _scrape_with_scrapfly(self, url: str) -> Dict[str, any]:
        """Scrape using Scrapfly API for Cloudflare-protected sites."""
        logger.info(f"🚀 [SCRAPFLY] Starting scrape: {url}")
        logger.info(f"🚀 [SCRAPFLY] Config: ASP=True, Country=CR, RenderJS=True, Wait=3000ms")
        
        try:
            # Configure Scrapfly scrape
            scrape_config = ScrapeConfig(
                url=url,
                # Anti-Scraping Protection (Cloudflare bypass)
                asp=True,
                # Use residential proxies from Costa Rica
                country='cr',
                # Enable JavaScript rendering
                render_js=True,
                # Wait for page to load
                rendering_wait=3000,
                # Retry on failure (Note: timeout cannot be set when retry=True)
                retry=True,
            )
            logger.info(f"🚀 [SCRAPFLY] Executing API call...")
            
            # Execute scrape
            api_response: ScrapeApiResponse = self.scrapfly_client.scrape(scrape_config)
            logger.info(f"✅ [SCRAPFLY] API call successful")
            logger.info(f"🔍 [SCRAPFLY] Response status: {api_response.scrape_result.get('status_code', 'N/A')}")
            
            # Extract HTML content
            html_content = api_response.scrape_result['content']
            logger.info(f"🔍 [SCRAPFLY] HTML length: {len(html_content)} chars")
            
            # Parse with BeautifulSoup for text extraction
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Extract images
            images = []
            for img in soup.find_all('img', limit=10):
                src = img.get('src')
                if src:
                    images.append(src)
            
            # Get title
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else ''
            
            # Log API cost
            api_cost = api_response.context.get('api_cost', 0)
            logger.info(f"✅ Scrapfly success - API cost: {api_cost} credits")
            
            return {
                'success': True,
                'html': html_content,
                'text': text_content,
                'title': title,
                'images': images,
                'url': url,
                'method': 'scrapfly',
                'api_cost': api_cost
            }
            
        except Exception as e:
            logger.error(f"Scrapfly error: {e}")
            raise ScraperError(f"Scrapfly error scraping {url}: {str(e)}")
    
    async def scrape(self, url: str) -> Dict[str, any]:
        """
        Main scrape method - automatically chooses best approach.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraped content
            
        Raises:
            ScraperError: If scraping fails
        """
        
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ScraperError(f"Invalid URL: {url}")
        
        # Rate limiting
        domain = parsed.netloc
        if domain in self.last_request_time:
            import time
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < (1.0 / self.rate_limit):
                await asyncio.sleep((1.0 / self.rate_limit) - elapsed)
        
        import time
        self.last_request_time[domain] = time.time()
        
        # Choose scraping method based on site requirements
        # Priority: Scrapfly > Playwright > httpx
        
        logger.info(f"🔍 [SCRAPE DECISION] Starting method selection for: {url}")
        
        if self._should_use_scrapfly(url):
            # Use Scrapfly for Cloudflare-protected sites
            logger.info(f"✅ [DECISION] Using Scrapfly for Cloudflare bypass: {url}")
            result = await self._scrape_with_scrapfly(url)
        elif await self._should_use_playwright(url):
            # Use Playwright for JS-heavy sites
            logger.info(f"✅ [DECISION] Using Playwright for JS rendering: {url}")
            result = await self._scrape_with_playwright(url)
        else:
            # Try httpx first, fallback to Playwright if fails
            logger.info(f"✅ [DECISION] Trying httpx first (simple scraping): {url}")
            try:
                result = await self._scrape_with_httpx(url)
            except ScraperError as e:
                logger.info(f"⚠️ [FALLBACK] httpx failed ({str(e)}), falling back to Playwright: {url}")
                result = await self._scrape_with_playwright(url)
        
        return result
    
    def scrape_sync(self, url: str) -> Dict[str, any]:
        """Synchronous wrapper for scrape method."""
        return asyncio.run(self.scrape(url))


def scrape_url(url: str) -> Dict[str, any]:
    """
    Convenience function to scrape a URL.
    
    Usage:
        result = scrape_url('https://encuentra24.com/property/123')
        html = result['html']
        text = result['text']
    """
    scraper = WebScraper()
    return scraper.scrape_sync(url)
