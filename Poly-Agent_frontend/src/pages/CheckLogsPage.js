import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const CheckLogsPage = () => {
  const [check, setCheck] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { checkId } = useParams();
  const navigate = useNavigate();
  const logsPerPage = 20;

  useEffect(() => {
    const fetchCheckLogs = async () => {
      try {
        // Fetch check details
        const checkResponse = await fetch(`/health/api/checks/${checkId}/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!checkResponse.ok) {
          throw new Error('Failed to fetch check details');
        }

        const checkData = await checkResponse.json();
        setCheck(checkData);

        // Fetch check logs with pagination
        const logsResponse = await fetch(`/health/api/checks/${checkId}/logs/?page=${currentPage}&page_size=${logsPerPage}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!logsResponse.ok) {
          throw new Error('Failed to fetch check logs');
        }

        const logsData = await logsResponse.json();
        
        // Handle pagination data
        if (logsData.results && Array.isArray(logsData.results)) {
          setLogs(logsData.results);
          setTotalPages(Math.ceil(logsData.count / logsPerPage));
        } else if (Array.isArray(logsData)) {
          // If the API doesn't return paginated data, handle the array directly
          setLogs(logsData);
          setTotalPages(Math.ceil(logsData.length / logsPerPage));
        } else {
          console.error('Unexpected logs response format:', logsData);
          setLogs([]);
          setTotalPages(1);
        }
      } catch (err) {
        console.error('Error fetching check logs:', err);
        setError(err.message || 'An error occurred while fetching check logs');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCheckLogs();
  }, [checkId, currentPage, logsPerPage]);

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

  const handlePageChange = (page) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'N/A';
    const date = new Date(timeString);
    return date.toLocaleString();
  };

  const getStatusClass = (status) => {
    return status ? 'status-up' : 'status-down';
  };

  const getStatusText = (status) => {
    return status ? 'Up' : 'Down';
  };

  const getResponseTimeDisplay = (time) => {
    if (time === null || time === undefined) return 'N/A';
    return `${time.toFixed(2)} ms`;
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading check logs...</p>
      </div>
    );
  }

  if (error) {
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

  if (!check) {
    return (
      <div className="error-container">
        <p className="error-message">Check not found</p>
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
          <h1>Check Logs</h1>
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

      <main className="dashboard-content">
        <div className="check-logs-header">
          <h2>{check.name} - Logs</h2>
          <Link 
            to={`/check/${checkId}`} 
            className="btn btn-secondary"
          >
            Back to Check Details
          </Link>
        </div>

        <div className="check-logs-container">
          {logs.length > 0 ? (
            <div className="logs-table-card">
              <table className="logs-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Status Code</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, index) => (
                    <tr key={index}>
                      <td>{formatTime(log.timestamp)}</td>
                      <td>
                        <span className={`status-badge ${getStatusClass(log.status)}`}>
                          {getStatusText(log.status)}
                        </span>
                      </td>
                      <td>{getResponseTimeDisplay(log.response_time)}</td>
                      <td>{log.status_code || 'N/A'}</td>
                      <td className="log-error">{log.error || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="no-logs-message">
              No logs available for this check.
            </div>
          )}

          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => handlePageChange(currentPage - 1)} 
                disabled={currentPage === 1}
                className="pagination-btn"
              >
                Previous
              </button>
              
              <div className="pagination-info">
                Page {currentPage} of {totalPages}
              </div>
              
              <button 
                onClick={() => handlePageChange(currentPage + 1)} 
                disabled={currentPage === totalPages}
                className="pagination-btn"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default CheckLogsPage; 