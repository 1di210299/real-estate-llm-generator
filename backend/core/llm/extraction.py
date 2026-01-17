"""
LLM-powered property extraction from HTML/text.
"""

import json
import logging
from typing import Dict, Optional
from decimal import Decimal

import openai
from django.conf import settings
from django.utils import timezone

from .prompts import PROPERTY_EXTRACTION_PROMPT
from .content_types import get_extraction_prompt, CONTENT_TYPES

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""
    pass


class PropertyExtractor:
    """
    Extract structured data from unstructured HTML/text using LLM.
    Supports multiple content types: real_estate, tour, restaurant, local_tips, transportation.
    """
    
    def __init__(self, content_type: str = 'real_estate', page_type: str = 'specific'):
        """
        Initialize extractor.
        
        Args:
            content_type: Type of content to extract (real_estate, tour, restaurant, etc.)
            page_type: Type of page ('specific' for single item, 'general' for guides/listings)
        """
        api_key = settings.OPENAI_API_KEY
        logger.info(f"🔑 OPENAI_API_KEY configured: {'Yes' if api_key else 'No'}")
        logger.info(f"🔑 API Key length: {len(api_key) if api_key else 0} chars")
        logger.info(f"🔑 API Key preview: {api_key[:10]}..." if api_key and len(api_key) > 10 else "🔑 API Key: EMPTY or TOO SHORT")
        
        if not api_key:
            logger.error("❌ OPENAI_API_KEY is empty! Check environment variables.")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Validate content type
        if content_type not in CONTENT_TYPES:
            logger.warning(f"⚠️ Unknown content type: {content_type}, defaulting to real_estate")
            content_type = 'real_estate'
        
        # Validate page type
        if page_type not in ['specific', 'general']:
            logger.warning(f"⚠️ Unknown page type: {page_type}, defaulting to specific")
            page_type = 'specific'
        
        self.content_type = content_type
        self.page_type = page_type
        self.client = openai.OpenAI(api_key=api_key)
        self.model = settings.OPENAI_MODEL_CHAT
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = 0.1  # Low temperature for consistent extraction
        
        logger.info(f"📝 Extractor initialized for content type: {content_type}, page type: {page_type}")
    
    def _clean_content(self, content: str) -> str:
        """Clean and truncate content for LLM processing."""
        from bs4 import BeautifulSoup
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract key sections
        important_text = []
        
        # 1. Title and meta description
        title = soup.find('title')
        if title:
            important_text.append(f"TITLE: {title.get_text(strip=True)}")
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            important_text.append(f"META DESCRIPTION: {meta_desc['content']}")
        
        # 2. ALL headings (h1-h6) - often contain key info like prices, features, sections
        for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headings = soup.find_all(heading_tag)
            for heading in headings:
                text = heading.get_text(strip=True)
                if text and len(text) > 2:
                    important_text.append(f"HEADING ({heading_tag.upper()}): {text}")
        
        # 3. Property details sections (common patterns)
        detail_patterns = [
            {'class': lambda x: x and any(word in str(x).lower() for word in 
                ['show__', 'product', 'detail', 'property', 'tour', 'rate', 'price', 'cost', 'schedule', 'info', 'feature', 'highlight'])},
            {'id': lambda x: x and any(word in x.lower() for word in 
                ['detail', 'overview', 'price', 'rate', 'schedule', 'info', 'description', 'feature'])},
        ]
        
        for pattern in detail_patterns:
            elements = soup.find_all('div', **pattern)
            for elem in elements:
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 10:  # Skip very short snippets
                    important_text.append(f"SECTION: {text[:500]}")  # Limit each section to 500 chars
        
        # 4. Structured data (JSON-LD, microdata) - VERY IMPORTANT
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string:
                important_text.append(f"STRUCTURED DATA: {script.string}")
        
        # 5. Lists (ul, ol) - often contain features, inclusions, schedules
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            if items and len(items) > 1:  # Only capture lists with multiple items
                list_text = ' | '.join([item.get_text(strip=True) for item in items[:10]])  # Max 10 items
                if len(list_text) > 20:
                    important_text.append(f"LIST: {list_text}")
        
        # 6. Description/content paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            if len(text) > 50:  # Skip short paragraphs
                important_text.append(f"PARAGRAPH: {text[:300]}")  # Limit to 300 chars
        
        # 7. Tables - often contain pricing, schedules, features
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if rows:
                table_text = ' | '.join([row.get_text(separator=' ', strip=True) for row in rows[:10]])
                if len(table_text) > 20:
                    important_text.append(f"TABLE: {table_text}")
        
        # 8. All remaining text as fallback (if nothing structured found)
        if len(important_text) < 10:
            # If no structured sections found, get all text
            all_text = soup.get_text(separator=' ', strip=True)
            important_text.append(f"FULL TEXT: {all_text}")
        
        # Combine all extracted text
        combined = '\n\n'.join(important_text)
        
        # Remove excessive whitespace
        combined = ' '.join(combined.split())
        
        # Truncate if still too long (max ~150K chars for better coverage of pricing/details)
        # This allows capturing more content while staying within LLM context limits
        if len(combined) > 150000:
            combined = combined[:150000] + "...[truncated]"
        
        return combined
    
    def _fill_missing_fields_with_inference(self, data: Dict, cleaned_content: str, raw_html: str) -> Dict:
        """
        Second pass: Fill missing fields by inferring from full content.
        
        This method analyzes which fields are null after initial extraction,
        then makes a targeted API call to infer/derive those fields from the
        complete content context.
        
        Args:
            data: Initial extraction results
            cleaned_content: Cleaned HTML content
            raw_html: Original HTML
            
        Returns:
            Updated data dictionary with inferred fields
        """
        
        # Define fields that can be inferred for each content type
        inferable_fields_by_type = {
            'tour': [
                'duration_hours', 'difficulty_level', 'included_items', 'excluded_items',
                'max_participants', 'languages_available', 'pickup_included', 
                'minimum_age', 'cancellation_policy', 'schedules', 'what_to_bring',
                'check_in_time', 'restrictions'
            ],
            'restaurant': [
                'opening_hours', 'cuisine_type', 'price_range', 'dress_code',
                'reservation_required', 'parking_available'
            ],
            'real_estate': [
                'year_built', 'lot_size_m2', 'hoa_fee_monthly', 'property_tax_annual'
            ]
        }
        
        inferable_fields = inferable_fields_by_type.get(self.content_type, [])
        
        # Find which fields are null
        missing_fields = []
        for field in inferable_fields:
            # Check both property_name and content-specific name (e.g., tour_name)
            if data.get(field) in [None, '', []]:
                missing_fields.append(field)
        
        # If no missing fields or no inferable fields, skip second pass
        if not missing_fields:
            logger.info("✅ All fields filled, skipping inference pass")
            return data
        
        logger.info(f"🔍 Second pass: Inferring {len(missing_fields)} missing fields: {missing_fields}")
        
        # Build inference prompt
        inference_prompt = f"""You are analyzing a {self.content_type} page to fill in missing information.

**Already Extracted:**
{json.dumps({k: v for k, v in data.items() if not k.endswith('_evidence') and k not in ['raw_html', 'field_confidence', 'extracted_at', 'tokens_used']}, indent=2, default=str)}

**Missing Fields to Infer:**
{', '.join(missing_fields)}

**Full Content:**
{cleaned_content}

**Instructions:**
1. Analyze the full content carefully
2. For each missing field, try to INFER or DERIVE the information from context
3. Look for implicit information, schedules, lists, restrictions, tips
4. If a field truly cannot be inferred, return null
5. Return ONLY valid JSON with the missing fields

**Output Format:**
```json
{{
  "duration_hours": <inferred value or null>,
  "schedules": <inferred value or null>,
  "minimum_age": <inferred value or null>,
  "what_to_bring": <inferred list or null>,
  "check_in_time": <inferred value or null>,
  "restrictions": <inferred list or null>,
  ... (only fields that were missing)
}}
```

**Examples of Inference:**
- If content says "Child rates apply from ages 5 to 12" → minimum_age: 5
- If content says "8:00am | 9:00am | 10:30am" → schedules: ["08:00", "09:00", "10:30"]
- If content says "Wear comfortable clothes, sunscreen" → what_to_bring: ["comfortable clothes", "sunscreen", ...]
- If content says "Check-in 15 minutes prior" → check_in_time: "15 minutes before tour"

Now infer the missing fields:"""

        try:
            logger.info("🤖 Calling OpenAI for inference...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at inferring information from context. Output only valid JSON."},
                    {"role": "user", "content": inference_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual inference
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            inferred_json = response.choices[0].message.content
            inferred_data = json.loads(inferred_json)
            
            logger.info(f"✅ Inferred {len(inferred_data)} fields")
            logger.info(f"Inferred data: {json.dumps(inferred_data, indent=2, default=str)[:500]}")
            
            # Update tokens used
            data['tokens_used'] = data.get('tokens_used', 0) + response.usage.total_tokens
            
            # Merge inferred data into main data
            filled_count = 0
            for field, value in inferred_data.items():
                if value not in [None, '', []]:
                    data[field] = value
                    filled_count += 1
                    logger.info(f"  ✅ Filled {field}: {value}")
            
            logger.info(f"🎯 Second pass filled {filled_count}/{len(missing_fields)} fields")
            
            return data
            
        except Exception as e:
            logger.warning(f"⚠️ Inference pass failed: {e}, continuing with original data")
            return data
    
    def _validate_extraction(self, data: Dict) -> Dict:
        """Validate and clean extracted data based on page type."""
        validated = {}
        
        # For GENERAL pages, preserve guide fields without strict validation
        if self.page_type == 'general':
            # Copy all guide-specific fields directly
            guide_fields = [
                'page_type', 'destination', 'overview', 
                'property_types_available', 'tour_types_available',
                'price_range', 'popular_areas', 'market_trends',
                'featured_properties', 'featured_tours', 'featured_items_count',
                'total_properties_mentioned', 'total_tours_mentioned',
                'investment_tips', 'booking_tips', 'legal_considerations',
                'best_season', 'best_time_of_day', 'duration_range',
                'tips', 'things_to_bring', 'cuisine_types',
                # NEW: Extended tour guide fields
                'regions', 'seasonal_activities', 'faqs', 'what_to_pack',
                'family_friendly', 'accessibility_info'
            ]
            
            for field in guide_fields:
                if field in data:
                    validated[field] = data[field]
        
        # ============================================================================
        # FIELD PRESERVATION: Keep content-type specific field names
        # ============================================================================
        # Instead of mapping tour_name → property_name, we keep both:
        # - tour_name, restaurant_name, etc. (original specific fields)
        # - property_name (copy for DB compatibility)
        #
        # This allows frontend to display context-appropriate labels while
        # maintaining backward compatibility with Property model.
        
        field_mapping = {
            'tour': {
                'tour_name': 'property_name',
                'tour_type': 'property_type',
            },
            'restaurant': {
                'restaurant_name': 'property_name',
                'cuisine_type': 'property_type',
            },
            'real_estate': {
                # Real estate uses property_name/property_type directly (no mapping needed)
            },
            'local_tips': {
                'tip_title': 'property_name',
                'tip_category': 'property_type',
            },
            'transportation': {
                'service_name': 'property_name',
                'transport_type': 'property_type',
            }
        }
        
        # Apply content-type specific mapping (CREATE copies, don't replace)
        content_mapping = field_mapping.get(self.content_type, {})
        for source_field, target_field in content_mapping.items():
            if source_field in data and data[source_field] not in [None, '']:
                # Copy source to target (keep both fields)
                data[target_field] = data[source_field]
                logger.info(f"🔄 Copied {source_field} → {target_field}: {data[source_field]}")
        
        # For SPECIFIC pages OR common fields, validate property fields
        # Handle price
        if data.get('price_usd'):
            try:
                validated['price_usd'] = Decimal(str(data['price_usd']))
            except (ValueError, TypeError):
                validated['price_usd'] = None
        
        # Handle price_details (JSONField)
        if data.get('price_details'):
            try:
                validated['price_details'] = data['price_details']
                logger.info(f"💰 Saving price_details: {data['price_details']}")
            except Exception as e:
                logger.warning(f"Failed to save price_details: {e}")
                validated['price_details'] = {}
        
        # Handle integers
        for field in ['bedrooms', 'year_built', 'parking_spaces']:
            if data.get(field):
                try:
                    validated[field] = int(data[field])
                except (ValueError, TypeError):
                    validated[field] = None
        
        # Handle decimals
        for field in ['bathrooms', 'square_meters', 'lot_size_m2', 
                     'hoa_fee_monthly', 'property_tax_annual', 'latitude', 'longitude']:
            if data.get(field):
                try:
                    validated[field] = Decimal(str(data[field]))
                except (ValueError, TypeError):
                    validated[field] = None
        
        # Handle strings - BOTH generic and content-specific fields
        generic_fields = ['property_name', 'property_type', 'location', 'description',
                         'listing_id', 'internal_property_id', 'listing_status']
        
        # Content-specific fields by type
        content_specific_fields = {
            'tour': ['tour_name', 'tour_type', 'duration_hours', 'difficulty_level',
                    'included_items', 'excluded_items', 'max_participants', 
                    'languages_available', 'pickup_included', 'minimum_age',
                    'cancellation_policy', 'schedules', 'what_to_bring',
                    'check_in_time', 'restrictions'],
            'restaurant': ['restaurant_name', 'cuisine_type', 'opening_hours',
                          'price_range', 'dress_code', 'reservation_required'],
            'real_estate': ['property_name', 'property_type'],
        }
        
        # Add content-specific fields for this content type
        all_fields = generic_fields + content_specific_fields.get(self.content_type, [])
        
        for field in all_fields:
            if field in data:
                validated[field] = data.get(field)
        
        # Handle date_listed
        if data.get('date_listed'):
            validated['date_listed'] = data.get('date_listed')  # Keep as string for now, Django will parse
        else:
            validated['date_listed'] = None
        
        # Handle amenities array
        amenities = data.get('amenities')
        if amenities and isinstance(amenities, list):
            validated['amenities'] = [str(a) for a in amenities]
        else:
            validated['amenities'] = []
        
        # Handle confidence
        try:
            confidence = float(data.get('extraction_confidence', 0.5))
            validated['extraction_confidence'] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            validated['extraction_confidence'] = 0.5
        
        # Store field-level evidence
        evidence_fields = {}
        for key, value in data.items():
            if key.endswith('_evidence'):
                field_name = key.replace('_evidence', '')
                evidence_fields[field_name] = value
        
        validated['field_confidence'] = evidence_fields
        validated['extracted_at'] = timezone.now()
        
        return validated
    
    def extract_from_html(self, html: str, url: Optional[str] = None) -> Dict:
        """
        Extract data from HTML content based on content type.
        
        Args:
            html: HTML content to extract from
            url: Optional source URL
            
        Returns:
            Dictionary with extracted data (fields depend on content_type)
            
        Raises:
            ExtractionError: If extraction fails
        """
        
        # Clean content
        content = self._clean_content(html)
        
        # Get the appropriate prompt for this content type and page type
        extraction_prompt_template = get_extraction_prompt(self.content_type, self.page_type)
        # Use replace instead of format to avoid issues with braces in HTML content
        prompt = extraction_prompt_template.replace('{content}', content)
        
        logger.info(f"Prompt preview (first 800 chars): {prompt[:800]}")
        logger.info(f"Prompt preview (last 800 chars): {prompt[-800:]}")
        
        try:
            logger.info("Starting LLM property extraction...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Extract JSON from response
            raw_json = response.choices[0].message.content
            
            logger.info(f"LLM extraction completed. Tokens used: {response.usage.total_tokens}")
            logger.info(f"Raw LLM response: {raw_json[:500]}")  # Log first 500 chars
            
            # Parse JSON
            try:
                extracted_data = json.loads(raw_json)
                logger.info(f"Parsed JSON keys: {list(extracted_data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Raw response was: {raw_json}")
                raise ExtractionError("LLM returned invalid JSON")
            
            # Validate and clean
            validated_data = self._validate_extraction(extracted_data)
            
            # ========================================================================
            # SECOND PASS: Fill missing fields with inference from full content
            # ========================================================================
            # If key fields are still null, make a second API call with full context
            # to infer/derive missing information
            validated_data = self._fill_missing_fields_with_inference(
                validated_data, 
                content, 
                html
            )
            
            # Add metadata
            validated_data['source_url'] = url
            validated_data['raw_html'] = html[:10000]  # Store first 10K chars
            validated_data['tokens_used'] = response.usage.total_tokens
            validated_data['content_type'] = self.content_type
            validated_data['page_type'] = self.page_type
            
            logger.info(f"Extraction successful. Confidence: {validated_data['extraction_confidence']}")
            
            return validated_data
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ExtractionError(f"LLM API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected extraction error: {e}")
            raise ExtractionError(f"Extraction failed: {str(e)}")
    
    def extract_from_text(self, text: str) -> Dict:
        """
        Extract property data from plain text.
        
        Args:
            text: Text content to extract from
            
        Returns:
            Dictionary with extracted property data
        """
        return self.extract_from_html(text, url=None)
    
    def extract_with_retry(self, content: str, max_retries: int = 2) -> Dict:
        """
        Extract with retry logic on failure.
        
        Args:
            content: Content to extract from
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with extracted property data
            
        Raises:
            ExtractionError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.extract_from_html(content)
            except ExtractionError as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(f"Extraction attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {max_retries + 1} extraction attempts failed")
        
        raise last_error


def extract_property_data(content: str, url: Optional[str] = None) -> Dict:
    """
    Convenience function to extract property data.
    
    Usage:
        data = extract_property_data(html_content, url='https://...')
        property_name = data['property_name']
        price = data['price_usd']
    """
    extractor = PropertyExtractor(content_type='real_estate')
    return extractor.extract_from_html(content, url=url)


def extract_content_data(content: str, content_type: str, page_type: str = 'specific', url: Optional[str] = None) -> Dict:
    """
    Generic function to extract data for any content type.
    
    Args:
        content: HTML or text content to extract from
        content_type: Type of content (real_estate, tour, restaurant, local_tips, transportation)
        page_type: Type of page ('specific' for single item details, 'general' for guides/listings)
        url: Optional source URL
        
    Returns:
        Dictionary with extracted data (fields depend on content_type and page_type)
        
    Usage:
        # Extract specific tour data
        data = extract_content_data(html, 'tour', 'specific', url='https://viator.com/tours/d742-12345')
        
        # Extract general tour guide
        data = extract_content_data(html, 'tour', 'general', url='https://costarica.org/tours/')
        
        # Extract restaurant data  
        data = extract_content_data(html, 'restaurant', 'specific', url='https://yelp.com/biz/...')
    """
    extractor = PropertyExtractor(content_type=content_type, page_type=page_type)
    return extractor.extract_from_html(content, url=url)
