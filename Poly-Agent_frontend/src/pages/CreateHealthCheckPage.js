import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import HealthCheckForm from '../components/HealthCheckForm';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const CreateHealthCheckPage = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
  const handleCreateHealthCheck = async (formData) => {
    try {
      console.log('Creating health check with data:', formData);
      
      // Get CSRF token from cookie
      const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
      const csrfToken = csrfCookie ? csrfCookie.split('=')[1] : '';
      
      if (!csrfToken) {
        console.error('CSRF token not found in cookies');
      }
      
      const response = await fetch('/health/api/checks/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('API error response:', errorData);
        
        if (typeof errorData === 'object' && Object.keys(errorData).length > 0) {
          // Format validation errors
          const errorMessages = Object.entries(errorData)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
          throw new Error(errorMessages || 'Validation error');
        } else {
          throw new Error(errorData.detail || 'Failed to create health check');
        }
      }
      
      const newCheck = await response.json();
      
      // Navigate to health checks list on success
      navigate('/health-checks');
      return newCheck;
    } catch (err) {
      console.error('Error creating health check:', err);
      setError(err.message || 'An error occurred while creating the health check');
      return Promise.reject(err);
    }
  };
  
  const handleLogout = async () => {
    try {
      await fetch('/api/users/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      
      // Clear local storage and state
      localStorage.removeItem('user');
      
      // Redirect to login page
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Failed to logout. Please try again.');
    }
  };
  
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Create Health Check</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
          </nav>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {error && <div className="dashboard-error">{error}</div>}

      <main className="dashboard-content">
        <div className="health-check-container">
          <div className="page-description">
            <p>
              Create a new health check to monitor the status and response times of your services.
              Health checks periodically ping your specified endpoints and alert you when they're down.
            </p>
          </div>
          
          <HealthCheckForm onSubmit={handleCreateHealthCheck} />
          
          <div className="form-actions-secondary">
            <Link to="/health-checks" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CreateHealthCheckPage; 