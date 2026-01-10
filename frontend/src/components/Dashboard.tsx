import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <h1 className="dashboard-title">🏠 KP Real Estate Platform</h1>
        <p className="dashboard-subtitle">Comprehensive AI-powered real estate management system</p>
        
        <div className="dashboard-cards">
          <div className="dashboard-card" onClick={() => navigate('/data-collector')}>
            <div className="card-icon">📊</div>
            <h2>Data Collector</h2>
            <p>Property collection and management</p>
            <button className="card-button">Access →</button>
          </div>
          
          <div className="dashboard-card" onClick={() => navigate('/properties')}>
            <div className="card-icon">🏘️</div>
            <h2>Properties</h2>
            <p>View indexed properties</p>
            <button className="card-button">Access →</button>
          </div>
          
          <div className="dashboard-card" onClick={() => navigate('/chatbot')}>
            <div className="card-icon">💬</div>
            <h2>AI Chatbot</h2>
            <p>Virtual real estate assistant</p>
            <button className="card-button">Access →</button>
          </div>
        </div>
        
        <div className="dashboard-footer">
          <p>Backend API: <span className="status-indicator">✓</span> Connected</p>
        </div>
      </div>
    </div>
  );
}
