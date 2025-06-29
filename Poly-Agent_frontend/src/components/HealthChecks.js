import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HealthCheck.css';

const HealthChecks = () => {
  const [healthChecks, setHealthChecks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHealthChecks = async () => {
      try {
        const response = await fetch('/health/api/checks/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch health checks');
        }

        const data = await response.json();
        console.log('API Response:', data); // Debug the response structure
        
        // Handle different response structures
        if (Array.isArray(data)) {
          setHealthChecks(data);
        } else if (data.results && Array.isArray(data.results)) {
          setHealthChecks(data.results);
        } else {
          // If data is an object but not in the expected format
          console.error('Unexpected response format:', data);
          setHealthChecks([]);
        }
      } catch (err) {
        console.error('Error fetching health checks:', err);
        setError(err.message || 'An error occurred while fetching health checks');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHealthChecks();
  }, []);

  // Function to handle health check deletion
  const handleDeleteCheck = async (checkId) => {
    if (!window.confirm('Are you sure you want to delete this health check?')) {
      return;
    }

    try {
      const response = await fetch(`/health/api/checks/${checkId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to delete health check');
      }

      // Remove the deleted check from state
      setHealthChecks(healthChecks.filter(check => check.id !== checkId));
    } catch (err) {
      console.error('Error deleting health check:', err);
      setError(err.message || 'An error occurred while deleting the health check');
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading health checks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">Error: {error}</p>
        <p>Please try refreshing the page or contact support if the problem persists.</p>
      </div>
    );
  }

  if (!Array.isArray(healthChecks) || healthChecks.length === 0) {
    return (
      <div className="empty-state">
        <h3>No Health Checks Yet</h3>
        <p>Create your first health check to start monitoring your services.</p>
        <Link to="/health-checks/create" className="create-button">
          <i className="fas fa-plus"></i> Create Health Check
        </Link>
      </div>
    );
  }

  const getStatusClass = (check) => {
    if (!check.is_active) return 'status-inactive';
    return check.is_up ? 'status-up' : 'status-down';
  };

  const getStatusText = (check) => {
    if (!check.is_active) return 'Inactive';
    return check.is_up ? 'Up' : 'Down';
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'Never';
    const date = new Date(timeString);
    return date.toLocaleString();
  };

  return (
    <div className="health-checks-container">
      {healthChecks.map(check => (
        <div key={check.id} className="health-check-card">
          <div className="health-check-header">
            <h3 className="health-check-name">{check.name}</h3>
            <span className={`health-check-status ${getStatusClass(check)}`}>
              {getStatusText(check)}
            </span>
          </div>
          
          <p className="health-check-description">
            {check.description || 'No description provided'}
          </p>
          
          <div className="health-check-details">
            <div className="detail-item">
              <span className="detail-label">Last Ping</span>
              <span className="detail-value">{formatTime(check.last_ping)}</span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Ping URL</span>
              <span className="detail-value" style={{ wordBreak: 'break-all' }}>
                {`${window.location.origin}/health/ping/${check.ping_url}/`}
              </span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Avg Response Time</span>
              <span className="detail-value">
                {check.avg_response_time ? `${check.avg_response_time.toFixed(2)} ms` : 'N/A'}
              </span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Target URL</span>
              <span className="detail-value" style={{ wordBreak: 'break-all' }}>
                {check.url || 'N/A'}
              </span>
            </div>
          </div>
          
          <div className="health-check-actions">
            <Link 
              to={`/check/${check.id}`} 
              className="action-button view-button"
            >
              View Details
            </Link>
            <Link 
              to={`/check/${check.id}/edit`} 
              className="action-button edit-button"
            >
              Edit
            </Link>
            <button 
              className="action-button delete-button"
              onClick={() => handleDeleteCheck(check.id)}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default HealthChecks; 