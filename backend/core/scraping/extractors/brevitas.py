"""
Brevitas.com specific extractor.
"""

from typing import Optional
from bs4 import BeautifulSoup
from decimal import Decimal
import re
import logging
import openai
from django.conf import settings
from .base import BaseExtractor

logger = logging.getLogger(__name__)


class BrevitasExtractor(BaseExtractor):
    """Extractor for brevitas.com listings."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "brevitas.com"
    
    def extract(self, html: str, url: Optional[str] = None):
        """Override extract to use AI enhancement with clean text."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract ALL relevant text from page (clean, no HTML tags)
        full_text = self.extract_all_text(soup)
        print(f"📝 Texto limpio extraído: {len(full_text)} caracteres (vs {len(html)} chars HTML)")
        
        # Use AI to process ALL the text and extract fields
        ai_enhanced_data = self.enhance_with_ai(full_text)
        
        # Call parent extract
        data = super().extract(html, url)
        
        # Merge AI-enhanced data (AI data takes precedence)
        data.update(ai_enhanced_data)
        
        return data
    
    def extract_all_text(self, soup: BeautifulSoup) -> str:
        """Extract ALL relevant visible text from Brevitas page."""
        sections = []
        
        # 1. Title
        title = soup.find('h1', class_='show__title')
        if title:
            sections.append(f"TITLE: {title.get_text(strip=True)}")
        
        # 2. Price
        price = soup.find(class_='show__price')
        if price:
            sections.append(f"PRICE: {price.get_text(strip=True)}")
        
        # 3. Address
        address = soup.find('p', class_='show__address')
        if address:
            sections.append(f"LOCATION: {address.get_text(strip=True)}")
        
        # 4. Property Details (Building Size, Lot Area, Beds, Baths, etc.)
        details = soup.find_all(class_='product__detail')
        if details:
            details_text = []
            for detail in details:
                details_text.append(detail.get_text(strip=True))
            sections.append("DETAILS:\n" + "\n".join(details_text))
            
        # 4b. Features / Amenities (Often in list format)
        features_container = soup.find(class_='show__features') or soup.find(id='features')
        if features_container:
            sections.append(f"FEATURES: {features_container.get_text(separator=' | ', strip=True)}")
        else:
             # Generic fallback
            lists = soup.find_all('ul')
            for ul in lists:
                if len(ul.find_all('li')) > 4: 
                     sections.append(f"POSSIBLE FEATURES: {ul.get_text(separator=' | ', strip=True)}")
        
        # 5. Description (most important)
        description = soup.find('p', class_='show__copy')
        if description:
            desc_text = description.get_text(strip=True)
            if desc_text:
                sections.append(f"DESCRIPTION:\n{desc_text}")
        
        # 6. Property status badges
        badges = soup.find_all(class_='label')
        if badges:
            badge_text = [badge.get_text(strip=True) for badge in badges]
            sections.append("STATUS: " + " | ".join(badge_text))
        
        # Join all sections
        return "\n\n".join(sections)
    
    def enhance_with_ai(self, full_text: str) -> dict:
        """Use OpenAI to process clean text and extract ALL fields + generate professional description."""
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("⚠️ OpenAI API key not configured, skipping AI enhancement")
                return {}
            
            client = openai.OpenAI(api_key=api_key)
            
            # Limit text to reasonable size
            text_to_process = full_text[:10000] if len(full_text) > 10000 else full_text
            
            # Save text to file for inspection
            try:
                with open('ai_input_text.txt', 'w', encoding='utf-8') as f:
                    f.write(text_to_process)
                print(f"💾 Texto guardado en: ai_input_text.txt ({len(text_to_process)} caracteres)")
            except Exception as e:
                print(f"⚠️ No se pudo guardar archivo: {e}")
            
            prompt = """Analyze the real estate property information and extract/normalize the following fields in JSON format:

{
  "title": "Property name or descriptive title (max 100 chars)",
  "price_usd": <numeric price in USD>,
  "bedrooms": <number or null>,
  "bathrooms": <number or null>,
  "area_m2": <number or null>,
  "lot_size_m2": <number or null>,
  "property_type": "Casa|Apartamento|Terreno|Lote|House|Land|Commercial|etc",
  "listing_type": "sale|rent",
  "location": "City, Province, Country",
  "amenities": ["amenity1", "amenity2", ...],
  "parking_spaces": <number or null>,
  "pool": <boolean>,
  "description": "Professional property description (3-4 sentences, max 600 chars)",
  "units": <number of units if multi-unit/hotel property, else null>,
  "zoning": "Residential|Commercial|Mixed|etc (if specified)",
  "hoa_fee": <numeric monthly fee in USD or null>,
  "taxes": <numeric yearly taxes in USD or null>,
  "year_built": <number or null>,
  "video_url": "url or null",
  "brochure_url": "url or null"
}

CRITICAL INSTRUCTIONS:

TITLE:
- Extract the actual property NAME or create a descriptive title
- If there's unique features, mention them (e.g., "Oceanfront", "Titled Property", "Beach Access")
- Format: "Unique Feature + Property Type in Location"
- Example: "Oceanfront Titled Estate in El Roble" or "Luxury Mountain View Residence in Atenas"
- Keep concise (max 100 chars)

DESCRIPTION:
- Write a professional, compelling summary highlighting ALL key selling points
- Include: property type, location, size, unique features, main amenities, investment/use potential
- Mention CRITICAL differentiators (titled ownership, beach access, retreat-ready, etc.)
- Use complete sentences, professional real estate language
- 3-4 sentences (around 400-600 characters)
- Example: "Rare oceanfront titled property in El Roble offering full ownership rights without concession restrictions. Features a 2-story main house with 3br/3ba plus independent guest house with 1br/1ba, infinity pool, and direct beach access on a 2,200 m² lot. Prime location within 5 minutes of hospitals, restaurants, and schools, ideal for residential living, vacation rental, or boutique hospitality ventures."

LOT SIZE:
- CRITICAL: Extract lot area in square meters or convert from acres (1 acre = 4,046.86 m²)
- Look for "Lot Area", "Lot Size", "Land Area" in sqft or acres
- If in sqft: divide by 10.764 to get m²
- If in acres: multiply by 4046.86 to get m²

BUILDING SIZE:
- Extract construction area in m²
- Convert from sqft if needed (1 sqft = 0.092903 m²)
- Look for "Building Size", "Total Construction", "Living Area"

OTHER FIELDS:
- Parse bedrooms/bathrooms as integers
- Extract ALL amenities from description (pool, jacuzzi, terrace, garage, beach access, etc.)
- Identify unique features (titled ownership, no concession, ocean views, etc.)
- Property type: prefer "House", "Land", "Commercial" over Spanish terms for Brevitas
- Parking spaces from "Parking Spots" field
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a real estate data extraction expert specializing in Costa Rica properties. Extract and normalize ALL property information accurately, including lot sizes and unique features. Always return valid JSON."},
                    {"role": "user", "content": f"{prompt}\n\n{text_to_process}"}
                ],
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            import json
            ai_data = json.loads(response.choices[0].message.content)
            
            # Convert AI response to expected format
            cleaned_data = {}
            
            if ai_data.get('title'):
                cleaned_data['title'] = ai_data['title']
            
            if ai_data.get('price_usd'):
                try:
                    cleaned_data['price_usd'] = Decimal(str(ai_data['price_usd']))
                except:
                    pass
            
            if ai_data.get('bedrooms'):
                try:
                    cleaned_data['bedrooms'] = int(ai_data['bedrooms'])
                except:
                    pass
            
            if ai_data.get('bathrooms'):
                try:
                    cleaned_data['bathrooms'] = Decimal(str(ai_data['bathrooms']))
                except:
                    pass
            
            if ai_data.get('area_m2'):
                try:
                    cleaned_data['area_m2'] = Decimal(str(ai_data['area_m2']))
                except:
                    pass
            
            if ai_data.get('lot_size_m2'):
                try:
                    cleaned_data['lot_size_m2'] = Decimal(str(ai_data['lot_size_m2']))
                except:
                    pass
            
            if ai_data.get('property_type'):
                cleaned_data['property_type'] = ai_data['property_type']
            
            if ai_data.get('listing_type'):
                cleaned_data['listing_type'] = ai_data['listing_type']
            
            if ai_data.get('location'):
                cleaned_data['location'] = ai_data['location']
            
            if ai_data.get('amenities') and isinstance(ai_data['amenities'], list):
                cleaned_data['amenities'] = ai_data['amenities']
            
            if ai_data.get('parking_spaces'):
                try:
                    cleaned_data['parking_spaces'] = int(ai_data['parking_spaces'])
                except:
                    pass
            
            if ai_data.get('description'):
                cleaned_data['description'] = ai_data['description']
            
            if ai_data.get('pool') is not None:
                cleaned_data['pool'] = ai_data.get('pool')
            
            print(f"✅ AI enhanced data: {len(cleaned_data)} fields extracted")
            return cleaned_data
            
        except Exception as e:
            print(f"❌ AI enhancement error: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property title."""
        # Brevitas uses show__title class
        title = soup.find('h1', class_='show__title')
        if title:
            return title.get_text(strip=True)
        return super().extract_title(soup)
    
    def extract_price(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract price from show__price."""
        # Try show__price class
        price_elem = soup.find(class_='show__price')
        if price_elem:
            text = price_elem.get_text(strip=True)
            logger.info(f"[Brevitas] Found price element: {text}")
            # Remove $ and commas
            match = re.search(r'([\d,]+)', text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = Decimal(price_str)
                    logger.info(f"[Brevitas] Extracted price: ${price}")
                    return price
                except:
                    pass
        
        # Fallback: try to find any element with $ symbol
        all_text = soup.get_text()
        match = re.search(r'\$\s*([\d,]+)', all_text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                price = Decimal(price_str)
                logger.info(f"[Brevitas] Extracted price from text: ${price}")
                return price
            except:
                pass
        
        logger.warning("[Brevitas] Could not find price")
        return super().extract_price(soup)
    
    def extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract bedrooms from Details section."""
        # Look for "Beds:" in product details
        details = soup.find_all(class_='product__detail')
        for detail in details:
            text = detail.get_text(strip=True)
            if 'Beds:' in text or 'Bedrooms:' in text:
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
        
        # Also check in description
        desc_elem = soup.find('p', class_='show__copy')
        if desc_elem:
            text = desc_elem.get_text()
            match = re.search(r'Bedrooms:\s*(\d+)', text)
            if match:
                return int(match.group(1))
        
        return super().extract_bedrooms(soup)
    
    def extract_bathrooms(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract bathrooms from Details section."""
        # Look for "Baths:" in product details
        details = soup.find_all(class_='product__detail')
        for detail in details:
            text = detail.get_text(strip=True)
            if 'Baths:' in text or 'Bathrooms:' in text:
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    return Decimal(match.group(1))
        
        # Also check in description
        desc_elem = soup.find('p', class_='show__copy')
        if desc_elem:
            text = desc_elem.get_text()
            match = re.search(r'Bathrooms:\s*(\d+)', text)
            if match:
                return Decimal(match.group(1))
        
        return super().extract_bathrooms(soup)
    
    def extract_area(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract building size."""
        # Look for Building Size in details
        details = soup.find_all(class_='product__detail')
        for detail in details:
            text = detail.get_text(strip=True)
            if 'Building Size:' in text:
                match = re.search(r'([\d,]+\.?\d*)\s*sqft', text)
                if match:
                    sqft = Decimal(match.group(1).replace(',', ''))
                    return sqft * Decimal('0.092903')  # Convert to m2
        
        # Also check description
        desc_elem = soup.find('p', class_='show__copy')
        if desc_elem:
            text = desc_elem.get_text()
            match = re.search(r'Total Construction:\s*([\d,]+)\s*sq ft', text)
            if match:
                sqft = Decimal(match.group(1).replace(',', ''))
                return sqft * Decimal('0.092903')
        
        return super().extract_area(soup)
    
    def extract_lot_size(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract lot area."""
        # Look for Lot Area in details
        details = soup.find_all(class_='product__detail')
        for detail in details:
            text = detail.get_text(strip=True)
            if 'Lot Area:' in text:
                match = re.search(r'([\d,]+\.?\d*)\s*acres', text)
                if match:
                    acres = Decimal(match.group(1).replace(',', ''))
                    return acres * Decimal('4046.86')  # Convert to m2
        
        # Also check description
        desc_elem = soup.find('p', class_='show__copy')
        if desc_elem:
            text = desc_elem.get_text()
            match = re.search(r'Lot Size:\s*([\d,]+\.?\d*)\s*acres', text)
            if match:
                acres = Decimal(match.group(1).replace(',', ''))
                return acres * Decimal('4046.86')
        
        return super().extract_lot_size(soup)
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description."""
        # Brevitas uses show__copy class for description
        desc = soup.find('p', class_='show__copy')
        if desc:
            return desc.get_text(separator='\n', strip=True)
        return super().extract_description(soup)
    
    def extract_property_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property type from badges."""
        badges = soup.find_all(class_='label')
        for badge in badges:
            text = badge.get_text(strip=True).lower()
            if 'residential' in text:
                # Check if it has bedrooms to determine if it's a house/condo or land
                bedrooms = self.extract_bedrooms(soup)
                if bedrooms and bedrooms > 0:
                    return 'house'
                else:
                    return 'land'
            elif 'commercial' in text:
                return 'commercial'
        return 'house'
    
    def extract_listing_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing type."""
        badges = soup.find_all(class_='label')
        for badge in badges:
            text = badge.get_text(strip=True).lower()
            if 'for sale' in text:
                return 'for_sale'
            elif 'for rent' in text or 'for lease' in text:
                return 'for_rent'
        return 'for_sale'
    
    def extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract address."""
        addr = soup.find('p', class_='show__address')
        if addr:
            return addr.get_text(strip=True)
        return None
    
    def extract_city(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract city from address."""
        addr = self.extract_address(soup)
        if addr:
            # Brevitas format: "Juanilama, Espíritu Santo, Provincia de Puntarenas 60201, Costa Rica"
            parts = [p.strip() for p in addr.split(',')]
            if len(parts) >= 2:
                return parts[1]  # Espíritu Santo
        return None
    
    def extract_province(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract province from address."""
        addr = self.extract_address(soup)
        if addr:
            # Look for "Provincia de X"
            match = re.search(r'Provincia de ([^,\d]+)', addr)
            if match:
                return match.group(1).strip()
        return None
    
    def extract_country(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract country from address."""
        addr = self.extract_address(soup)
        if addr and 'Costa Rica' in addr:
            return 'Costa Rica'
        return None
    
    def extract_parking(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract parking spaces."""
        details = soup.find_all(class_='product__detail')
        for detail in details:
            text = detail.get_text(strip=True)
            if 'Parking Spots:' in text:
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
        return None
    
    def extract_amenities(self, soup: BeautifulSoup) -> list:
        """Extract amenities from description."""
        amenities = []
        desc = soup.find('p', class_='show__copy')
        if desc:
            text = desc.get_text()
            
            # Look for bulleted lists
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Lines starting with • or -
                if line.startswith('•') or line.startswith('-'):
                    amenity = line.lstrip('•-').strip()
                    if amenity and len(amenity) > 3:
                        amenities.append(amenity)
        
        return amenities
    
    def extract_agent_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract agent name from contact section."""
        desc = soup.find('p', class_='show__copy')
        if desc:
            text = desc.get_text()
            # Look for "Contact" section
            if 'Contact' in text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'Contact' in line and i + 2 < len(lines):
                        # Agent name is usually after "Contact"
                        agent_line = lines[i + 2].strip()
                        if agent_line and '/' in agent_line:
                            # "Evelyn Bulakar / Justin Nielsen"
                            return agent_line.split('/')[0].strip()
                        elif agent_line and not any(x in agent_line for x in ['WhatsApp', 'Email', '@', '+']):
                            return agent_line
        return None
    
    def extract_agent_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract agent phone."""
        desc = soup.find('p', class_='show__copy')
        if desc:
            text = desc.get_text()
            # Look for phone numbers
            match = re.search(r'\+\d{3}\s*\d{4}-\d{4}', text)
            if match:
                return match.group(0)
        return None
    
    def extract_agent_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract agent email."""
        desc = soup.find('p', class_='show__copy')
        if desc:
            text = desc.get_text()
            # Look for email
            match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if match:
                return match.group(0)
        return None
