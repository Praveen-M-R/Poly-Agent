import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell 
} from 'recharts';
import '../styles/Dashboard.css';
import '../styles/Reports.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const ReportsPage = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [checks, setChecks] = useState([]);
  const [selectedCheck, setSelectedCheck] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [reportData, setReportData] = useState({
    performance_data: [],
    performance_labels: [],
    uptime_data: [],
    uptime_labels: [],
    cost_data: [],
    cost_labels: [],
    sla_compliance_rate: 0,
    avg_response_time: 0,
    min_response_time: 0,
    max_response_time: 0,
    p95_response_time: 0,
    response_time_trend: 0,
    uptime_percentage: 0,
    downtime_incidents: 0,
    avg_downtime_duration: 0,
    anomalies: []
  });
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch health checks for the dropdown
    const fetchChecks = async () => {
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
        
        // Handle different response structures
        if (Array.isArray(data)) {
          setChecks(data);
        } else if (data.results && Array.isArray(data.results)) {
          setChecks(data.results);
        } else {
          console.error('Unexpected response format:', data);
          setChecks([]);
        }
      } catch (err) {
        console.error('Error fetching health checks:', err);
        setError(err.message || 'An error occurred while fetching health checks');
      }
    };

    fetchChecks();
  }, []);

  useEffect(() => {
    // Fetch report data when selection changes
    const fetchReportData = async () => {
      setIsLoading(true);
      try {
        // Use the correct API endpoint for reports
        const response = await fetch(`/health/api/reports/?days=${timeRangeToDays(timeRange)}&check_id=${selectedCheck === 'all' ? '' : selectedCheck}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch report data');
        }

        const data = await response.json();
        console.log('Report data received:', data);
        
        // Transform the data to match the expected format
        const transformedData = {
          performance_data: data.response_time_data?.map(item => ({
            name: new Date(item.timestamp).toLocaleString(),
            value: item.response_time
          })) || [],
          performance_labels: data.response_time_data?.map(item => 
            new Date(item.timestamp).toLocaleString()
          ) || [],
          uptime_data: [
            { name: 'Up', value: data.uptime_percentage || 0 },
            { name: 'Down', value: 100 - (data.uptime_percentage || 0) }
          ],
          uptime_labels: ['Up', 'Down'],
          sla_compliance_rate: data.uptime_percentage || 0,
          avg_response_time: data.response_time_stats?.avg_response || 0,
          min_response_time: data.response_time_stats?.min_response || 0,
          max_response_time: data.response_time_stats?.max_response || 0,
          uptime_percentage: data.uptime_percentage || 0,
          downtime_incidents: data.downtime_incidents || 0,
          anomalies: data.anomalies || []
        };
        
        setReportData(transformedData);
      } catch (err) {
        console.error('Error fetching report data:', err);
        setError(err.message || 'An error occurred while fetching report data');
      } finally {
        setIsLoading(false);
      }
    };

    // Convert time range to days for API
    const timeRangeToDays = (range) => {
      switch(range) {
        case '24h': return 1;
        case '7d': return 7;
        case '30d': return 30;
        case '90d': return 90;
        default: return 7;
      }
    };

    if (checks.length > 0 || selectedCheck === 'all') {
      fetchReportData();
    }
  }, [selectedCheck, timeRange, checks]);

  const handleLogout = async () => {
    try {
      await fetch('/api/users/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      
      localStorage.removeItem('user');
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Failed to logout. Please try again.');
    }
  };

  const handleCheckChange = (e) => {
    setSelectedCheck(e.target.value);
  };

  const handleTimeRangeChange = (e) => {
    setTimeRange(e.target.value);
  };

  const handleExportCSV = () => {
    window.location.href = `/health/api/reports/export/?time_range=${timeRange}&check_id=${selectedCheck}`;
  };

  const handleGenerateReport = () => {
    window.location.href = `/health/api/reports/generate/?time_range=${timeRange}&check_id=${selectedCheck}`;
  };

  const formatResponseTime = (time) => {
    if (time === null || time === undefined) return 'N/A';
    return `${time.toFixed(2)} ms`;
  };

  const preparePerformanceData = () => {
    if (!reportData.performance_data) return [];
    
    return reportData.performance_data.map(item => {
      if (typeof item === 'object' && item !== null) {
        return {
          name: typeof item.name === 'string' ? item.name : 'Unknown',
          responseTime: typeof item.value === 'number' ? item.value : 0
        };
      } else {
        return { name: 'Unknown', responseTime: 0 };
      }
    });
  };

  const prepareUptimeData = () => {
    if (!reportData.uptime_data) return [];
    
    return reportData.uptime_data.map(item => {
      if (typeof item === 'object' && item !== null) {
        return {
          name: typeof item.name === 'string' ? item.name : 'Unknown',
          uptime: typeof item.value === 'number' ? item.value : 0
        };
      } else {
        return { name: 'Unknown', uptime: 0 };
      }
    });
  };

  const prepareCostData = () => {
    return [];
  };

  const prepareSLAData = () => {
    const compliantPercentage = reportData.sla_compliance_rate || 0;
    const nonCompliantPercentage = 100 - compliantPercentage;
    
    return [
      { name: 'Compliant', value: compliantPercentage },
      { name: 'Non-Compliant', value: nonCompliantPercentage > 0 ? nonCompliantPercentage : 0 }
    ];
  };

  const COLORS = ['#00C49F', '#FF8042'];

  if (isLoading && checks.length === 0) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading report data...</p>
      </div>
    );
  }

  if (error && !checks.length) {
    return (
      <div className="error-container">
        <p className="error-message">Error: {error}</p>
        <p>Please try refreshing the page or contact support if the problem persists.</p>
        <button 
          onClick={() => navigate('/dashboard')} 
          className="btn btn-primary"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Health Check Reports</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/reports" className="nav-link active">Reports</Link>
            <Link to="/failed-checks" className="nav-link">Failed Checks</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
          </nav>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="reports-container">
          <div className="reports-filter-bar">
            <div className="filter-group">
              <label htmlFor="check-select">Health Check:</label>
              <select 
                id="check-select" 
                value={selectedCheck}
                onChange={handleCheckChange}
              >
                <option value="all">All Checks</option>
                {checks.map(check => (
                  <option key={check.id} value={check.id}>
                    {check.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="filter-group">
              <label htmlFor="time-range">Time Range:</label>
              <select 
                id="time-range" 
                value={timeRange}
                onChange={handleTimeRangeChange}
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>
            
            <div className="filter-actions">
              <button 
                className="btn btn-secondary"
                onClick={handleExportCSV}
              >
                Export CSV
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleGenerateReport}
              >
                Generate PDF Report
              </button>
            </div>
          </div>
          
          {isLoading ? (
            <div className="loading-container">
              <div className="spinner medium"></div>
              <p>Loading report data...</p>
            </div>
          ) : (
            <div className="reports-grid">
              <div className="report-card performance-card">
                <h3>Response Time Performance</h3>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                      data={preparePerformanceData()}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis 
                        label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip />
                      <Line 
                        type="monotone" 
                        dataKey="responseTime" 
                        stroke="#4285f4" 
                        activeDot={{ r: 8 }} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="metrics-summary">
                  <div className="metric">
                    <span className="metric-label">Average:</span>
                    <span className="metric-value">{formatResponseTime(reportData.avg_response_time)}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Min:</span>
                    <span className="metric-value">{formatResponseTime(reportData.min_response_time)}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Max:</span>
                    <span className="metric-value">{formatResponseTime(reportData.max_response_time)}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">95th Percentile:</span>
                    <span className="metric-value">{formatResponseTime(reportData.p95_response_time)}</span>
                  </div>
                </div>
              </div>
              
              <div className="report-card uptime-card">
                <h3>Uptime Performance</h3>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={prepareUptimeData()}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis 
                        label={{ value: 'Uptime %', angle: -90, position: 'insideLeft' }}
                        domain={[0, 100]}
                      />
                      <Tooltip />
                      <Bar dataKey="uptime" fill="#4CAF50" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="metrics-summary">
                  <div className="metric">
                    <span className="metric-label">Uptime:</span>
                    <span className="metric-value">{(reportData.uptime_percentage || 0).toFixed(2)}%</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Downtime Incidents:</span>
                    <span className="metric-value">{reportData.downtime_incidents || 0}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Avg Downtime:</span>
                    <span className="metric-value">{(reportData.avg_downtime_duration || 0).toFixed(2)}s</span>
                  </div>
                </div>
              </div>
              
              <div className="report-card sla-card">
                <h3>SLA Compliance</h3>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={prepareSLAData()}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {prepareSLAData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="metrics-summary">
                  <div className="metric">
                    <span className="metric-label">Target SLA:</span>
                    <span className="metric-value">99.9%</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Current SLA:</span>
                    <span className="metric-value">{(reportData.sla_compliance_rate || 0).toFixed(2)}%</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Status:</span>
                    <span className={`metric-value ${(reportData.sla_compliance_rate || 0) >= 99.9 ? 'status-up' : 'status-down'}`}>
                      {(reportData.sla_compliance_rate || 0) >= 99.9 ? 'Compliant' : 'Non-Compliant'}
                    </span>
                  </div>
                </div>
              </div>
              
              {reportData.anomalies && reportData.anomalies.length > 0 && (
                <div className="report-card anomalies-card">
                  <h3>Detected Anomalies</h3>
                  <div className="anomalies-list">
                    {reportData.anomalies.map((anomaly, index) => (
                      <div key={index} className={`anomaly-item severity-${anomaly.severity}`}>
                        <div className="anomaly-header">
                          <h4>{anomaly.title}</h4>
                          <span className="anomaly-time">{new Date(anomaly.timestamp).toLocaleString()}</span>
                        </div>
                        <p>{anomaly.description}</p>
                        <div className="anomaly-meta">
                          <span className="anomaly-metric">Metric: {anomaly.metric}</span>
                          <span className="anomaly-severity">Severity: {anomaly.severity}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ReportsPage; 