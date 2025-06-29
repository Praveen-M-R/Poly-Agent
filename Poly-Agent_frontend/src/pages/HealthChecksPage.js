import React, { useState, useEffect } from 'react';
import HealthChecks from '../components/HealthChecks';
import HealthCheckDashboard from '../components/HealthCheckDashboard';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';
import { Link, useNavigate } from 'react-router-dom';

const HealthChecksPage = () => {
  const navigate = useNavigate();
  const [view, setView] = useState('dashboard'); // 'dashboard' or 'list'
  const [user, setUser] = useState(null);

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) {
      setUser(JSON.parse(user));
    }
  }, []); 
  const handleLogout = async () => {
    try {
      await fetch('/api/users/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      
      // Clear user data from localStorage
      localStorage.removeItem('user');
      
      // Redirect to login page
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Health Monitoring</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link active">Health Checks</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
          </nav>
          {user && (
            <div className="user-info">
              <span>Welcome, {user.name || user.username}</span>
              <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </div>
          )}
        </div>
      </header>

      <main className="dashboard-content">
        <div className="health-checks-header">
          <h2>{view === 'dashboard' ? 'Health Check Dashboard' : 'Your Health Checks'}</h2>
          <div className="view-controls">
            <button 
              className={`view-button ${view === 'dashboard' ? 'active' : ''}`} 
              onClick={() => setView('dashboard')}
            >
              Dashboard View
            </button>
            <button 
              className={`view-button ${view === 'list' ? 'active' : ''}`} 
              onClick={() => setView('list')}
            >
              List View
            </button>
            <Link to="/health-checks/create" className="create-button">
              <i className="fas fa-plus"></i> Create Health Check
            </Link>
          </div>
        </div>
        
        {view === 'dashboard' ? <HealthCheckDashboard /> : <HealthChecks />}
      </main>
    </div>
  );
};

export default HealthChecksPage; 