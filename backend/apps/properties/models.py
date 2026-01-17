"""
Property model for real estate listings.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField

from apps.tenants.models import Tenant


class PropertyType:
    """Property type constants."""
    HOUSE = 'house'
    CONDO = 'condo'
    VILLA = 'villa'
    LAND = 'land'
    COMMERCIAL = 'commercial'
    APARTMENT = 'apartment'
    
    CHOICES = [
        (HOUSE, _('House')),
        (CONDO, _('Condominium')),
        (VILLA, _('Villa')),
        (LAND, _('Land')),
        (COMMERCIAL, _('Commercial')),
        (APARTMENT, _('Apartment')),
    ]


class PropertyStatus:
    """Property status constants."""
    AVAILABLE = 'available'
    PENDING = 'pending'
    SOLD = 'sold'
    OFF_MARKET = 'off_market'
    
    CHOICES = [
        (AVAILABLE, _('Available')),
        (PENDING, _('Pending')),
        (SOLD, _('Sold')),
        (OFF_MARKET, _('Off Market')),
    ]


class SourceWebsite:
    """Source website constants."""
    ENCUENTRA24 = 'encuentra24'
    CR_REALESTATE = 'crrealestate'
    COLDWELL_BANKER = 'coldwellbanker'
    OTHER = 'other'
    
    CHOICES = [
        (ENCUENTRA24, _('Encuentra24')),
        (CR_REALESTATE, _('CR Real Estate')),
        (COLDWELL_BANKER, _('Coldwell Banker')),
        (OTHER, _('Other')),
    ]


class Property(models.Model):
    """
    Real estate property model with vector embeddings for semantic search.
    """
    
    # Primary identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='properties',
        verbose_name=_('Tenant')
    )
    
    # Basic property information
    property_name = models.CharField(
        _('Property Name'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Name or title of the property')
    )
    
    price_usd = models.DecimalField(
        _('Price (USD)'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Price in US dollars (lowest price if multiple categories)')
    )
    
    price_details = models.JSONField(
        _('Price Details'),
        default=dict,
        blank=True,
        help_text=_('Detailed pricing information: adults, children, students, etc. for tours; ranges for restaurants/hotels')
    )
    
    bedrooms = models.IntegerField(
        _('Bedrooms'),
        null=True,
        blank=True,
        help_text=_('Number of bedrooms')
    )
    
    bathrooms = models.DecimalField(
        _('Bathrooms'),
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_('Number of bathrooms (can be 2.5, etc.)')
    )
    
    property_type = models.CharField(
        _('Property Type'),
        max_length=20,
        choices=PropertyType.CHOICES,
        null=True,
        blank=True,
        help_text=_('Type of property')
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PropertyStatus.CHOICES,
        default=PropertyStatus.AVAILABLE,
        help_text=_('Current status of the property')
    )
    
    # Location
    location = models.CharField(
        _('Location'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('City, region, or area')
    )
    
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('GPS latitude coordinate')
    )
    
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('GPS longitude coordinate')
    )
    
    # Detailed information
    description = models.TextField(
        _('Description'),
        null=True,
        blank=True,
        help_text=_('Full property description')
    )
    
    square_meters = models.DecimalField(
        _('Square Meters'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Property size in square meters')
    )
    
    lot_size_m2 = models.DecimalField(
        _('Lot Size (m²)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Lot size in square meters')
    )
    
    hoa_fee_monthly = models.DecimalField(
        _('HOA Fee (Monthly)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly HOA/maintenance fee in USD')
    )
    
    property_tax_annual = models.DecimalField(
        _('Property Tax (Annual)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Annual property tax in USD')
    )
    
    amenities = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name=_('Amenities'),
        help_text=_('List of amenities (pool, gym, etc.)')
    )
    
    year_built = models.IntegerField(
        _('Year Built'),
        null=True,
        blank=True,
        help_text=_('Year property was constructed')
    )
    
    parking_spaces = models.IntegerField(
        _('Parking Spaces'),
        null=True,
        blank=True,
        help_text=_('Number of parking spaces')
    )
    
    # User role visibility
    user_roles = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        verbose_name=_('Visible to Roles'),
        help_text=_('Which user roles can see this property')
    )
    
    # Metadata and tracking
    source_website = models.CharField(
        _('Source Website'),
        max_length=50,
        choices=SourceWebsite.CHOICES,
        default=SourceWebsite.OTHER,
        help_text=_('Website where property was found')
    )
    
    source_url = models.URLField(
        _('Source URL'),
        max_length=500,
        null=True,
        blank=True,
        help_text=_('Original listing URL')
    )
    
    # Listing identification
    listing_id = models.CharField(
        _('Listing ID'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Public listing ID from source website')
    )
    
    internal_property_id = models.CharField(
        _('Internal Property ID'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Internal property ID from source website')
    )
    
    listing_status = models.CharField(
        _('Listing Status'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Status from source website (Active, Published, Sold, Pending)')
    )
    
    date_listed = models.DateField(
        _('Date Listed'),
        null=True,
        blank=True,
        help_text=_('Date property was listed on source website')
    )
    
    raw_html = models.TextField(
        _('Raw HTML'),
        null=True,
        blank=True,
        help_text=_('Original HTML content for backup')
    )
    
    extraction_confidence = models.DecimalField(
        _('Extraction Confidence'),
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Confidence score from LLM extraction (0-1)')
    )
    
    field_confidence = models.JSONField(
        _('Field Confidence'),
        default=dict,
        blank=True,
        help_text=_('Confidence score per field')
    )
    
    extracted_at = models.DateTimeField(
        _('Extracted At'),
        null=True,
        blank=True,
        help_text=_('When data was extracted')
    )
    
    last_verified = models.DateTimeField(
        _('Last Verified'),
        null=True,
        blank=True,
        help_text=_('When data was last manually verified')
    )
    
    verified_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_properties',
        verbose_name=_('Verified By')
    )
    
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Is this property listing active?')
    )
    
    # For RAG - Vector search
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text=_('Vector embedding for semantic search')
    )
    
    content_for_search = models.TextField(
        _('Search Content'),
        blank=True,
        help_text=_('Optimized text for semantic search')
    )
    
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        help_text=_('Full-text search vector')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('Updated At'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'properties'
        verbose_name = _('Property')
        verbose_name_plural = _('Properties')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status', 'is_active']),
            models.Index(fields=['property_type', 'location']),
            models.Index(fields=['price_usd']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'source_url'],
                name='unique_property_per_tenant',
                condition=models.Q(source_url__isnull=False),
                violation_error_message='This property URL already exists for this tenant'
            )
        ]
    
    def __str__(self):
        return f"{self.property_name} - ${self.price_usd:,.0f}"
    
    def get_price_per_sqm(self):
        """Calculate price per square meter."""
        if self.price_usd and self.square_meters and self.square_meters > 0:
            return self.price_usd / self.square_meters
        return None
    
    def has_coordinates(self):
        """Check if property has GPS coordinates."""
        return self.latitude is not None and self.longitude is not None
    
    def generate_search_content(self):
        """Generate optimized content for semantic search."""
        parts = []
        
        if self.property_name:
            parts.append(f"Property: {self.property_name}")
        
        if self.property_type:
            parts.append(f"Type: {self.get_property_type_display()}")
        
        if self.location:
            parts.append(f"Location: {self.location}")
        
        if self.price_usd:
            parts.append(f"Price: ${self.price_usd:,.0f} USD")
        
        if self.bedrooms:
            parts.append(f"{self.bedrooms} bedrooms")
        
        if self.bathrooms:
            parts.append(f"{self.bathrooms} bathrooms")
        
        if self.square_meters:
            parts.append(f"{self.square_meters} m²")
        
        if self.amenities:
            parts.append(f"Amenities: {', '.join(self.amenities)}")
        
        if self.description:
            parts.append(f"Description: {self.description}")
        
        return "\n".join(parts) if parts else "Property listing"
    
    def save(self, *args, **kwargs):
        """Override save to generate search content."""
        if not self.content_for_search:
            self.content_for_search = self.generate_search_content()
        
        super().save(*args, **kwargs)


class PropertyImage(models.Model):
    """Property images."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image_url = models.TextField(
        help_text=_('Image URL - no length limit to support URLs with many parameters')
    )
    
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Image caption')
    )
    
    order = models.IntegerField(
        default=0,
        help_text=_('Display order')
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text=_('Is this the primary image?')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_images'
        ordering = ['order', '-is_primary', 'created_at']
        indexes = [
            models.Index(fields=['property', 'order']),
        ]
    
    def __str__(self):
        return f"Image for {self.property.property_name}"


class ContentGuide(models.Model):
    """
    General guide/overview pages (listings, category pages, destination guides).
    Stores aggregate information about multiple items rather than single specific items.
    
    Examples:
    - Tour guide for a destination (costarica.org/tours/)
    - Restaurant directory for a city
    - Property listings for a neighborhood
    """
    
    # Identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='content_guides',
        help_text=_('Organization that owns this guide')
    )
    
    # Content Type
    content_type = models.CharField(
        max_length=50,
        default='tour',
        help_text=_('Type of content: tour, restaurant, real_estate, local_tips, transportation')
    )
    
    page_type = models.CharField(
        max_length=20,
        default='general',
        help_text=_('Should always be "general" for this model')
    )
    
    # Location/Destination Info
    destination = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Destination or location name (e.g., "Costa Rica", "Manuel Antonio")')
    )
    
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('City/region/area')
    )
    
    # General Content
    title = models.CharField(
        max_length=500,
        help_text=_('Page title or guide name')
    )
    
    overview = models.TextField(
        blank=True,
        null=True,
        help_text=_('General description/overview of what this page offers')
    )
    
    # Type-specific structured data (JSON)
    # For tours: {"tour_types": ["volcano", "beach"], "price_range": "$50-$200"}
    # For restaurants: {"cuisine_types": ["italian", "seafood"], "price_level": "$$-$$$"}
    structured_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Structured data specific to content type')
    )
    
    # Featured/Popular Items
    featured_items = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of featured items with basic info: [{name, url, price, rating}]')
    )
    
    # Tips and Recommendations
    tips = models.JSONField(
        default=list,
        blank=True,
        help_text=_('General tips or advice (e.g., ["Book in advance", "Bring sunscreen"])')
    )
    
    # Best times/seasons
    best_season = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Best time to visit/book (e.g., "December - April")')
    )
    
    # Price information
    typical_price_range = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Typical price range (e.g., "$50-$200")')
    )
    
    # Source Information
    source_url = models.URLField(
        max_length=1000,
        help_text=_('Original source URL')
    )
    
    source_website = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Source website name')
    )
    
    # Metadata
    extraction_confidence = models.FloatField(
        default=0.5,
        help_text=_('Confidence score of extraction (0.0 - 1.0)')
    )
    
    extraction_method = models.CharField(
        max_length=50,
        default='llm_based',
        help_text=_('Method used for extraction')
    )
    
    # User roles who can access
    user_roles = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text=_('Roles that can access this guide')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this guide was created')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this guide was last updated')
    )
    
    # Search
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        db_table = 'content_guides'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'content_type']),
            models.Index(fields=['destination']),
            models.Index(fields=['source_website']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = _('Content Guide')
        verbose_name_plural = _('Content Guides')
    
    def __str__(self):
        return f"{self.title} ({self.content_type})"
    
    @property
    def featured_items_count(self):
        """Count of featured items."""
        return len(self.featured_items) if self.featured_items else 0
