from django.contrib import admin
from .models import Property, PropertyImage, ContentGuide


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image_url', 'caption', 'order', 'is_primary')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'tenant', 'property_type', 'price_usd', 
                    'location', 'source_website', 'status', 'is_active', 'created_at')
    list_filter = ('status', 'property_type', 'source_website', 'is_active', 'tenant', 'created_at')
    search_fields = ('property_name', 'location', 'description')
    readonly_fields = ('id', 'extraction_confidence', 'extracted_at', 
                      'last_verified', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'property_name', 'property_type', 'status')
        }),
        ('Pricing', {
            'fields': ('price_usd', 'hoa_fee_monthly', 'property_tax_annual')
        }),
        ('Details', {
            'fields': ('bedrooms', 'bathrooms', 'square_meters', 'lot_size_m2',
                      'year_built', 'parking_spaces')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Description & Amenities', {
            'fields': ('description', 'amenities')
        }),
        ('Access Control', {
            'fields': ('user_roles',)
        }),
        ('Source & Tracking', {
            'fields': ('source_website', 'source_url', 'extraction_confidence', 'field_confidence',
                      'extracted_at', 'last_verified', 'verified_by')
        }),
        ('Search & RAG', {
            'fields': ('content_for_search',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [PropertyImageInline]
    
    actions = ['mark_as_verified', 'mark_as_available', 'mark_as_sold']
    
    def mark_as_verified(self, request, queryset):
        from django.utils import timezone
        queryset.update(last_verified=timezone.now(), verified_by=request.user)
        self.message_user(request, f"{queryset.count()} properties marked as verified.")
    mark_as_verified.short_description = "Mark selected as verified"
    
    def mark_as_available(self, request, queryset):
        queryset.update(status='available')
        self.message_user(request, f"{queryset.count()} properties marked as available.")
    mark_as_available.short_description = "Mark as available"
    
    def mark_as_sold(self, request, queryset):
        queryset.update(status='sold')
        self.message_user(request, f"{queryset.count()} properties marked as sold.")
    mark_as_sold.short_description = "Mark as sold"


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'caption', 'order', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('property__property_name', 'caption')


@admin.register(ContentGuide)
class ContentGuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'destination', 'source_website', 
                    'featured_items_count', 'extraction_confidence', 'created_at')
    list_filter = ('content_type', 'page_type', 'source_website', 'tenant', 'created_at')
    search_fields = ('title', 'destination', 'location', 'overview')
    readonly_fields = ('id', 'extraction_confidence', 'extraction_method', 
                      'created_at', 'updated_at', 'featured_items_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'title', 'content_type', 'page_type')
        }),
        ('Location', {
            'fields': ('destination', 'location')
        }),
        ('Content', {
            'fields': ('overview', 'structured_data', 'tips')
        }),
        ('Pricing & Timing', {
            'fields': ('typical_price_range', 'best_season')
        }),
        ('Featured Items', {
            'fields': ('featured_items', 'featured_items_count'),
            'description': 'List of featured items found on this page'
        }),
        ('Access Control', {
            'fields': ('user_roles',)
        }),
        ('Source & Extraction', {
            'fields': ('source_url', 'source_website', 'extraction_confidence', 
                      'extraction_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['refresh_extraction']
    
    def refresh_extraction(self, request, queryset):
        # TODO: Implement re-extraction from source URL
        self.message_user(request, f"Re-extraction queued for {queryset.count()} guides.")
    refresh_extraction.short_description = "Re-extract from source URL"
