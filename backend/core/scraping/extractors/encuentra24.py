"""Encuentra24.com specific extractor.
"""

from typing import Optional
from bs4 import BeautifulSoup
from decimal import Decimal
import re
import json
import openai
from django.conf import settings
from .base import BaseExtractor


class Encuentra24Extractor(BaseExtractor):
    """Extractor for encuentra24.com listings."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "encuentra24.com"
    
    def extract(self, html: str, url: Optional[str] = None):
        """Override extract to include custom fields and AI enhancement.
        
        OPTIMIZATION STRATEGY:
        1. Extract relevant HTML sections (property details, amenities, etc.)
        2. Pass compact semantic HTML to AI for intelligent extraction
        3. AI uses HTML structure to identify fields accurately
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # STEP 1: Extract relevant HTML sections (semantic structure)
        relevant_html = self.extract_relevant_html_sections(soup)
        print(f"📦 HTML relevante extraído: {len(relevant_html)} caracteres")
        
        # STEP 2: Extract construction stage from timeline
        construction_stage = self.extract_construction_stage(soup)
        
        # STEP 3: Use AI to extract all fields from semantic HTML
        ai_enhanced_data = self.enhance_with_ai_html(relevant_html, construction_stage, url)
        
        # STEP 4: Merge robust manual extraction (User feedback fix)
        manual_desc = self.extract_description(soup)
        if manual_desc:
            # Prefer manual description if longer/present
            if not ai_enhanced_data.get('description') or len(manual_desc) > len(ai_enhanced_data.get('description', '')):
                ai_enhanced_data['description'] = manual_desc

        manual_benefits = self.extract_benefits(soup)
        if manual_benefits:
            current_amenities = ai_enhanced_data.get('amenities', []) or []
            # Merge unique benefits
            ai_enhanced_data['amenities'] = list(set(current_amenities + manual_benefits))
        
        # STEP 5: Add custom fields
        ai_enhanced_data['listing_id'] = self.extract_listing_id(soup)
        ai_enhanced_data['date_listed'] = self.extract_date_listed(soup)
        ai_enhanced_data['construction_stage'] = construction_stage
        
        return ai_enhanced_data
    
    
    def extract_relevant_html_sections(self, soup: BeautifulSoup) -> str:
        """Extract only relevant HTML sections for AI processing.
        
        Strategy: Find sections with property details, specs, amenities using:
        - Common CSS class patterns (detail, info, spec, feature, amenity)
        - Semantic HTML structures (dl/dt/dd, table, ul/li)
        - Remove images, scripts, styles, and other noise
        
        Returns compact semantic HTML with property data structure intact.
        """
        relevant_sections = []
        
        # 1. Search by common class name patterns (case-insensitive)
        patterns = [
            'detail', 'info', 'spec', 'feature', 'amenity', 
            'characteristic', 'attribute', 'insight', 'about',
            'description', 'descripción'
        ]
        
        for pattern in patterns:
            sections = soup.find_all(class_=re.compile(pattern, re.I))
            for section in sections:
                # Skip if already added
                if section not in relevant_sections:
                    relevant_sections.append(section)
        
        # 2. Search by semantic HTML structures
        relevant_sections.extend(soup.find_all(['dl', 'table']))
        
        # 3. Search for title/header
        title = soup.find('h1')
        if title and title not in relevant_sections:
            relevant_sections.insert(0, title)
        
        # 4. Clean each section
        cleaned_html = []
        for section in relevant_sections[:15]:  # Limit to first 15 sections
            # Clone section to avoid modifying original
            section_copy = BeautifulSoup(str(section), 'html.parser')
            
            # Remove noise: scripts, styles, images, links to images
            for tag in section_copy.find_all(['script', 'style', 'img', 'svg', 'iframe']):
                tag.decompose()
            
            # Remove image links (a tags with img inside or image URLs)
            for a_tag in section_copy.find_all('a'):
                href = a_tag.get('href', '')
                if any(ext in href.lower() for ext in ['.jpg', '.png', '.gif', '.webp', '.jpeg']):
                    a_tag.decompose()
                elif a_tag.find('img'):
                    a_tag.decompose()
            
            # Get cleaned HTML
            section_html = str(section_copy)
            
            # Skip if too small or empty
            if len(section_html.strip()) > 20:
                cleaned_html.append(section_html)
        
        # 5. Join sections and limit total size
        combined_html = '\n'.join(cleaned_html)
        
        # Limit to reasonable size (~8KB max)
        if len(combined_html) > 8000:
            combined_html = combined_html[:8000]
        
        return combined_html
    
    def enhance_with_ai_html(self, relevant_html: str, construction_stage: str, url: Optional[str]) -> dict:
        """Use OpenAI to extract property data from semantic HTML.
        
        The AI receives HTML structure which helps it accurately identify:
        - Field labels and values (from dt/dd, th/td patterns)
        - Lists and arrays (from ul/li patterns)
        - Hierarchical data (from nested divs with classes)
        
        This prevents confusion like "Precio/M² $4,100" being mistaken for area.
        """
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("⚠️ OpenAI API key not configured, skipping AI enhancement")
                return {}
            
            client = openai.OpenAI(api_key=api_key)
            
            # Detect listing type from URL
            listing_type_hint = None
            if url:
                if 'venta' in url.lower() or 'sale' in url.lower():
                    listing_type_hint = 'sale'
                elif 'alquiler' in url.lower() or 'rent' in url.lower():
                    listing_type_hint = 'rent'
            
            # Build optimized prompt
            prompt = f"""Extract property data from this HTML structure. Use the semantic HTML tags and classes to identify fields accurately.

HTML:
{relevant_html}

CONSTRUCTION STAGE: {construction_stage or 'Not specified'}
URL HINT: listing_type is likely "{listing_type_hint}" (from URL pattern)

Extract these fields in JSON format:
{{
  "title": "Property name/title",
  "price_usd": <numeric USD price, NOT price per m²>,
  "bedrooms": <integer or null>,
  "bathrooms": <integer or null>,
  "area_m2": <construction area in m², NOT price per m²>,
  "lot_size_m2": <lot/land size in m²>,
  "property_type": "Casa|Apartamento|Terreno|etc",
  "listing_type": "sale|rent",
  "location": "City, Province, Country",
  "amenities": ["amenity1", "amenity2"],
  "parking_spaces": <integer or null>,
  "pool": <true/false>,
  "description": "Brief summary in English (2-3 sentences)"
}}

CRITICAL:
- Look for <dt>Parking</dt><dd>3</dd> patterns for exact values
- "M² construcción" or "Construcción" = area_m2
- "M² terreno" or "Terreno" = lot_size_m2
- "Precio/M²" is NOT area_m2, ignore it
- Use listing_type from URL hint if not found in HTML
- Return valid JSON only"""
            
            # Save for debugging
            try:
                with open('ai_html_input.txt', 'w', encoding='utf-8') as f:
                    f.write(f"=== PROMPT ===\n{prompt}\n\n=== HTML ===\n{relevant_html}")
                print(f"💾 HTML y prompt guardados en: ai_html_input.txt")
            except Exception as e:
                print(f"⚠️ No se pudo guardar archivo: {e}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a real estate data extraction expert. Extract property information from HTML structure accurately. Return clean JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1200
            )
            
            print(f"📊 Tokens usados: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = re.sub(r'^```(?:json)?\s*\n', '', content)
                content = re.sub(r'\n```\s*$', '', content)
            
            extracted_data = json.loads(content)
            print(f"✅ AI extrajo {len(extracted_data)} campos exitosamente")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI response: {e}")
            print(f"Response content: {content[:200]}")
            return {}
        except Exception as e:
            print(f"❌ Error in AI enhancement: {e}")
            return {}
    
    def extract_structured_html_data(self, soup: BeautifulSoup) -> dict:
        """Extract structured data directly from HTML using CSS selectors.
        
        This method extracts precise data from d3-property-insight__attribute sections:
        - Parking spaces
        - Bedrooms
        - Bathrooms
        - Area m²
        - Lot size
        - Pool
        - Floor
        - Property type
        
        Returns exact values from HTML, no AI interpretation needed.
        """
        data = {}
        
        # Find all property insight attributes (the structured data sections)
        attributes = soup.find_all('div', class_='d3-property-insight__attribute')
        
        for attr in attributes:
            # Get the title (e.g., "Parking", "Recámaras", "Baños")
            title_elem = attr.find('dt', class_='d3-property-insight__attribute-title')
            value_elem = attr.find('dd', class_='d3-property-insight__attribute-value')
            
            if not title_elem or not value_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            value = value_elem.get_text(strip=True)
            
            # Map to standard field names
            if 'Parking' in title:
                try:
                    data['parking_spaces'] = int(value)
                    print(f"✅ Parking extraído: {value}")
                except ValueError:
                    data['parking_spaces'] = value
            
            elif 'Recámara' in title or 'Habitación' in title:
                try:
                    data['bedrooms'] = int(value)
                    print(f"✅ Recámaras extraídas: {value}")
                except ValueError:
                    data['bedrooms'] = value
            
            elif 'Baño' in title:
                try:
                    data['bathrooms'] = int(value)
                    print(f"✅ Baños extraídos: {value}")
                except ValueError:
                    data['bathrooms'] = value
            
            elif 'M² construcción' in title or 'Construcción' in title:
                # Extract numeric value from "400 M²" or "400"
                try:
                    numeric_value = re.search(r'[\d,]+', value.replace("'", ""))
                    if numeric_value:
                        area_str = numeric_value.group().replace(',', '')
                        data['area_m2'] = int(area_str)
                        print(f"✅ Área extraída: {area_str} m²")
                except ValueError:
                    pass
            
            elif 'M² terreno' in title or 'Terreno' in title:
                try:
                    numeric_value = re.search(r'[\d,]+', value.replace("'", ""))
                    if numeric_value:
                        lot_str = numeric_value.group().replace(',', '')
                        data['lot_size_m2'] = int(lot_str)
                        print(f"✅ Terreno extraído: {lot_str} m²")
                except ValueError:
                    pass
            
            elif 'Piscina' in title or 'Pool' in title:
                data['pool'] = value.lower() in ['sí', 'si', 'yes', 'true', '1']
                print(f"✅ Piscina extraída: {data['pool']}")
            
            elif 'Piso' in title or 'Floor' in title:
                data['floor'] = value
                print(f"✅ Piso extraído: {value}")
            
            elif 'Tipo' in title or 'Type' in title:
                data['property_type'] = value
                print(f"✅ Tipo extraído: {value}")
        
        # Also check d3-property-details__content section for price
        content_div = soup.find('div', class_='d3-property-details__content')
        if content_div:
            labels = content_div.find_all('div', class_='d3-property-details__detail-label')
            for label_div in labels:
                label_text = label_div.get_text(strip=True)
                detail_p = label_div.find('p', class_='d3-property-details__detail')
                
                if detail_p:
                    detail_text = detail_p.get_text(strip=True)
                    
                    if 'Precio' in label_text and 'M²' not in label_text:
                        # Extract price (e.g., "$400'000" -> 400000)
                        try:
                            price_clean = detail_text.replace("'", "").replace(",", "").replace("$", "").strip()
                            numeric_value = re.search(r'\d+', price_clean)
                            if numeric_value:
                                data['price_usd'] = int(numeric_value.group())
                                print(f"✅ Precio extraído: ${data['price_usd']}")
                        except ValueError:
                            pass
        
        # Extract title from h1
        title_elem = soup.find('h1')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
            print(f"✅ Título extraído: {data['title'][:50]}...")
        
        # Extract location from breadcrumb or location section
        location_section = soup.find('div', class_='d3-property-location')
        if location_section:
            location_text = location_section.get_text(strip=True)
            if location_text:
                data['location'] = location_text
                print(f"✅ Ubicación extraída: {location_text}")
        
        # Detect listing type from URL or page structure
        # URL patterns: /venta-de-propiedades/ = sale, /alquiler/ = rent
        url_text = str(soup)
        if 'venta-de-propiedades' in url_text or 'venta-casas' in url_text or 'venta-apartamentos' in url_text:
            data['listing_type'] = 'sale'
            print(f"✅ Tipo de listado extraído: sale (desde URL)")
        elif 'alquiler' in url_text or 'rent' in url_text:
            data['listing_type'] = 'rent'
            print(f"✅ Tipo de listado extraído: rent (desde URL)")
        
        return data
    
    def extract_structured_details(self, soup: BeautifulSoup) -> dict:
        """Extract all details from d3-property-details__content section."""
        details = {}
        
        # Find the content section
        content_div = soup.find('div', class_='d3-property-details__content')
        if not content_div:
            return details
        
        # Extract all label-detail pairs
        labels = content_div.find_all('div', class_='d3-property-details__detail-label')
        
        for label_div in labels:
            label_text = label_div.get_text(strip=True)
            detail_p = label_div.find('p', class_='d3-property-details__detail')
            
            if detail_p:
                detail_text = detail_p.get_text(strip=True)
                
                # Parse different fields
                if 'Categoria' in label_text or 'Categoría' in label_text:
                    details['category'] = detail_text
                elif 'Localización' in label_text or 'Ubicación' in label_text:
                    details['location'] = detail_text
                elif 'Modelo' in label_text:
                    details['model'] = detail_text
                elif 'Precio' in label_text and 'M²' not in label_text:
                    # Remove quotes and parse price
                    price_clean = detail_text.replace("'", "").replace(",", "").strip()
                    details['price_text'] = price_clean
                    try:
                        details['price'] = int(re.sub(r'[^\d]', '', price_clean))
                    except:
                        pass
                elif 'Precio / m²' in label_text or 'Precio / M²' in label_text:
                    details['price_per_sqm'] = detail_text
                elif 'M²' in label_text and 'Precio' not in label_text:
                    details['area_m2'] = detail_text
                elif 'Recámara' in label_text or 'Recamara' in label_text:
                    try:
                        details['bedrooms'] = int(detail_text)
                    except:
                        details['bedrooms'] = detail_text
                elif 'Baño' in label_text:
                    try:
                        details['bathrooms'] = int(detail_text)
                    except:
                        details['bathrooms'] = detail_text
                elif 'Parking' in label_text:
                    details['parking'] = detail_text
                elif 'Piscina' in label_text:
                    details['pool'] = detail_text
                elif 'Piso' in label_text:
                    details['floor'] = detail_text
                else:
                    # Store any other detail
                    clean_label = label_text.replace(':', '').strip()
                    details[clean_label.lower()] = detail_text
        
        return details
    
    def extract_all_text(self, soup: BeautifulSoup) -> str:
        """Extract ALL relevant visible text from the page, organized by sections."""
        sections = []
        
        # 1. Title/Header
        title = soup.find('h1')
        if title:
            sections.append(f"TÍTULO: {title.get_text(strip=True)}")
        
        # 2. Property Details Section (d3-property-details__content)
        details_section = soup.find('div', class_='d3-property-details__content')
        if details_section:
            details_text = []
            labels = details_section.find_all('div', class_='d3-property-details__detail-label')
            for label in labels:
                label_text = label.get_text(strip=True)
                detail = label.find('p', class_='d3-property-details__detail')
                if detail:
                    detail_text = detail.get_text(strip=True)
                    details_text.append(f"{label_text} {detail_text}")
            if details_text:
                sections.append("DETALLES:\n" + "\n".join(details_text))
        
        # 3. Description (d3-property-about__text)
        description = soup.find('div', class_='d3-property-about__text')
        if description:
            desc_text = description.get_text(strip=True)
            if desc_text:
                sections.append(f"DESCRIPCIÓN:\n{desc_text}")
        
        # 4. Amenities/Features section
        amenities_section = soup.find('div', class_='d3-property-features')
        if amenities_section:
            amenities = amenities_section.find_all('li')
            if amenities:
                amenity_list = [li.get_text(strip=True) for li in amenities]
                sections.append("AMENIDADES:\n" + "\n".join(amenity_list))
        
        # 5. Location information
        location = soup.find('div', class_='d3-property-location')
        if location:
            loc_text = location.get_text(strip=True)
            if loc_text:
                sections.append(f"UBICACIÓN:\n{loc_text}")
        
        # Join all sections with clear separators
        return "\n\n".join(sections)
    
    def extract_construction_stage(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract construction stage from timeline or details."""
        # 1. Timeline extraction
        timeline = soup.find('div', class_='d3-new-property-stage__time-line')
        if timeline:
            active_items = timeline.find_all('div', class_='d3-new-property-stage__time-line-item--active')
            if active_items:
                last_active = active_items[-1]
                label = last_active.find('p', class_='d3-new-property-stage__time-line-label')
                if label:
                    return label.get_text(strip=True)
        
        # 2. Text details extraction (User report: "Etapa de inversión")
        # Look in the details section
        details_content = soup.find('div', class_='d3-property-details__content')
        if details_content:
            labels = details_content.find_all('div', class_='d3-property-details__detail-label')
            for label in labels:
                if 'Etapa' in label.get_text():
                    detail = label.find('p', class_='d3-property-details__detail')
                    if detail:
                        return detail.get_text(strip=True)
        
        return None

    def extract_benefits(self, soup: BeautifulSoup) -> list:
        """Extract benefits/highlights section."""
        benefits = []
        
        # Look for "Beneficios" header
        headers = soup.find_all(['h2', 'h3', 'div'], string=re.compile(r'Beneficios', re.I))
        for header in headers:
            # The list usually follows the header
            # It might be in a ul next to it or in a container
            parent = header.parent
            if parent:
                # Try to find list items in parent or siblings
                items = parent.find_all('li')
                if not items:
                    # Look in next sibling
                    sibling = header.find_next_sibling()
                    if sibling:
                        items = sibling.find_all('li')
                
                for item in items:
                    benefits.append(item.get_text(strip=True))
        
        return benefits

    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description (Acerca de)."""
        # User reported "Acerca de" section
        
        # 1. Try d3-property-about__text (standard new design)
        desc = soup.find(class_='d3-property-about__text')
        if desc:
            for br in desc.find_all('br'):
                br.replace_with('\n')
            text = desc.get_text(strip=True)
            if text and len(text) > 20:
                return text

        # 2. Look for "Acerca de" header and get following text
        headers = soup.find_all(['h2', 'h3', 'div'], string=re.compile(r'Acerca de', re.I))
        for header in headers:
            # The text usually follows
            content = header.find_next_sibling('div') or header.find_next_sibling('p')
            if content:
                text = content.get_text(separator='\n', strip=True)
                if len(text) > 20:
                    return text
        
        # 3. Fallback to older extractors
        return super().extract_description(soup)
    
    def enhance_with_ai(self, full_text: str, construction_stage: str, structured_data: dict) -> dict:
        """Use OpenAI to process clean text and extract ONLY unstructured fields.
        
        This method only extracts fields that weren't found in structured HTML:
        - Description (always from AI, needs summarization)
        - Amenities (may be in free-form text)
        - Complex fields that need interpretation
        
        Structured fields (parking, bedrooms, etc.) are skipped to save tokens.
        """
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("⚠️ OpenAI API key not configured, skipping AI enhancement")
                return {}
            
            client = openai.OpenAI(api_key=api_key)
            
            # Limit text to reasonable size
            text_to_process = full_text[:6000] if len(full_text) > 6000 else full_text
            
            # Build list of fields to extract (only what's missing)
            fields_to_extract = []
            
            # Always extract description and amenities (unstructured)
            fields_to_extract.append("description")
            fields_to_extract.append("amenities")
            
            # Only ask AI for structured fields if not found in HTML
            if 'title' not in structured_data:
                fields_to_extract.append("title")
            if 'price_usd' not in structured_data:
                fields_to_extract.append("price_usd")
            if 'bedrooms' not in structured_data:
                fields_to_extract.append("bedrooms")
            if 'bathrooms' not in structured_data:
                fields_to_extract.append("bathrooms")
            if 'area_m2' not in structured_data:
                fields_to_extract.append("area_m2")
            if 'lot_size_m2' not in structured_data:
                fields_to_extract.append("lot_size_m2")
            if 'property_type' not in structured_data:
                fields_to_extract.append("property_type")
            if 'listing_type' not in structured_data:
                fields_to_extract.append("listing_type")
            if 'location' not in structured_data:
                fields_to_extract.append("location")
            if 'parking_spaces' not in structured_data:
                fields_to_extract.append("parking_spaces")
            if 'pool' not in structured_data:
                fields_to_extract.append("pool")
            
            # New financial/details fields
            fields_to_extract.append("hoa_fee")
            fields_to_extract.append("taxes")
            fields_to_extract.append("year_built")
            
            print(f"🤖 AI extraerá {len(fields_to_extract)} campos: {', '.join(fields_to_extract)}")
            
            # Build optimized prompt
            prompt = f"""Extract real estate property information from this Costa Rica listing.

PROPERTY TEXT:
{text_to_process}

CONSTRUCTION STAGE: {construction_stage or 'Not specified'}

Extract ONLY these fields (in JSON format):
{', '.join(fields_to_extract)}

Guidelines:
- Use null for missing values
- listing_type: "sale" or "rent"
- property_type: Casa, Apartamento, Terreno, Local Comercial, etc.
- parking_spaces: integer or null
- pool: true/false
- amenities: array of strings
- description: brief summary in English (2-3 sentences max)
- area_m2: construction area in square meters
- lot_size_m2: lot/land size in square meters
- hoa_fee: monthly maintenance fee (number)
- taxes: yearly property taxes (number)
- year_built: year of construction (number)
- video_url: link to YouTube/Vimeo video
- brochure_url: link to PDF brochure

Return valid JSON only."""
            
            # Save prompt for debugging
            try:
                with open('ai_prompt_optimized.txt', 'w', encoding='utf-8') as f:
                    f.write(prompt)
                print(f"💾 Prompt optimizado guardado ({len(prompt)} caracteres vs {len(full_text)} original)")
            except Exception as e:
                print(f"⚠️ No se pudo guardar archivo: {e}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a real estate data extraction expert. Extract property information accurately and return clean JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500
            )
            
            print(f"📊 Tokens usados: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = re.sub(r'^```(?:json)?\s*\n', '', content)
                content = re.sub(r'\n```\s*$', '', content)
            
            extracted_data = json.loads(content)
            print(f"✅ AI extrajo {len(extracted_data)} campos exitosamente")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI response: {e}")
            print(f"Response content: {content[:200]}")
            return {}
        except Exception as e:
            print(f"❌ Error in AI enhancement: {e}")
            return {}
    
    def extract_listing_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing ID from URL or page."""
        # Try to find in URL (e.g., /31786735 at the end)
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href'):
            url = canonical['href']
            match = re.search(r'/(\d+)$', url)
            if match:
                return match.group(1)
        return None
    
    def extract_date_listed(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing date if available."""
        # Look for date in meta tags or structured data
        date_meta = soup.find('meta', {'property': 'article:published_time'})
        if date_meta and date_meta.get('content'):
            return date_meta['content']
        return None
    
    def _dict_to_text(self, d: dict) -> str:
        """Convert dict to readable text format."""
        lines = []
        for key, value in d.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property title from Encuentra24."""
        # Try d3-property-details__title (new design)
        title = soup.find(class_='d3-property-details__title')
        if title:
            return title.get_text(strip=True)
        
        # Try property-detail section (old design)
        title = soup.find('h1', class_='property-detail')
        if title:
            return title.get_text(strip=True)
        
        # Try property-info section
        title = soup.find('h1', class_='property-info')
        if title:
            return title.get_text(strip=True)
        
        return super().extract_title(soup)
    
    def extract_price(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract price from property details."""
        # Try d3-property-insight__attribute-details (new design)
        insights = soup.find_all(class_='d3-property-insight__attribute-details')
        for insight in insights:
            text = insight.get_text(strip=True)
            # Check for USD price
            usd_match = re.search(r'\$\s*([\d,]+)', text)
            if usd_match:
                price_str = usd_match.group(1).replace(',', '')
                try:
                    return Decimal(price_str)
                except:
                    pass
            
            # Check for CRC (colones) price
            crc_match = re.search(r'₡\s*([\d,]+)', text)
            if crc_match:
                price_str = crc_match.group(1).replace(',', '')
                try:
                    # Convert CRC to USD (approximate rate: 1 USD = 520 CRC)
                    crc_price = Decimal(price_str)
                    usd_price = crc_price / Decimal('520')
                    return usd_price.quantize(Decimal('0.01'))
                except:
                    pass
        
        # Look in property-detail or property-info sections (old design)
        for class_name in ['property-detail', 'property-info', 'listing-detail']:
            section = soup.find(class_=class_name)
            if section:
                price_text = section.get_text()
                match = re.search(r'\$\s*([\d,]+)', price_text)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        return Decimal(price_str)
                    except:
                        pass
        
        return super().extract_price(soup)
    
    def extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract bedrooms from property details."""
        # Try d3-property-insight__attribute-details (new design)
        insights = soup.find_all(class_='d3-property-insight__attribute-details')
        for insight in insights:
            text = insight.get_text(strip=True)
            match = re.search(r'(\d+)\s*(recamara|recámara|habitacion|habitación|bedroom|dormitorio)', text, re.IGNORECASE)
            if not match:
                # Try with number after the word (e.g., "Recámaras2")
                match = re.search(r'(recamara|recámara|habitacion|habitación|bedroom|dormitorio)s?\s*(\d+)', text, re.IGNORECASE)
                if match:
                    return int(match.group(2))
            else:
                return int(match.group(1))
        
        # Search in property sections (old design)
        for class_name in ['property-detail', 'property-info', 'listing-detail']:
            section = soup.find(class_=class_name)
            if section:
                text = section.get_text()
                match = re.search(r'(\d+)\s*(recamara|recámara|habitacion|habitación|bedroom|dormitorio)', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        
        return super().extract_bedrooms(soup)
    
    def extract_bathrooms(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract bathrooms from property details."""
        # Try d3-property-insight__attribute-details (new design)
        insights = soup.find_all(class_='d3-property-insight__attribute-details')
        for insight in insights:
            text = insight.get_text(strip=True)
            match = re.search(r'(\d+\.?\d*)\s*(baño|baños|bathroom)', text, re.IGNORECASE)
            if not match:
                # Try with number after the word (e.g., "Baños2")
                match = re.search(r'(baño|baños|bathroom)s?\s*(\d+\.?\d*)', text, re.IGNORECASE)
                if match:
                    return Decimal(match.group(2))
            else:
                return Decimal(match.group(1))
        
        # Search in property sections (old design)
        for class_name in ['property-detail', 'property-info', 'listing-detail']:
            section = soup.find(class_=class_name)
            if section:
                text = section.get_text()
                match = re.search(r'(\d+\.?\d*)\s*(baño|baños|bathroom)', text, re.IGNORECASE)
                if match:
                    return Decimal(match.group(1))
        
        return super().extract_bathrooms(soup)
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description."""
        # Try d3-property-about__text (new design)
        desc = soup.find(class_='d3-property-about__text')
        if desc:
            # Remove all <br> tags and get clean text
            for br in desc.find_all('br'):
                br.replace_with('\n')
            text = desc.get_text(strip=True)
            if text and len(text) > 20:
                return text
        
        # Try description class (most common)
        desc = soup.find(class_='description')
        if desc:
            text = desc.get_text(separator='\n', strip=True)
            if text and len(text) > 20:
                return text
        
        # Try property-detail or listing-detail sections
        for class_name in ['property-detail', 'property-info', 'listing-detail']:
            desc = soup.find('div', class_=class_name)
            if desc:
                # Find paragraphs within
                paragraphs = desc.find_all('p')
                if paragraphs:
                    return '\n'.join([p.get_text(strip=True) for p in paragraphs])
        
        return super().extract_description(soup)
    
    def extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from property details."""
        # Try breadcrumb or location elements
        breadcrumb = soup.find(class_='adaptor-breadcrumb-detailpager')
        if breadcrumb:
            # Extract location from breadcrumb text
            text = breadcrumb.get_text(strip=True)
            # Look for location patterns
            match = re.search(r'(Alquiler|Venta)\s+de\s+[^>]+>\s*([^>]+)', text)
            if match:
                location = match.group(2).strip()
                if location and len(location) > 2:
                    return location
        
        # Try to find location in title
        title = self.extract_title(soup)
        if title:
            # Extract location from patterns like "Casa en San José"
            match = re.search(r'\ben\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)', title)
            if match:
                location = match.group(1)
                if location and len(location) > 2:
                    return location
        
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
    
    def extract_listing_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing ID/reference number."""
        # Try d3-property-details__code class
        code_span = soup.find('span', class_='d3-property-details__code')
        if code_span:
            text = code_span.get_text(strip=True)
            # Extract number from "Ref.: 2315"
            ref_match = re.search(r'Ref\.?:\s*(\d+)', text, re.IGNORECASE)
            if ref_match:
                return ref_match.group(1)
        
        # Fallback: search in full text
        text = soup.get_text()
        ref_match = re.search(r'Ref\.?:\s*(\d+)', text, re.IGNORECASE)
        if ref_match:
            return ref_match.group(1)
        
        # Try to find ID in URL or message text like "(31846620)"
        id_match = re.search(r'\((\d{8})\)', text)
        if id_match:
            return id_match.group(1)
        
        return None
    
    def extract_property_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property type (Casa, Apartamento, etc.)."""
        # Try to find in title or breadcrumb
        title = self.extract_title(soup)
        if title:
            # Look for property types in Spanish
            types = {
                'casa': 'Casa',
                'casas': 'Casa',
                'apartamento': 'Apartamento',
                'apto': 'Apartamento',
                'terreno': 'Terreno',
                'lote': 'Lote',
                'bodega': 'Bodega',
                'local': 'Local Comercial',
                'oficina': 'Oficina',
                'finca': 'Finca',
                'quinta': 'Quinta'
            }
            
            title_lower = title.lower()
            for key, value in types.items():
                if key in title_lower:
                    return value
        
        return None
    
    def extract_listing_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing type (Alquiler/Venta)."""
        # Try d3-property-insight__attribute-details
        insights = soup.find_all(class_='d3-property-insight__attribute-details')
        for insight in insights:
            text = insight.get_text(strip=True)
            if 'Alquiler' in text:
                return 'rent'
            if 'Venta' in text:
                return 'sale'
        
        # Try in title or breadcrumb
        text = soup.get_text()
        if re.search(r'\bAlquiler\b', text, re.IGNORECASE):
            return 'rent'
        if re.search(r'\bVenta\b', text, re.IGNORECASE):
            return 'sale'
        
        return None
    
    def extract_lot_size(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract lot size (M² totales)."""
        # Find all d3-property-details__detail-label
        labels = soup.find_all('div', class_='d3-property-details__detail-label')
        for label in labels:
            text = label.get_text(strip=True)
            # Look for "M² totales120" pattern (label and value together)
            match = re.search(r'M?²?\s*totales\s*([\d,]+)', text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    return Decimal(value_str)
                except:
                    pass
        
        return super().extract_lot_size(soup)
    
    def extract_date_listed(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing date (Publicado 11/01/2026)."""
        # Find all d3-property-details__detail-label
        labels = soup.find_all('div', class_='d3-property-details__detail-label')
        for label in labels:
            text = label.get_text(strip=True)
            # Look for "Publicado11/01/2026" pattern (label and value together)
            match = re.search(r'Publicado\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Convert to ISO format: DD/MM/YYYY -> YYYY-MM-DD
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    return date_str
        
        return None
