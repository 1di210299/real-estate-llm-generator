"""
Web scraping utility using Playwright for JavaScript-heavy sites.
Falls back to requests for simple HTML pages.
"""

import asyncio
import logging
import random
from typing import Dict, Optional
from urllib.parse import urlparse

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
        
        needs_bypass = self._needs_cloudflare_bypass(url)
        logger.info(f"🔍 [SCRAPFLY CHECK] Needs Cloudflare bypass: {needs_bypass}")
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
            browser = await p.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-extensions',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    '--disable-translate',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-device-discovery-notifications',
                    '--disable-gpu',
                    '--no-zygote'
                ]
            )
            
            try:
                # Random delay before starting (2-5 seconds)
                await asyncio.sleep(random.uniform(2, 5))
                
                # Check if this site needs residential proxy
                proxy_config = None
                if self._needs_residential_proxy(url):
                    proxy_config = {
                        'server': self.residential_proxy
                    }
                    logger.info(f"🌐 Using residential proxy for: {url}")
                
                context = await browser.new_context(
                    proxy=proxy_config,
                    user_agent=self._get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    locale='es-CR',
                    timezone_id='America/Costa_Rica',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'es-CR,es;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0'
                    }
                )
                
                # Add stealth scripts to hide automation
                await context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['es-CR', 'es', 'en-US', 'en']
                    });
                    
                    // Mock Chrome runtime
                    window.chrome = {
                        runtime: {}
                    };
                    
                    // Mock Permissions API
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Override toString methods to hide proxy behavior
                    const originalToString = Function.prototype.toString;
                    Function.prototype.toString = function() {
                        if (this === window.navigator.permissions.query) {
                            return 'function query() { [native code] }';
                        }
                        return originalToString.call(this);
                    };
                    
                    // Mock hardware concurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8
                    });
                    
                    // Mock device memory
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => 8
                    });
                    
                    // Mock platform
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'MacIntel'
                    });
                    
                    // Mock screen properties
                    Object.defineProperty(screen, 'colorDepth', {
                        get: () => 24
                    });
                    
                    Object.defineProperty(screen, 'pixelDepth', {
                        get: () => 24
                    });
                    
                    // Add fake battery API
                    if (!navigator.getBattery) {
                        navigator.getBattery = () => Promise.resolve({
                            charging: true,
                            chargingTime: 0,
                            dischargingTime: Infinity,
                            level: 1.0,
                            addEventListener: () => {},
                            removeEventListener: () => {}
                        });
                    }
                    
                    // Mock connection API
                    Object.defineProperty(navigator, 'connection', {
                        get: () => ({
                            effectiveType: '4g',
                            rtt: 50,
                            downlink: 10,
                            saveData: false
                        })
                    });
                    
                    // Hide automation in iframe
                    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                        get: function() {
                            const win = this.contentWindowGetter.call(this);
                            if (win) {
                                try {
                                    win.navigator.webdriver = undefined;
                                } catch(e) {}
                            }
                            return win;
                        }
                    });
                    HTMLIFrameElement.prototype.contentWindowGetter = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow').get;
                    
                    // Add missing window properties
                    window.chrome.app = {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        },
                        RunningState: {
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }
                    };
                    
                    window.chrome.csi = function() {};
                    window.chrome.loadTimes = function() {};
                    
                    // Mock OuterHTML to not show iframe[srcdoc]
                    const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
                    Object.getOwnPropertyDescriptor = function(target, property) {
                        if (target === HTMLIFrameElement.prototype && property === 'srcdoc') {
                            return undefined;
                        }
                        return originalGetOwnPropertyDescriptor(target, property);
                    };
                """)
                
                page = await context.new_page()
                
                # Random mouse movements to simulate human behavior
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Navigate with longer timeout and wait for network idle
                try:
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                    logger.info("✅ Page loaded with networkidle")
                except PlaywrightTimeout:
                    # Fallback to domcontentloaded if networkidle takes too long
                    logger.warning("⚠️ networkidle timeout, falling back to domcontentloaded")
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Random scroll to simulate human behavior
                await page.evaluate(f'window.scrollTo(0, {random.randint(100, 300)})')
                await asyncio.sleep(random.uniform(1, 2))
                
                # Wait for network to be idle (if not already)
                try:
                    await page.wait_for_load_state('networkidle', timeout=15000)
                except:
                    logger.warning("Network idle timeout - continuing anyway")
                
                # Wait for site-specific selectors to ensure content is loaded
                domain = urlparse(url).netloc
                if 'brevitas.com' in domain:
                    logger.info("🔍 Brevitas detected - waiting for key elements...")
                    try:
                        # Wait for title and price elements to be visible
                        await page.wait_for_selector('.show__title', timeout=10000, state='visible')
                        logger.info("✅ Brevitas title element loaded")
                        await page.wait_for_selector('.show__price', timeout=10000, state='visible')
                        logger.info("✅ Brevitas price element loaded")
                    except PlaywrightTimeout:
                        logger.warning("⚠️ Some Brevitas elements didn't load in time, continuing anyway...")
                
                # Wait a bit for any lazy-loaded content with random delay
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Check if it's encuentra24.com/costa-rica-es to extract clean text
                if 'encuentra24.com/costa-rica-es' in url:
                    logger.info("Encuentra24 Costa Rica detected - extracting clean text only")
                    try:
                        # Get title from page
                        title = await page.title()
                        
                        # Wait longer for dynamic content to load with random delay
                        await page.wait_for_timeout(random.randint(3000, 5000))
                        
                        # Extract full body text instead of sections (content loads dynamically)
                        body = await page.query_selector('body')
                        full_body_text = await body.inner_text() if body else ""
                        logger.info(f"Extracted full body text: {len(full_body_text)} chars")
                        
                        # Extract GPS coordinates from Google Maps embed
                        coordinates_info = ""
                        try:
                            # Wait a bit more for maps to load
                            await page.wait_for_timeout(1000)
                            
                            # Try to extract from Google Maps iframe and URLs
                            import re
                            page_html = await page.content()
                            
                            logger.info("🔍 DEBUG: Starting GPS extraction...")
                            logger.info(f"🔍 DEBUG: Page HTML length: {len(page_html)} chars")
                            logger.info(f"🔍 DEBUG: Using re.DOTALL flag for regex matching")
                            
                            # Method 1: Search for coordinates in Google Maps embed URLs (q= parameter)
                            # Handle HTML entities (&amp;), line breaks, and any characters with DOTALL
                            maps_embed_pattern = r'google\.com/maps/embed.*?q=([-\d.\s]+),([-\d.\s]+)'
                            logger.info(f"🔍 DEBUG: Pattern: {maps_embed_pattern}")
                            maps_embed_matches = re.findall(maps_embed_pattern, page_html, re.DOTALL)
                            logger.info(f"🔍 DEBUG: Found {len(maps_embed_matches)} maps embed with coordinates")
                            if maps_embed_matches:
                                lat_raw, lng_raw = maps_embed_matches[0]
                                # Remove whitespace and line breaks from coordinates
                                lat = re.sub(r'\s+', '', lat_raw)
                                lng = re.sub(r'\s+', '', lng_raw)
                                coordinates_info += f"\nExtracted Coordinates: {lat}, {lng}"
                                logger.info(f"📍 Extracted from maps embed: {lat}, {lng}")
                            
                            # Method 2: Search for coordinates in href links (@lat,lng format)
                            maps_links = re.findall(r'href="[^"]*maps\.google\.com[^"]*@([-\d.]+),([-\d.]+)', page_html)
                            logger.info(f"🔍 DEBUG: Found {len(maps_links)} maps href links with @ coordinates")
                            if maps_links and not maps_embed_matches:
                                lat, lng = maps_links[0]
                                coordinates_info += f"\nExtracted Coordinates: {lat}, {lng}"
                                logger.info(f"📍 Extracted from maps URL: {lat}, {lng}")
                            
                            # Method 3: Search for DMS coordinates in text (e.g., 9°36'55.9"N)
                            dms_pattern = r'(\d+)°(\d+)\'([\d.]+)"([NS])\s+(\d+)°(\d+)\'([\d.]+)"([EW])'
                            dms_match = re.search(dms_pattern, page_html)
                            logger.info(f"🔍 DEBUG: DMS pattern match found: {dms_match is not None}")
                            if dms_match:
                                lat_deg, lat_min, lat_sec, lat_dir, lng_deg, lng_min, lng_sec, lng_dir = dms_match.groups()
                                gps_text = f"{lat_deg}°{lat_min}'{lat_sec}\"{lat_dir} {lng_deg}°{lng_min}'{lng_sec}\"{lng_dir}"
                                coordinates_info += f"\nGPS Coordinates (DMS): {gps_text}"
                                logger.info(f"📍 Found GPS DMS: {gps_text}")
                            
                            # Method 4: Try to find the place-card elements in iframe
                            frames = page.frames
                            logger.info(f"🔍 DEBUG: Found {len(frames)} frames on page")
                            for idx, frame in enumerate(frames):
                                try:
                                    frame_url = frame.url
                                    if 'maps.google' in frame_url:
                                        logger.info(f"🔍 DEBUG: Frame {idx} is Google Maps: {frame_url[:150]}")
                                        
                                        # Wait longer for map content to load
                                        await frame.wait_for_timeout(3000)
                                        
                                        # Try to extract coordinates from iframe URL
                                        if 'q=' in frame_url:
                                            q_match = re.search(r'[?&]q=([-\d.]+)[,\s%2C]+([-\d.]+)', frame_url)
                                            if q_match:
                                                lat, lng = q_match.groups()
                                                if not coordinates_info:  # Only add if we don't have coordinates yet
                                                    coordinates_info += f"\nExtracted Coordinates: {lat}, {lng}"
                                                logger.info(f"📍 Extracted from iframe URL q param: {lat}, {lng}")
                                        
                                        # Try to extract Plus Code address from iframe HTML
                                        try:
                                            iframe_html = await frame.content()
                                            # Look for Plus Code pattern like "J98C+6J5 Jaco, Puntarenas Province"
                                            plus_code_pattern = r'([A-Z0-9]{4}\+[A-Z0-9]{2,3})\s+([^,<>"]+(?:,\s*[^,<>"]+)*)'
                                            plus_code_match = re.search(plus_code_pattern, iframe_html)
                                            if plus_code_match:
                                                plus_code_address = f"{plus_code_match.group(1)} {plus_code_match.group(2)}"
                                                coordinates_info += f"\nFull Address: {plus_code_address}"
                                                logger.info(f"📍 Found Plus Code Address: {plus_code_address}")
                                        except Exception as e:
                                            logger.debug(f"Could not extract Plus Code: {e}")
                                    
                                    # Try to extract address from the Google Maps iframe
                                    place_card = await frame.query_selector('.place-card')
                                    if place_card:
                                        # Get the full address
                                        address_elem = await frame.query_selector('.place-card .address')
                                        if address_elem:
                                            address_text = await address_elem.inner_text()
                                            logger.info(f"🔍 DEBUG: Found address in Maps iframe: {address_text}")
                                            coordinates_info += f"\nAddress: {address_text}"
                                            logger.info(f"📍 Found Address from Maps: {address_text}")
                                        
                                        # Get place name with GPS coordinates
                                        place_name = await frame.query_selector('.place-card .place-name')
                                        if place_name:
                                            gps_text = await place_name.inner_text()
                                            logger.info(f"🔍 DEBUG: Found place-name in frame {idx}: {gps_text}")
                                        if '°' in gps_text or 'N' in gps_text or 'W' in gps_text:
                                            coordinates_info += f"\nGPS Coordinates (DMS): {gps_text}"
                                            logger.info(f"📍 Found GPS in iframe: {gps_text}")
                                    
                                    address_elem = await frame.query_selector('.place-card .address')
                                    if address_elem:
                                        address_text = await address_elem.inner_text()
                                        logger.info(f"🔍 DEBUG: Found address in frame {idx}: {address_text}")
                                        coordinates_info += f"\nFull Address: {address_text}"
                                        logger.info(f"📍 Found Address in iframe: {address_text}")
                                except Exception as frame_error:
                                    if 'maps.google' in frame.url:
                                        logger.info(f"🔍 DEBUG: Error in Google Maps frame {idx}: {frame_error}")
                            
                            # Method 5: Search for address in main page HTML
                            address_pattern = r'([A-Z0-9+]{4,}\s+[A-Za-zó]+,\s+[A-Za-z\s]+Province,\s+Costa\s+Rica)'
                            address_matches = re.findall(address_pattern, page_html)
                            logger.info(f"🔍 DEBUG: Found {len(address_matches)} address matches")
                            if address_matches:
                                coordinates_info += f"\nFull Address: {address_matches[0]}"
                                logger.info(f"📍 Found Address in HTML: {address_matches[0]}")
                            
                            # Method 6: Search for any maps.google.com URLs in HTML (for debugging)
                            all_maps_urls = re.findall(r'https?://[^"\s]*maps\.google[^"\s]*', page_html)
                            logger.info(f"🔍 DEBUG: Found {len(all_maps_urls)} total Google Maps URLs")
                            if all_maps_urls:
                                logger.info(f"🔍 DEBUG: First maps URL preview: {all_maps_urls[0][:200]}")
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Could not extract GPS coordinates: {e}")
                            logger.exception("Full traceback:")
                        
                        # Combine as clean text with coordinates
                        text_content = f"Title: {title}\n\n{full_body_text}{coordinates_info}"
                        html_content = text_content  # Use text as HTML since LLM works better with clean text
                        
                        logger.info(f"✅ Extracted clean text: {len(text_content)} chars")
                        logger.info(f"Preview: {text_content[:200]}")
                        logger.info(f"🔍 DEBUG: Coordinates info added: {len(coordinates_info)} chars")
                        if coordinates_info:
                            logger.info(f"🔍 DEBUG: Coordinates content: {coordinates_info}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error extracting text: {e}, falling back to full page")
                        html_content = await page.content()
                        text_content = await page.inner_text('body')
                else:
                    # Get full HTML content for other sites
                    html_content = await page.content()
                    text_content = await page.inner_text('body')
                
                # Try to extract property images
                images = await page.query_selector_all('img')
                image_urls = []
                for img in images[:10]:  # Limit to first 10 images
                    src = await img.get_attribute('src')
                    if src and ('property' in src.lower() or 'photo' in src.lower()):
                        image_urls.append(src)
                
                # Get page title
                title = await page.title()
                
                await browser.close()
                
                return {
                    'success': True,
                    'html': html_content,
                    'text': text_content,
                    'title': title,
                    'images': image_urls,
                    'url': url,
                    'method': 'playwright'
                }
                
            except PlaywrightTimeout:
                await browser.close()
                raise ScraperError(f"Timeout scraping {url}")
            
            except Exception as e:
                await browser.close()
                logger.error(f"Playwright error: {e}")
                raise ScraperError(f"Error scraping {url}: {str(e)}")
    
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
            except ScraperError:
                logger.info(f"⚠️ [FALLBACK] httpx failed, falling back to Playwright: {url}")
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
