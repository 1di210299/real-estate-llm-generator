from typing import List, Optional
from pydantic import BaseModel, Field

class PropertyData(BaseModel):
    """
    Schema for structured property data extraction.
    """
    property_name: Optional[str] = Field(None, description="Name or title of the property")
    property_name_evidence: Optional[str] = Field(None, description="Exact quote from source for property_name")
    
    price_usd: Optional[float] = Field(None, description="Price in USD. Remove commas. Convert from other currencies if rate is known.")
    price_evidence: Optional[str] = Field(None, description="Exact quote from source for price")
    
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bedrooms_evidence: Optional[str] = Field(None, description="Exact quote from source for bedrooms")
    
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms (can be decimal for half baths)")
    bathrooms_evidence: Optional[str] = Field(None, description="Exact quote from source for bathrooms")
    
    property_type: Optional[str] = Field(None, description="Type of property: house, condo, villa, land, commercial, apartment")
    property_type_evidence: Optional[str] = Field(None, description="Exact quote from source for property_type")
    
    location: Optional[str] = Field(None, description="Full address or city/province")
    location_evidence: Optional[str] = Field(None, description="Exact quote from source for location")
    
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    coordinates_evidence: Optional[str] = Field(None, description="Source of coordinates")
    
    listing_id: Optional[str] = Field(None, description="Public listing ID")
    listing_id_evidence: Optional[str] = Field(None, description="Exact quote from source for listing_id")
    
    internal_property_id: Optional[str] = Field(None, description="Internal system ID from forms/urls")
    internal_property_id_evidence: Optional[str] = Field(None, description="Exact quote from source for internal_property_id")
    
    listing_status: Optional[str] = Field(None, description="Active, Published, Sold, Pending")
    listing_status_evidence: Optional[str] = Field(None, description="Exact quote from source for listing_status")
    
    date_listed: Optional[str] = Field(None, description="Publication date in YYYY-MM-DD")
    date_listed_evidence: Optional[str] = Field(None, description="Exact quote from source for date_listed")
    
    description: Optional[str] = Field(None, description="Full description text")
    
    square_meters: Optional[float] = Field(None, description="Built area in square meters")
    square_meters_evidence: Optional[str] = Field(None, description="Exact quote from source for square_meters")
    
    lot_size_m2: Optional[float] = Field(None, description="Lot size in square meters")
    lot_size_evidence: Optional[str] = Field(None, description="Exact quote from source for lot_size_m2")
    
    hoa_fee_monthly: Optional[float] = Field(None, description="Monthly HOA fee")
    hoa_fee_evidence: Optional[str] = Field(None, description="Exact quote from source for hoa_fee_monthly")
    
    property_tax_annual: Optional[float] = Field(None, description="Annual property tax")
    property_tax_evidence: Optional[str] = Field(None, description="Exact quote from source for property_tax_annual")
    
    amenities: Optional[List[str]] = Field(None, description="List of amenities")
    amenities_evidence: Optional[str] = Field(None, description="Exact quote from source for amenities")
    
    year_built: Optional[int] = Field(None, description="Year built")
    year_built_evidence: Optional[str] = Field(None, description="Exact quote from source for year_built")
    
    parking_spaces: Optional[int] = Field(None, description="Number of parking spaces")
    parking_evidence: Optional[str] = Field(None, description="Exact quote from source for parking_spaces")
    
    classification: Optional[str] = Field(None, description="Classify as 'specific' (single property detail) or 'general' (list of properties or broad info)")
    classification_evidence: Optional[str] = Field(None, description="Reasoning for classification")

    category: str = Field("real_estate", description="Content category, defaulting to 'real_estate'")
    
    extraction_confidence: float = Field(..., description="0.0 to 1.0 confidence score")
    confidence_reasoning: str = Field(..., description="Explanation of confidence score")
