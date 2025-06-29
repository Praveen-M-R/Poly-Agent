import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import '../styles/Dashboard.css';
import '../styles/HealthCheck.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const CheckDetailPage = () => {
  const [check, setCheck] = useState(null);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { checkId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCheckDetails = async () => {
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

        // Fetch check logs
        const logsResponse = await fetch(`/health/api/checks/${checkId}/logs/`, {
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
        setLogs(logsData);

        // Prepare stats similar to the Django view
        const today = new Date();
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay());
        
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        const startOfYear = new Date(today.getFullYear(), 0, 1);

        // Filter logs by date periods
        const todayLogs = logsData.filter(log => 
          new Date(log.timestamp).setHours(0, 0, 0, 0) === today.setHours(0, 0, 0, 0)
        );
        
        const weekLogs = logsData.filter(log => 
          new Date(log.timestamp) >= startOfWeek
        );
        
        const monthLogs = logsData.filter(log => 
          new Date(log.timestamp) >= startOfMonth
        );
        
        const yearLogs = logsData.filter(log => 
          new Date(log.timestamp) >= startOfYear
        );

        // Calculate stats for each period
        const getStatusCounts = (logs) => {
          const upCount = logs.filter(log => log.status).length;
          const downCount = logs.filter(log => !log.status).length;
          return [
            { status: false, count: downCount },
            { status: true, count: upCount }
          ];
        };

        const getResponseTimeStats = (logs) => {
          const responseTimes = logs
            .filter(log => log.response_time !== null)
            .map(log => log.response_time);
          
          if (responseTimes.length === 0) {
            return {
              avg_response_time: null,
              min_response_time: null,
              max_response_time: null
            };
          }
          
          return {
            avg_response_time: responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length,
            min_response_time: Math.min(...responseTimes),
            max_response_time: Math.max(...responseTimes)
          };
        };

        const statsData = {
          today: getStatusCounts(todayLogs),
          this_week: getStatusCounts(weekLogs),
          this_month: getStatusCounts(monthLogs),
          this_year: getStatusCounts(yearLogs),
          response_times: {
            today: getResponseTimeStats(todayLogs),
            this_week: getResponseTimeStats(weekLogs),
            this_month: getResponseTimeStats(monthLogs),
            this_year: getResponseTimeStats(yearLogs)
          }
        };

        setStats(statsData);
      } catch (err) {
        console.error('Error fetching check details:', err);
        setError(err.message || 'An error occurred while fetching check details');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCheckDetails();
  }, [checkId]);

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
    if (!timeString) return 'Never';
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

  const getUptimePercentage = (statusCounts) => {
    const totalChecks = statusCounts.reduce((sum, item) => sum + item.count, 0);
    if (totalChecks === 0) return 'N/A';
    
    const upChecks = statusCounts.find(item => item.status)?.count || 0;
    return `${((upChecks / totalChecks) * 100).toFixed(2)}%`;
  };

  // Prepare data for response time chart
  const prepareChartData = () => {
    if (!logs || logs.length === 0) return [];
    
    return logs.slice(0, 30).reverse().map(log => ({
      time: new Date(log.timestamp).toLocaleTimeString(),
      responseTime: log.response_time || 0
    }));
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading check details...</p>
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
          <h1>Check Details</h1>
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
        <div className="check-detail-header">
          <h2>{check.name}</h2>
          <span className={`health-check-status ${getStatusClass(check.is_up)}`}>
            {getStatusText(check.is_up)}
          </span>
        </div>

        <div className="check-detail-container">
          <div className="check-info-card">
            <h3>Check Information</h3>
            <div className="check-info-grid">
              <div className="info-item">
                <span className="info-label">Created At</span>
                <span className="info-value">{formatTime(check.created_at)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Last Ping</span>
                <span className="info-value">{formatTime(check.last_ping)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Ping URL</span>
                <span className="info-value">
                  <code>{`${window.location.origin}/health/ping/${check.ping_url}/`}</code>
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Average Response Time</span>
                <span className="info-value">
                  {getResponseTimeDisplay(check.avg_response_time)}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Min Response Time</span>
                <span className="info-value">
                  {getResponseTimeDisplay(check.min_response_time)}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Max Response Time</span>
                <span className="info-value">
                  {getResponseTimeDisplay(check.max_response_time)}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Total Pings</span>
                <span className="info-value">{check.total_pings}</span>
              </div>
            </div>
          </div>

          <div className="check-stats-card">
            <h3>Uptime Statistics</h3>
            <div className="stats-table">
              <table>
                <thead>
                  <tr>
                    <th>Period</th>
                    <th>Uptime</th>
                    <th>Avg Response</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Today</td>
                    <td>{getUptimePercentage(stats.today)}</td>
                    <td>{getResponseTimeDisplay(stats.response_times.today.avg_response_time)}</td>
                  </tr>
                  <tr>
                    <td>This Week</td>
                    <td>{getUptimePercentage(stats.this_week)}</td>
                    <td>{getResponseTimeDisplay(stats.response_times.this_week.avg_response_time)}</td>
                  </tr>
                  <tr>
                    <td>This Month</td>
                    <td>{getUptimePercentage(stats.this_month)}</td>
                    <td>{getResponseTimeDisplay(stats.response_times.this_month.avg_response_time)}</td>
                  </tr>
                  <tr>
                    <td>This Year</td>
                    <td>{getUptimePercentage(stats.this_year)}</td>
                    <td>{getResponseTimeDisplay(stats.response_times.this_year.avg_response_time)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="response-time-chart-card">
            <h3>Response Time History</h3>
            <div className="chart-container" style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <LineChart
                  data={prepareChartData()}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis 
                    label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="responseTime" 
                    stroke="#4285f4" 
                    activeDot={{ r: 8 }} 
                    name="Response Time"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="recent-logs-card">
            <div className="card-header">
              <h3>Recent Logs</h3>
              <Link 
                to={`/check-logs/${checkId}`} 
                className="btn btn-small"
              >
                View All Logs
              </Link>
            </div>
            <div className="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Response Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.slice(0, 10).map((log, index) => (
                    <tr key={index}>
                      <td>{formatTime(log.timestamp)}</td>
                      <td>
                        <span className={`status-badge ${getStatusClass(log.status)}`}>
                          {getStatusText(log.status)}
                        </span>
                      </td>
                      <td>{getResponseTimeDisplay(log.response_time)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CheckDetailPage; 