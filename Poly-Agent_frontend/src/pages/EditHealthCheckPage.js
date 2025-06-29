import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import HealthCheckForm from '../components/HealthCheckForm';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const EditHealthCheckPage = () => {
  const [check, setCheck] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const { checkId } = useParams();
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchCheckDetails = async () => {
      try {
        const response = await fetch(`/health/api/checks/${checkId}/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch health check details');
        }

        const data = await response.json();
        setCheck(data);
      } catch (err) {
        console.error('Error fetching health check details:', err);
        setError(err.message || 'An error occurred while fetching health check details');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCheckDetails();
  }, [checkId]);
  
  const handleUpdateHealthCheck = async (formData) => {
    try {
      console.log('Updating health check data:', formData);
      
      const response = await fetch(`/health/api/checks/${checkId}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
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
          throw new Error(errorData.detail || 'Failed to update health check');
        }
      }
      
      // Navigate to health check details on success
      navigate(`/check/${checkId}`);
    } catch (err) {
      console.error('Error updating health check:', err);
      setError(err.message || 'An error occurred while updating the health check');
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

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading health check details...</p>
      </div>
    );
  }

  if (error && !check) {
    return (
      <div className="error-container">
        <p className="error-message">Error: {error}</p>
        <p>Please try refreshing the page or contact support if the problem persists.</p>
        <button 
          onClick={() => navigate('/health-checks')} 
          className="btn btn-primary"
        >
          Back to Health Checks
        </button>
      </div>
    );
  }
  
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Edit Health Check</h1>
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
              Update the details of your health check monitoring configuration.
            </p>
          </div>
          
          {check && (
            <HealthCheckForm 
              onSubmit={handleUpdateHealthCheck} 
              initialValues={check}
              isEditing={true}
            />
          )}
          
          <div className="form-actions-secondary">
            <Link to={`/check/${checkId}`} className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};

export default EditHealthCheckPage; 