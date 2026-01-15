"""ColdwellBankerCostaRica.com specific extractor.
"""

from typing import Optional
from bs4 import BeautifulSoup
from decimal import Decimal
import re
import openai
import json
from django.conf import settings
from .base import BaseExtractor


class ColdwellBankerExtractor(BaseExtractor):
    """Extractor for coldwellbankercostarica.com listings."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "coldwellbankercostarica.com"
    
    def extract(self, html: str, url: Optional[str] = None) -> dict:
        """
        Override extract to use AI enhancement with clean text extraction.
        This reduces token usage by 98%+ and improves data quality.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract clean text from key sections
        text_content = self.extract_all_text(soup)
        
        # Log character count reduction
        original_chars = len(html)
        text_chars = len(text_content)
        reduction_pct = ((original_chars - text_chars) / original_chars * 100) if original_chars > 0 else 0
        print(f"📝 Texto limpio extraído: {text_chars} caracteres (vs {original_chars} chars HTML) - {reduction_pct:.1f}% reducción")
        
        # Save to file for inspection
        try:
            with open('ai_input_text.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"💾 Texto guardado en: ai_input_text.txt")
        except Exception as e:
            print(f"⚠️ Error guardando texto: {e}")
        
        # Enhance with AI
        enhanced_data = self.enhance_with_ai(text_content)
        
        if enhanced_data:
            return enhanced_data
        
        # Fallback to base extraction if AI fails
        print("⚠️ AI enhancement failed, falling back to base extraction")
        return super().extract(html)
    
    def extract_all_text(self, soup: BeautifulSoup) -> str:
        """
        Extract clean, structured text from key sections of Coldwell Banker pages.
        """
        sections = []
        
        # 1. TÍTULO Y PRECIO
        title_wrap = soup.find('div', class_='title-wrap')
        if title_wrap:
            sections.append("=== TÍTULO Y PRECIO ===")
            sections.append(title_wrap.get_text(separator='\n', strip=True))
            sections.append("")
        
        # 2. ESPECIFICACIONES (bedrooms, bathrooms, area, lot size)
        ul_specs = soup.find('ul', class_='ul-specs')
        if ul_specs:
            sections.append("=== ESPECIFICACIONES ===")
            for li in ul_specs.find_all('li'):
                spec_text = li.get_text(strip=True)
                if spec_text:
                    sections.append(spec_text)
            sections.append("")
        
        # 3. MÁS DETALLES (additional specifications)
        more_details = soup.find('div', class_='more-details')
        if more_details:
            sections.append("=== MÁS DETALLES ===")
            sections.append(more_details.get_text(separator='\n', strip=True))
            sections.append("")
        
        # 4. DESCRIPCIÓN COMPLETA
        desc_wrap = soup.find('div', class_='desc-wrap')
        if desc_wrap:
            sections.append("=== DESCRIPCIÓN ===")
            # Try complete description first
            desc_complete = desc_wrap.find('div', class_='desc-content-complete')
            if desc_complete:
                # Remove read-toggle links
                for link in desc_complete.find_all('a', class_='read-toggle'):
                    link.decompose()
                sections.append(desc_complete.get_text(separator='\n', strip=True))
            else:
                # Fallback to any desc-content
                desc_content = desc_wrap.find('div', class_='desc-content')
                if desc_content:
                    for link in desc_content.find_all('a', class_='read-toggle'):
                        link.decompose()
                    sections.append(desc_content.get_text(separator='\n', strip=True))
            sections.append("")
        
        # 5. CARACTERÍSTICAS/AMENIDADES
        features_section = soup.find('div', class_='property-features')
        if features_section:
            sections.append("=== CARACTERÍSTICAS ===")
            for li in features_section.find_all('li'):
                feature = li.get_text(strip=True)
                if feature:
                    sections.append(f"• {feature}")
            sections.append("")
        
        # 6. UBICACIÓN
        # Try h3 tags with location info
        for section in soup.find_all('section'):
            for h3 in section.find_all('h3'):
                text = h3.get_text(strip=True)
                if 'ubicación:' in text.lower() or 'location:' in text.lower():
                    sections.append("=== UBICACIÓN ===")
                    sections.append(text)
                    sections.append("")
                    break
        
        return '\n'.join(sections)
    
    def enhance_with_ai(self, text_content: str) -> Optional[dict]:
        """
        Use OpenAI to extract and enhance property data from clean text.
        """
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("⚠️ No OpenAI API key configured")
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""Eres un experto en extracción de datos de bienes raíces de Costa Rica.

Analiza el siguiente texto extraído de una propiedad en Coldwell Banker Costa Rica y extrae toda la información posible.

INSTRUCCIONES IMPORTANTES:

1. **Precio (price_usd)**: MUY IMPORTANTE - Busca el precio en la sección "TÍTULO Y PRECIO"
   - El precio aparece en formato: $1,750,000 o $750,000
   - Extrae SOLO los números sin símbolos ($), sin comas (,), sin puntos decimales
   - Ejemplo: si ves "$1,750,000" → extrae "1750000"
   - Ejemplo: si ves "$750,000" → extrae "750000"
   - Si NO encuentras precio, usa null

2. **Título profesional**: Genera un título atractivo y profesional en ESPAÑOL que resuma la propiedad. 
   - Para terrenos: Incluye el tamaño y ubicación (ej: "Terreno Comercial de 360 m² en Curridabat")
   - Para casas/apartamentos: Incluye tipo, tamaño, y ubicación (ej: "Casa de Lujo de 250 m² en Escazú")
   - NO uses el título exacto del sitio web si es muy largo o poco claro

3. **Descripción profesional**: Genera UNA descripción profesional en ESPAÑOL de 3-4 oraciones que sintetice toda la información clave:
   - Características principales (tamaño, ubicación, zonificación si es terreno)
   - Características únicas o especiales (zonificación comercial, acceso a transporte público, ubicación estratégica)
   - Potencial de desarrollo o uso
   - Condiciones especiales (muros perimetrales, edificaciones existentes, etc.)
   - NO copies y pegues toda la descripción del sitio - sintetiza lo más importante

4. **Tamaño del lote (lot_size_m2)**: MUY IMPORTANTE para terrenos
   - Busca términos: "superficie", "área del terreno", "lot size", "lote de", "terreno de"
   - Convierte unidades: 1 acre = 4046.86 m², 1 sqft = 0.092903 m², 1 hectárea = 10000 m²
   - Si encuentras el área de construcción Y el área del lote, usa el área del lote para lot_size_m2
   - Para terrenos SIN construcción, lot_size_m2 y area_m2 pueden ser el mismo valor

5. **Área construida (area_m2)**: Área de construcción o edificación
   - Para terrenos SIN construcción, puede ser null o igual a lot_size_m2 si no se especifica
   - Convierte sqft a m² si es necesario

6. **Tipo de propiedad (property_type)**: "Terreno", "Casa", "Apartamento", "Condominio", "Lote", etc.

7. **Estado del listado (listing_type)**: Siempre "Venta" para Coldwell Banker (es un sitio de ventas)

8. **Zonificación**: Para terrenos, extrae información de uso de suelo (Comercial, Residencial de Baja Densidad, etc.)

9. **Amenidades**: Lista TODO lo que encuentres en características/amenidades

TEXTO A ANALIZAR:
{text_content}

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin ```json):
{{
  "title": "Título profesional en español",
  "price_usd": "solo el número sin símbolos ni comas",
  "property_type": "Terreno/Casa/Apartamento/etc",
  "listing_type": "Venta",
  "location": "ciudad, provincia",
  "city": "ciudad",
  "province": "provincia",
  "country": "Costa Rica",
  "bedrooms": número o null,
  "bathrooms": número decimal o null,
  "area_m2": número decimal (área construida) o null,
  "lot_size_m2": número decimal (área del lote/terreno) o null,
  "parking_spaces": "número o null",
  "description": "descripción profesional de 3-4 oraciones en español",
  "amenities": ["lista", "de", "amenidades"],
  "zoning": "Residencial|Comercial|Mixto|etc (si se especifica)",
  "hoa_fee": "número mensual en USD o null",
  "taxes": "número anual en USD o null",
  "year_built": "número (año) o null",
  "video_url": "url de video o null",
  "brochure_url": "url del brochure/pdf o null"
}}"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de datos de bienes raíces. Respondes ÚNICAMENTE con JSON válido, sin markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            
            print(f"✅ AI enhancement successful: {len(data)} campos extraídos")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI response as JSON: {e}")
            print(f"Response content: {content[:500]}")
            return None
        except Exception as e:
            print(f"❌ Error in AI enhancement: {e}")
            return None
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property title."""
        # Try title-wrap section
        title_section = soup.find('div', class_='title-wrap')
        if title_section:
            title = title_section.find('h1')
            if title:
                return title.get_text(strip=True)
        
        return super().extract_title(soup)
    
    def extract_price(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract price from title-wrap section."""
        title_section = soup.find('div', class_='title-wrap')
        if title_section:
            price_text = title_section.get_text()
            match = re.search(r'\$\s*([\d,]+)', price_text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return Decimal(price_str)
                except:
                    pass
        
        return super().extract_price(soup)
    
    def extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract bedrooms from ul-specs."""
        specs = soup.find('ul', class_='ul-specs')
        if specs:
            text = specs.get_text()
            match = re.search(r'(\d+)\s*(bed|habitacion|dormitorio)', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Try more-details section
        more_details = soup.find('div', class_='more-details')
        if more_details:
            text = more_details.get_text()
            match = re.search(r'(\d+)\s*(bed|habitacion|dormitorio)', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return super().extract_bedrooms(soup)
    
    def extract_bathrooms(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract bathrooms from ul-specs."""
        specs = soup.find('ul', class_='ul-specs')
        if specs:
            text = specs.get_text()
            match = re.search(r'(\d+\.?\d*)\s*(bath|baño)', text, re.IGNORECASE)
            if match:
                return Decimal(match.group(1))
        
        # Try more-details section
        more_details = soup.find('div', class_='more-details')
        if more_details:
            text = more_details.get_text()
            match = re.search(r'(\d+\.?\d*)\s*(bath|baño)', text, re.IGNORECASE)
            if match:
                return Decimal(match.group(1))
        
        return super().extract_bathrooms(soup)
    
    def extract_area(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract building area from specs."""
        specs = soup.find('ul', class_='ul-specs')
        if specs:
            text = specs.get_text()
            # Look for sq ft or m2
            match = re.search(r'([\d,]+\.?\d*)\s*(sq\s*ft|sqft|m[²2])', text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    value = Decimal(value_str)
                    # Convert sq ft to m2 if needed
                    if 'ft' in match.group(2).lower():
                        value = value * Decimal('0.092903')
                    return value
                except:
                    pass
        
        return super().extract_area(soup)
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description."""
        # Try desc-wrap section (main description container)
        desc_wrap = soup.find('div', class_='desc-wrap')
        if desc_wrap:
            # Try to get the complete description first
            desc_complete = desc_wrap.find('div', class_='desc-content-complete')
            if desc_complete:
                # Remove "Read More" / "Leer menos" links
                for link in desc_complete.find_all('a', class_='read-toggle'):
                    link.decompose()
                text = desc_complete.get_text(separator='\n', strip=True)
                if text:
                    return text
            
            # Fallback to partial description
            desc_partial = desc_wrap.find('div', class_='desc-content-partial')
            if desc_partial:
                for link in desc_partial.find_all('a', class_='read-toggle'):
                    link.decompose()
                text = desc_partial.get_text(separator='\n', strip=True)
                if text:
                    return text
            
            # Try general desc-content
            desc_content = desc_wrap.find('div', class_='desc-content')
            if desc_content:
                # Remove read-toggle links
                for link in desc_content.find_all('a', class_='read-toggle'):
                    link.decompose()
                text = desc_content.get_text(separator='\n', strip=True)
                if text:
                    return text
        
        # Try property-description as fallback
        desc = soup.find('div', class_='property-description')
        if desc:
            return desc.get_text(separator='\n', strip=True)
        
        # Try meta description as last resort
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '').strip()
            if content:
                return content
        
        return super().extract_description(soup)
    
    def extract_amenities(self, soup: BeautifulSoup) -> list:
        """Extract amenities from property-features."""
        amenities = []
        features_section = soup.find('div', class_='property-features')
        if features_section:
            # Find list items
            items = features_section.find_all('li')
            for item in items:
                amenity = item.get_text(strip=True)
                if amenity:
                    amenities.append(amenity)
        
        return amenities if amenities else super().extract_amenities(soup)
    
    def extract_latitude(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract latitude from map iframe."""
        # Look for Google Maps iframe
        iframe = soup.find('iframe', src=lambda x: x and 'google.com/maps' in x)
        if iframe:
            src = iframe.get('src', '')
            # Extract coordinates from iframe src
            # Format: https://maps.google.com/maps?q=LAT,LNG&...
            match = re.search(r'[?&]q=([-\d.]+),([-\d.]+)', src)
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    pass
        
        # Try map-container data attributes
        map_container = soup.find('div', class_='map-container')
        if map_container:
            lat = map_container.get('data-lat') or map_container.get('data-latitude')
            if lat:
                try:
                    return Decimal(lat)
                except:
                    pass
        
        return super().extract_latitude(soup)
    
    def extract_longitude(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract longitude from map iframe."""
        # Look for Google Maps iframe
        iframe = soup.find('iframe', src=lambda x: x and 'google.com/maps' in x)
        if iframe:
            src = iframe.get('src', '')
            match = re.search(r'[?&]q=([-\d.]+),([-\d.]+)', src)
            if match:
                try:
                    return Decimal(match.group(2))
                except:
                    pass
        
        # Try map-container data attributes
        map_container = soup.find('div', class_='map-container')
        if map_container:
            lng = map_container.get('data-lng') or map_container.get('data-longitude')
            if lng:
                try:
                    return Decimal(lng)
                except:
                    pass
        
        return super().extract_longitude(soup)
    
    def extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract full location string."""
        # Try to find h3 with location info in main content sections
        sections = soup.find_all('section')
        for section in sections:
            h3_tags = section.find_all('h3')
            for h3 in h3_tags:
                text = h3.get_text(strip=True)
                # Check if it contains location keywords
                if 'ubicación:' in text.lower() or 'location:' in text.lower():
                    # Split and get the part after the colon
                    parts = text.split(':', 1)
                    if len(parts) > 1:
                        location = parts[1].strip()
                        if location:
                            return location
        
        # Try location-wrap section
        location_section = soup.find('div', class_='location-wrap')
        if location_section:
            # Try to find address in the section
            addr = location_section.find('address')
            if addr:
                return addr.get_text(strip=True)
            
            # Or try paragraphs
            paragraphs = location_section.find_all('p')
            if paragraphs:
                return paragraphs[0].get_text(strip=True)
        
        # Fallback: Use OpenAI to extract location from description
        description = self.extract_description(soup)
        if description and len(description) > 50:
            try:
                location = self._extract_location_with_ai(description)
                if location:
                    return location
            except Exception as e:
                print(f"Error extracting location with AI: {e}")
        
        return super().extract_location(soup)
    
    def extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract address from location-wrap or any h3 with location info."""
        # Try to find h3 with location info in main content sections
        sections = soup.find_all('section')
        for section in sections:
            h3_tags = section.find_all('h3')
            for h3 in h3_tags:
                text = h3.get_text(strip=True)
                # Check if it contains location keywords
                if 'ubicación:' in text.lower() or 'location:' in text.lower():
                    # Split and get the part after the colon
                    parts = text.split(':', 1)
                    if len(parts) > 1:
                        location = parts[1].strip()
                        if location:
                            return location
        
        # Try location-wrap section
        location_section = soup.find('div', class_='location-wrap')
        if location_section:
            # Try to find address in the section
            addr = location_section.find('address')
            if addr:
                return addr.get_text(strip=True)
            
            # Or try paragraphs
            paragraphs = location_section.find_all('p')
            if paragraphs:
                return paragraphs[0].get_text(strip=True)
        
        # Fallback: Use OpenAI to extract location from description
        description = self.extract_description(soup)
        if description and len(description) > 50:
            try:
                location = self._extract_location_with_ai(description)
                if location:
                    return location
            except Exception as e:
                print(f"Error extracting location with AI: {e}")
        
        return super().extract_address(soup)
    
    def _extract_location_with_ai(self, description: str) -> Optional[str]:
        """Use OpenAI to extract location from description."""
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            instruction = "Extract the location (city, region, country) from this property description. Return ONLY the location in format: 'City, Region' or 'City, Region, Country'. If no clear location is found, return 'Unknown'."
            prompt = f"{instruction}\n\nDescription:\n{description[:1000]}\n\nLocation:"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a real estate data extraction assistant. Extract location information accurately and concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=100
            )
            
            location = response.choices[0].message.content.strip()
            
            # Validate the response
            if location and location.lower() not in ['unknown', 'n/a', 'none', '']:
                return location
            
            return None
            
        except Exception as e:
            print(f"OpenAI extraction error: {e}")
            return None
