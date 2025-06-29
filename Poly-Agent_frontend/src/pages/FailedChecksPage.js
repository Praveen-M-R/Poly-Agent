import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const FailedChecksPage = () => {
  const [failedChecks, setFailedChecks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFailedChecks = async () => {
      try {
        const response = await fetch('/health/api/failed_checks/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch failed checks');
        }

        const data = await response.json();
        
        // Handle different response structures
        if (Array.isArray(data)) {
          setFailedChecks(data);
        } else if (data.results && Array.isArray(data.results)) {
          setFailedChecks(data.results);
        } else {
          console.error('Unexpected response format:', data);
          setFailedChecks([]);
        }
      } catch (err) {
        console.error('Error fetching failed checks:', err);
        setError(err.message || 'An error occurred while fetching failed checks');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFailedChecks();
  }, []);

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

  const formatTime = (timeString) => {
    if (!timeString) return 'N/A';
    const date = new Date(timeString);
    return date.toLocaleString();
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    
    if (seconds < 60) {
      return `${seconds} seconds`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours} ${hours === 1 ? 'hour' : 'hours'} ${minutes > 0 ? `${minutes} ${minutes === 1 ? 'minute' : 'minutes'}` : ''}`;
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading failed checks...</p>
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

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Failed Health Checks</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/reports" className="nav-link">Reports</Link>
            <Link to="/failed-checks" className="nav-link active">Failed Checks</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
          </nav>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="failed-checks-container">
          <div className="page-description">
            <p>
              This page shows health checks that have failed. Review these issues to ensure your services are running properly.
            </p>
          </div>
          
          {failedChecks.length > 0 ? (
            <div className="failed-checks-table-wrapper">
              <table className="failed-checks-table">
                <thead>
                  <tr>
                    <th>Check Name</th>
                    <th>Failed At</th>
                    <th>Duration</th>
                    <th>Error</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {failedChecks.map((failedCheck, index) => (
                    <tr key={index}>
                      <td>
                        <span className="check-name">{failedCheck.check_name.name}</span>
                      </td>
                      <td>{formatTime(failedCheck.failed_at)}</td>
                      <td>{formatDuration(failedCheck.duration)}</td>
                      <td className="error-message">{failedCheck.error || 'Unknown error'}</td>
                      <td>
                        <div className="check-actions">
                          <Link 
                            to={`/check/${failedCheck.check_name.id}`} 
                            className="action-button view-button"
                          >
                            View Check
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <h3>No Failed Checks</h3>
              <p>All your health checks are currently operational. Great job!</p>
              <Link to="/health-checks" className="btn btn-primary">
                View All Health Checks
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default FailedChecksPage; 