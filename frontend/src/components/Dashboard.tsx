import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <h1 className="dashboard-title">🏠 KP Real Estate Platform</h1>
        <p className="dashboard-subtitle">Sistema integral de gestión inmobiliaria con IA</p>
        
        <div className="dashboard-cards">
          <div className="dashboard-card" onClick={() => navigate('/data-collector')}>
            <div className="card-icon">📊</div>
            <h2>Data Collector</h2>
            <p>Recolección y gestión de propiedades</p>
            <button className="card-button">Acceder →</button>
          </div>
          
          <div className="dashboard-card" onClick={() => navigate('/properties')}>
            <div className="card-icon">🏘️</div>
            <h2>Properties</h2>
            <p>View indexed properties</p>
            <button className="card-button">Acceder →</button>
          </div>
          
          <div className="dashboard-card" onClick={() => navigate('/chatbot')}>
            <div className="card-icon">💬</div>
            <h2>Chatbot IA</h2>
            <p>Asistente virtual inmobiliario</p>
            <button className="card-button">Acceder →</button>
          </div>
        </div>
        
        <div className="dashboard-footer">
          <p>Backend API: <span className="status-indicator">✓</span> Connected</p>
        </div>
      </div>
    </div>
  );
}
