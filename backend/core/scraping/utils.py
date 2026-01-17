from decimal import Decimal, InvalidOperation
import logging
from typing import Optional, Union, Dict, Any
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class MoneyUtils:
    """Utilities for money handling and currency conversion."""
    
    # Default rates, in a real app these might come from a DB or API
    # 1 USD = X Currency
    DEFAULT_RATES = {
        'CRC': Decimal('520.0'),
        'EUR': Decimal('0.92'),
    }

    @classmethod
    def convert_to_usd(cls, amount: Decimal, currency: str, rate: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Convert an amount from a given currency to USD.
        
        Args:
            amount: The amount to convert.
            currency: The source currency code (e.g. 'CRC').
            rate: Optional explicit rate to use. If None, uses default/configured rates.
            
        Returns:
            Decimal amount in USD or None if conversion failed.
        """
        if amount is None:
            return None
            
        currency = currency.upper().strip()
        
        if currency == 'USD':
            return amount
            
        exchange_rate = rate or cls.DEFAULT_RATES.get(currency)
        
        if not exchange_rate:
            logger.warning(f"No exchange rate found for {currency} to USD")
            return None
            
        try:
            # simple division: Amount / Rate = USD
            # e.g. 520000 CRC / 520 = 1000 USD
            usd_amount = amount / exchange_rate
            return usd_amount.quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error converting currency: {e}")
            return None

class NumberUtils:
    """Utilities for robust number parsing."""
    
    @staticmethod
    def extract_float(text: Union[str, float, int, None]) -> Optional[float]:
        """Extract the first float value found in text."""
        if text is None:
            return None
        if isinstance(text, (float, int)):
            return float(text)
            
        # Clean text
        text = str(text).replace(',', '').strip()
        
        # Search for pattern
        match = re.search(r'[-+]?\d*\.\d+|\d+', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    @staticmethod
    def extract_int(text: Union[str, float, int, None]) -> Optional[int]:
        """Extract the first integer value found in text."""
        val = NumberUtils.extract_float(text)
        return int(val) if val is not None else None
        
    @staticmethod
    def parse_area(text: Optional[str]) -> Optional[Decimal]:
        """Parse area string handling units (sqft -> m2) as explicit fallback logic."""
        if not text:
            return None
            
        text = text.lower()
        val = NumberUtils.extract_float(text)
        
        if val is None:
            return None
            
        # Simple heuristic conversion if unit is explicitly sqft/ft2
        if 'sq' in text and 'ft' in text:
             # 1 sqft = 0.092903 m2
             val = val * 0.092903
             
        return Decimal(str(val)).quantize(Decimal('0.01'))

class JSONUtils:
    """Utilities for parsing AI JSON responses."""
    
    @staticmethod
    def parse_ai_response(content: str) -> Dict[str, Any]:
        """
        Robustly parse JSON from AI response.
        Handles:
        - Markdown code blocks (```json ... ```)
        - Leading/trailing whitespace
        - Common syntax errors (trailing commas, missing braces, comments)
        """
        if not content:
            return {}
            
        # Strip markdown code blocks
        content = re.sub(r'^```(?:json)?\s*', '', content.strip(), flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
        
        # Remove comments (//...)
        content = re.sub(r'//.*', '', content)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON directly: {e}. Attempting repair.")
            
            # Common Fix 1: Remove trailing commas
            content_fixed = re.sub(r',\s*([\]}])', r'\1', content)
            
            # Common Fix 2: Ensure braces match (simplistic)
            if content_fixed.count('{') > content_fixed.count('}'):
                content_fixed += '}' * (content_fixed.count('{') - content_fixed.count('}'))
            if content_fixed.count('[') > content_fixed.count(']'):
                content_fixed += ']' * (content_fixed.count('[') - content_fixed.count(']'))
                
            try:
                return json.loads(content_fixed)
            except json.JSONDecodeError:
                logger.error("JSON repair failed.")
                return {}

class DateUtils:
    """Utilities for standardizing dates."""
    
    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[str]:
        """Parse varied date strings into ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None
            
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',  # January 1, 2024
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        return None

def clean_text(text: Optional[str]) -> Optional[str]:
    """Basic clean text utility."""
    if not text:
        return None
    return " ".join(text.split())
