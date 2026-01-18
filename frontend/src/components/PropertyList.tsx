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
  classification?: string;
  category?: string;
}

const API_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/properties/`
  : 'http://localhost:8000/properties/';

// SVG Icons
const Icons = {
  x: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  chart: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  alert: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  mapPin: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  ),
  home: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  bed: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2 4v16" />
      <path d="M2 8h18a2 2 0 0 1 2 2v10" />
      <path d="M2 17h20" />
      <path d="M6 8V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v4" />
    </svg>
  ),
  droplet: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  ),
  ruler: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 2.4 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0z" />
      <path d="M14.5 12.5l-8-8" />
      <path d="M5.5 5.5l.7.7" />
      <path d="M9.5 9.5l.7.7" />
      <path d="M13.5 13.5l.7.7" />
      <path d="M17.5 17.5l.7.7" />
    </svg>
  ),
  chat: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  lightbulb: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8a6 6 0 0 0-12 0c0 1.33.47 2.48 1.41 3.5.76.76 1.23 1.52 1.41 2.5" />
    </svg>
  ),
}; export default function PropertyList() {
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
        <div className="loading-spinner">Cargando propiedades...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="property-list-container">
        <div className="error-message">{Icons.x && <Icons.x />} {error}</div>
      </div>
    );
  }

  const embeddedProperties = properties.filter(p => p.has_embedding);
  const totalProperties = properties.length;

  return (
    <div className="property-list-container">
      <div className="property-list-header">
        <h1><Icons.chart /> Propiedades Indexadas</h1>
        <p className="subtitle">
          Propiedades disponibles para consultas del chatbot
        </p>
        <div className="stats">
          <div className="stat-card">
            <div className="stat-number">{totalProperties}</div>
            <div className="stat-label">Total de Propiedades</div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-number">{embeddedProperties.length}</div>
            <div className="stat-label">Con Embeddings</div>
          </div>
        </div>
      </div>

      <div className="property-grid">
        {properties.map((property) => (
          <div key={property.id} className={`property-card ${!property.has_embedding ? 'no-embedding' : ''}`}>
            <div className="property-header">
              <h3 className="property-name">{property.property_name}</h3>
              {property.has_embedding ? (
                <span className="badge badge-success"><Icons.check /> Indexada</span>
              ) : (
                <span className="badge badge-warning"><Icons.alert /> No indexada</span>
              )}
              {property.classification && (
                <span className={`badge ${property.classification === 'specific' ? 'badge-info' : 'badge-secondary'}`}>
                  {property.classification === 'specific' ? '📍 Específico' : '📋 General'}
                </span>
              )}
            </div>

            <div className="property-price">
              {property.price_usd ? `$${property.price_usd.toLocaleString()} USD` : 'Precio no disponible'}
            </div>

            <div className="property-details">
              {property.location && (
                <div className="detail-item">
                  <span className="detail-icon"><Icons.mapPin /></span>
                  <span className="detail-text">{property.location}</span>
                </div>
              )}
              {property.property_type && (
                <div className="detail-item">
                  <span className="detail-icon"><Icons.home /></span>
                  <span className="detail-text">{property.property_type}</span>
                </div>
              )}
              {property.bedrooms && (
                <div className="detail-item">
                  <span className="detail-icon"><Icons.bed /></span>
                  <span className="detail-text">{property.bedrooms} habitaciones</span>
                </div>
              )}
              {property.bathrooms && (
                <div className="detail-item">
                  <span className="detail-icon"><Icons.droplet /></span>
                  <span className="detail-text">{property.bathrooms} baños</span>
                </div>
              )}
              {property.square_meters && (
                <div className="detail-item">
                  <span className="detail-icon"><Icons.ruler /></span>
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
                <div className="queries-title"><Icons.chat /> Consultas sugeridas:</div>
                <div className="query-chip">¿Cuánto cuesta {property.property_name}?</div>
                <div className="query-chip">Cuéntame más sobre {property.location ? `la propiedad en ${property.location}` : 'esta propiedad'}</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {embeddedProperties.length > 0 && (
        <div className="tips-section">
          <h3><Icons.lightbulb /> Consejos para el Chatbot</h3>
          <ul>
            <li>Pregunta por ubicaciones específicas: "¿Propiedades en {properties[0]?.location}?"</li>
            <li>Usa filtros: "Casas con {properties[0]?.bedrooms || 3} habitaciones bajo ${Math.round((properties[0]?.price_usd || 300000) / 1000)}K"</li>
            <li>Compara propiedades: "¿Cuál es la diferencia entre {properties[0]?.property_name} y {properties[1]?.property_name}?"</li>
            <li>Pregunta sobre amenidades: "¿Propiedades con piscina?"</li>
          </ul>
        </div>
      )}
    </div>
  );
}
