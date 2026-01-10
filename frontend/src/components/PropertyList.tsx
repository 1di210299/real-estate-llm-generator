import { useState, useEffect } from 'react';
import './PropertyList.css';

interface Property {
  id: string;
  property_name: string;
  price_usd: number;
  location: string;
  property_type: string;
  bedrooms?: number;
  bathrooms?: number;
  square_meters?: number;
  description: string;
  has_embedding: boolean;
}

const API_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/properties/`
  : 'http://localhost:8000/properties/';export default function PropertyList() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error('Error loading properties');
      }
      const data = await response.json();
      setProperties(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="property-list-container">
        <div className="loading-spinner">Loading properties...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="property-list-container">
        <div className="error-message">❌ {error}</div>
      </div>
    );
  }

  const embeddedProperties = properties.filter(p => p.has_embedding);
  const totalProperties = properties.length;

  return (
    <div className="property-list-container">
      <div className="property-list-header">
        <h1>📊 Indexed Properties</h1>
        <p className="subtitle">
          Properties available for chatbot queries
        </p>
        <div className="stats">
          <div className="stat-card">
            <div className="stat-number">{totalProperties}</div>
            <div className="stat-label">Total Properties</div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-number">{embeddedProperties.length}</div>
            <div className="stat-label">With Embeddings</div>
          </div>
        </div>
      </div>

      <div className="property-grid">
        {properties.map((property) => (
          <div key={property.id} className={`property-card ${!property.has_embedding ? 'no-embedding' : ''}`}>
            <div className="property-header">
              <h3 className="property-name">{property.property_name}</h3>
              {property.has_embedding ? (
                <span className="badge badge-success">✓ Indexed</span>
              ) : (
                <span className="badge badge-warning">⚠ Not indexed</span>
              )}
            </div>

            <div className="property-price">
              {property.price_usd ? `$${property.price_usd.toLocaleString()} USD` : 'Price not available'}
            </div>

            <div className="property-details">
              {property.location && (
                <div className="detail-item">
                  <span className="detail-icon">📍</span>
                  <span className="detail-text">{property.location}</span>
                </div>
              )}
              {property.property_type && (
                <div className="detail-item">
                  <span className="detail-icon">🏠</span>
                  <span className="detail-text">{property.property_type}</span>
                </div>
              )}
              {property.bedrooms && (
                <div className="detail-item">
                  <span className="detail-icon">🛏️</span>
                  <span className="detail-text">{property.bedrooms} habitaciones</span>
                </div>
              )}
              {property.bathrooms && (
                <div className="detail-item">
                  <span className="detail-icon">🚿</span>
                  <span className="detail-text">{property.bathrooms} baños</span>
                </div>
              )}
              {property.square_meters && (
                <div className="detail-item">
                  <span className="detail-icon">📐</span>
                  <span className="detail-text">{property.square_meters} m²</span>
                </div>
              )}
            </div>

            {property.description && (
              <div className="property-description">
                {property.description.substring(0, 150)}
                {property.description.length > 150 && '...'}
              </div>
            )}

            {property.has_embedding && (
              <div className="suggested-queries">
                <div className="queries-title">💬 Suggested queries:</div>
                <div className="query-chip">How much does {property.property_name} cost?</div>
                <div className="query-chip">Tell me more about {property.location ? `the property in ${property.location}` : 'this property'}</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {embeddedProperties.length > 0 && (
        <div className="tips-section">
          <h3>💡 Chatbot Tips</h3>
          <ul>
            <li>Ask for specific locations: "Properties in {properties[0]?.location}?"</li>
            <li>Use filters: "Houses with {properties[0]?.bedrooms || 3} bedrooms under ${Math.round((properties[0]?.price_usd || 300000) / 1000)}K"</li>
            <li>Compare properties: "What's the difference between {properties[0]?.property_name} and {properties[1]?.property_name}?"</li>
            <li>Ask about amenities: "Properties with pool?"</li>
          </ul>
        </div>
      )}
    </div>
  );
}
