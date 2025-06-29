import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HealthCheck.css';
import { 
  FaCheckCircle, 
  FaTimesCircle, 
  FaExclamationTriangle, 
  FaServer, 
  FaClock, 
  FaLink, 
  FaChartLine,
  FaCog,
  FaExternalLinkAlt,
  FaCopy,
  FaPlus,
  FaTrash,
  FaEdit
} from 'react-icons/fa';
import { toast } from 'react-toastify';

const HealthCheckDashboard = () => {
  const [summary, setSummary] = useState({
    totalChecks: 0,
    activeChecks: 0,
    upChecks: 0,
    downChecks: 0,
    healthPercentage: 0,
    recentFailures: []
  });
  const [healthChecks, setHealthChecks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch summary data
        const summaryResponse = await fetch('/health/api/checks/summary/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!summaryResponse.ok) {
          throw new Error('Failed to fetch health check summary');
        }

        const summaryData = await summaryResponse.json();
        setSummary({
          totalChecks: summaryData.total_checks || 0,
          activeChecks: summaryData.active_checks || 0,
          upChecks: summaryData.up_checks || 0,
          downChecks: summaryData.down_checks || 0,
          healthPercentage: summaryData.health_percentage || 0,
          recentFailures: summaryData.recent_failures || []
        });
        
        // Fetch health checks list
        const checksResponse = await fetch('/health/api/checks/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!checksResponse.ok) {
          throw new Error('Failed to fetch health checks');
        }

        const checksData = await checksResponse.json();
        setHealthChecks(Array.isArray(checksData) ? checksData : checksData.results || []);
      } catch (err) {
        console.error('Error fetching health check data:', err);
        setError(err.message || 'An error occurred while fetching data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatTime = (timeString) => {
    if (!timeString) return 'Never';
    const date = new Date(timeString);
    return date.toLocaleString();
  };
  
  const getStatusClass = (check) => {
    if (!check.is_active) return 'status-inactive';
    return check.is_up ? 'status-up' : 'status-down';
  };
  
  const getStatusText = (check) => {
    if (!check.is_active) return 'Inactive';
    return check.is_up ? 'Up' : 'Down';
  };
  
  const getStatusIcon = (check) => {
    if (!check.is_active) return <FaExclamationTriangle className="status-icon inactive" />;
    return check.is_up ? 
      <FaCheckCircle className="status-icon up" /> : 
      <FaTimesCircle className="status-icon down" />;
  };
  
  const formatResponseTime = (time) => {
    if (!time) return 'N/A';
    return `${time.toFixed(2)} ms`;
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!', {
      position: 'top-right',
      autoClose: 2000,
      hideProgressBar: true,
    });
  };
  
  const getUptimeClass = (check) => {
    if (!check.avg_response_time) return 'uptime-unknown';
    if (check.avg_response_time < 200) return 'uptime-excellent';
    if (check.avg_response_time < 500) return 'uptime-good';
    if (check.avg_response_time < 1000) return 'uptime-fair';
    return 'uptime-poor';
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading health check summary...</p>
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
    <div className="health-dashboard">
      <div className="dashboard-section">
        <h2>Health Check Summary</h2>
        <div className="summary-stats">
          <div className="stat-card">
            <div className="stat-value">{summary.totalChecks}</div>
            <div className="stat-label">Total Checks</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.activeChecks}</div>
            <div className="stat-label">Active</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.upChecks}</div>
            <div className="stat-label">Up</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.downChecks}</div>
            <div className="stat-label">Down</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.healthPercentage.toFixed(1)}%</div>
            <div className="stat-label">Health Rate</div>
          </div>
        </div>
      </div>

      <div className="dashboard-section">
        <div className="section-header">
          <h2>Your Health Checks</h2>
          <Link to="/health-checks/create" className="primary-button">
            <FaPlus /> New Health Check
          </Link>
        </div>
        
        {healthChecks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <FaServer size={48} />
            </div>
            <h3>No Health Checks Found</h3>
            <p>Create your first health check to start monitoring your services</p>
            <Link to="/health-checks/create" className="primary-button">
              <FaPlus /> Create Health Check
            </Link>
          </div>
        ) : (
          <div className="health-checks-container">
            <div className="health-checks-filters">
              <div className="filter-group">
                <span className="filter-label">Status:</span>
                <button className="filter-button active">All ({healthChecks.length})</button>
                <button className="filter-button">
                  <FaCheckCircle className="status-icon up" /> Up ({summary.upChecks})
                </button>
                <button className="filter-button">
                  <FaTimesCircle className="status-icon down" /> Down ({summary.downChecks})
                </button>
                <button className="filter-button">
                  <FaExclamationTriangle className="status-icon inactive" /> Inactive ({healthChecks.length - summary.activeChecks})
                </button>
              </div>
            </div>
            
            <div className="health-checks-grid">
              {healthChecks.map(check => {
                const pingUrl = `${window.location.origin.replace('3000', '8000')}/health/ping/${check.ping_url}/`;
                const uptimeClass = getUptimeClass(check);
                
                return (
                  <div key={check.id} className={`health-check-card ${getStatusClass(check)}`}>
                    <div className="health-check-header">
                      <div className="status-indicator">
                        {getStatusIcon(check)}
                        <span className="status-text">{getStatusText(check)}</span>
                      </div>
                      <div className="health-check-actions">
                        <button 
                          className="icon-button" 
                          onClick={() => copyToClipboard(pingUrl)}
                          title="Copy Ping URL"
                        >
                          <FaCopy />
                        </button>
                        <Link 
                          to={`/check/${check.id}`} 
                          className="icon-button"
                          title="View Details"
                        >
                          <FaExternalLinkAlt />
                        </Link>
                      </div>
                    </div>
                    
                    <h3 className="health-check-name" title={check.name}>
                      {check.name}
                    </h3>
                    
                    {check.description && (
                      <p className="health-check-description">
                        {check.description}
                      </p>
                    )}
                    
                    <div className="health-check-metrics">
                      <div className="metric">
                        <div className="metric-label">Last Ping</div>
                        <div className="metric-value">
                          <FaClock className="metric-icon" />
                          {formatTime(check.last_ping) || 'Never'}
                        </div>
                      </div>
                      
                      <div className="metric">
                        <div className="metric-label">Response Time</div>
                        <div className={`metric-value ${uptimeClass}`}>
                          <FaChartLine className="metric-icon" />
                          {formatResponseTime(check.avg_response_time)}
                        </div>
                      </div>
                      
                      <div className="metric">
                        <div className="metric-label">Uptime</div>
                        <div className="metric-value">
                          <FaCheckCircle className="metric-icon" />
                          {check.avg_response_time ? '99.9%' : 'N/A'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="health-check-url">
                      <FaLink className="url-icon" />
                      <a 
                        href={check.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="url-link"
                        title={check.url || 'No URL provided'}
                      >
                        {check.url ? (check.url.length > 40 ? 
                          check.url.substring(0, 37) + '...' : check.url) : 'No URL provided'}
                      </a>
                    </div>
                    
                    <div className="health-check-ping-url">
                      <span className="ping-label">Ping URL:</span>
                      <div className="ping-url-container">
                        <code className="ping-url">
                          {pingUrl}
                        </code>
                        <button 
                          className="copy-button"
                          onClick={() => copyToClipboard(pingUrl)}
                          title="Copy to clipboard"
                        >
                          <FaCopy size={12} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="dashboard-section">
        <div className="section-header">
          <h2>Recent Failures</h2>
          <Link to="/failed-checks" className="view-all-link">View All</Link>
        </div>
        {summary.recentFailures?.length === 0 ? (
          <div className="empty-state">
            <p>No recent failures. All systems operational!</p>
          </div>
        ) : (
          <div className="failures-list">
            {(summary.recentFailures || []).slice(0, 3).map((failure, index) => (
              <div key={index} className="failure-item">
                <div className="failure-name">{failure.health_check?.name || 'Unknown Check'}</div>
                <div className="failure-time">Failed at: {formatTime(failure.failed_at)}</div>
                <Link to={`/check/${failure.health_check?.id}`} className="view-details-link">
                  View Details
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="dashboard-actions">
        <Link to="/health-checks/create" className="dashboard-action-button create">
          Create New Health Check
        </Link>
        <Link to="/reports" className="dashboard-action-button">
          View Reports
        </Link>
      </div>
    </div>
  );
};

export default HealthCheckDashboard;
