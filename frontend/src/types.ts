export interface PropertyData {
  id?: string;
  property_name?: string;
  price_usd?: string;
  listing_id?: string;
  internal_property_id?: string;
  listing_status?: string;
  date_listed?: string;
  description?: string;
  property_type?: string;
  property_type_display?: string;
  bedrooms?: number;
  bathrooms?: number;
  square_meters?: string;
  lot_size_m2?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  source_url?: string;
  source_website?: string;
  status?: string;
  status_display?: string;
  created_at?: string;
  extraction_confidence?: number;
  classification?: string;
  category?: string;
}

export interface IngestResponse {
  property: PropertyData;
  extraction_confidence: number;
  status?: string;
  error?: string;
}
