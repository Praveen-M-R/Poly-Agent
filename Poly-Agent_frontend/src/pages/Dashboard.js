import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [githubStats, setGithubStats] = useState({
    repositories: [],
    totalCommits: 0,
    totalLines: 0,
    totalLinesAdded: 0,
    totalLinesDeleted: 0,
    netLines: 0,
    repositoriesCount: 0,
    loading: true
  });
  // Function to get time-appropriate greeting
  const getTimeBasedGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const [healthStats, setHealthStats] = useState({
    totalChecks: 0,
    activeChecks: 0,
    upChecks: 0,
    downChecks: 0,
    healthPercentage: 0,
    loading: true
  });
  const [githubLinkInfo, setGithubLinkInfo] = useState({
    needsLink: false,
    error: null
  });
  const [githubUsername, setGithubUsername] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const navigate = useNavigate();

  // Fetch GitHub repository stats function (moved outside useEffect)
  const fetchGithubStats = async () => {
    try {
      // Fetch GitHub stats from our new CodeTrack API
      const response = await fetch('/api/codetrack/stats/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        // If the user doesn't have a GitHub profile yet, get error info
        const errorData = await response.json();
        setGithubLinkInfo({
          needsLink: true,
          error: errorData
        });
        
        // Set empty stats
        setGithubStats({
          repositories: [],
          totalCommits: 0,
          totalLines: 0,
          totalLinesAdded: 0,
          totalLinesDeleted: 0,
          netLines: 0,
          repositoriesCount: 0,
          loading: false
        });
        return;
      }

      const data = await response.json();
      
      // Reset needsLink flag if we got successful stats
      setGithubLinkInfo({ needsLink: false, error: null });
      
      // Map the API response to our state structure
      setGithubStats({
        repositories: [],  // We'll fetch repositories in a separate call
        totalCommits: data.total_commits || 0,
        totalLines: (data.total_lines_added || 0) + (data.total_lines_deleted || 0),
        totalLinesAdded: data.total_lines_added || 0,
        totalLinesDeleted: data.total_lines_deleted || 0,
        netLines: data.net_lines || 0,
        repositoriesCount: data.repositories_count || 0,
        loading: false
      });
      
      // Now fetch repository details
      fetchUserRepositories();
    } catch (err) {
      console.error('Error fetching GitHub stats:', err);
      setGithubStats(prev => ({ ...prev, loading: false }));
    }
  };
  
  // Fetch user repositories function (moved outside useEffect)
  const fetchUserRepositories = async () => {
    try {
      const response = await fetch('/api/codetrack/repositories/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      
      // Use the projects data directly from the API response
      setGithubStats(prev => ({
        ...prev,
        repositories: data.projects || [],
        per_project_contributions: data.projects || []
      }));
    } catch (err) {
      console.error('Error fetching user repositories:', err);
    }
  };

  useEffect(() => {
    // Load user data from localStorage
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    
    // Check if user is authenticated by making a request to the profile endpoint
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/users/profile/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);
          localStorage.setItem('user', JSON.stringify(data));
        } else {
          // If not authenticated, redirect to login
          navigate('/login');
        }
      } catch (err) {
        console.error('Authentication check failed:', err);
        setError('Failed to verify authentication. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [navigate]);

  useEffect(() => {
    // Fetch health check summary stats
    const fetchHealthStats = async () => {
      try {
        const response = await fetch('/health/api/checks/summary/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          setHealthStats({
            totalChecks: data.total_checks || 0,
            activeChecks: data.active_checks || 0,
            upChecks: data.up_checks || 0,
            downChecks: data.down_checks || 0,
            healthPercentage: data.health_percentage || 0,
            loading: false
          });
        } else {
          console.error('Failed to fetch health check stats');
          setHealthStats(prev => ({ ...prev, loading: false }));
        }
      } catch (err) {
        console.error('Error fetching health check stats:', err);
        setHealthStats(prev => ({ ...prev, loading: false }));
      }
    };

    if (!isLoading) {
      fetchGithubStats();
      fetchHealthStats();
    }
  }, [isLoading]);

  const handleLogout = async () => {
    try {
      await fetch('/api/users/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      
      // Clear local storage and state
      localStorage.removeItem('user');
      setUser(null);
      
      // Redirect to login page
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Failed to logout. Please try again.');
    }
  };

  // Handle submitting GitHub username
  const handleLinkGitHub = async (e) => {
    e.preventDefault();
    if (!githubUsername) return;
    
    setIsLinking(true);
    
    try {
      // Get CSRF token from cookie
      const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
      const csrfToken = csrfCookie ? csrfCookie.split('=')[1] : '';
      
      const response = await fetch('/api/codetrack/sync/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'include',
        body: JSON.stringify({ github_username: githubUsername })
      });
      
      if (response.ok) {
        const data = await response.json();
        // Successfully linked account - refresh stats
        setGithubLinkInfo({ needsLink: false, error: null });
        setGithubUsername('');
        fetchGithubStats();
      } else {
        // Handle errors from the API
        const errorData = await response.json();
        console.error('Error linking GitHub account:', errorData);
        setGithubLinkInfo(prev => ({ ...prev, error: errorData }));
      }
    } catch (err) {
      console.error('Error linking GitHub account:', err);
    } finally {
      setIsLinking(false);
    }
  };

  // Render the GitHub linking component
  const renderGitHubLinkPrompt = () => {
    if (!githubLinkInfo.needsLink) return null;
    
    return (
      <div className="github-link-prompt">
        <h3>Link Your GitHub Account</h3>
        <p>We couldn't find your GitHub statistics. Link your GitHub account to track your contributions.</p>
        
        {githubLinkInfo.error && (
          <div className="link-error-info">
            <p>Your email: {githubLinkInfo.error.email || 'Not available'}</p>
            {githubLinkInfo.error.next_steps && (
              <ul className="next-steps">
                {githubLinkInfo.error.next_steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            )}
          </div>
        )}
        
        <form onSubmit={handleLinkGitHub} className="github-link-form">
          <input
            type="text"
            placeholder="Enter your GitHub username"
            value={githubUsername}
            onChange={(e) => setGithubUsername(e.target.value)}
            disabled={isLinking}
            required
          />
          <button type="submit" disabled={isLinking}>
            {isLinking ? 'Linking...' : 'Link GitHub Account'}
          </button>
        </form>
        
        <div className="auto-link-section">
          <p>Or let us try to find your GitHub account automatically:</p>
          <button 
            className="auto-link-button"
            onClick={async () => {
              setIsLinking(true);
              try {
                // Get CSRF token from cookie
                const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
                const csrfToken = csrfCookie ? csrfCookie.split('=')[1] : '';
                
                const response = await fetch('/api/codetrack/sync/', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                  },
                  credentials: 'include',
                  // Send an empty body to trigger automatic lookup
                  body: JSON.stringify({})
                });
                
                if (response.ok) {
                  const data = await response.json();
                  // Successfully linked account - refresh stats
                  setGithubLinkInfo({ needsLink: false, error: null });
                  fetchGithubStats();
                } else {
                  // Handle errors from the API
                  const errorData = await response.json();
                  console.error('Error auto-linking GitHub account:', errorData);
                  setGithubLinkInfo(prev => ({ ...prev, error: errorData }));
                }
              } catch (err) {
                console.error('Error auto-linking GitHub account:', err);
              } finally {
                setIsLinking(false);
              }
            }}
            disabled={isLinking}
          >
            {isLinking ? 'Finding Account...' : 'Find My GitHub Account'}
          </button>
        </div>
        
        <div className="github-link-options">
          <Link to="/profile" className="profile-link">Go to Profile Settings</Link>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>Poly Agent</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link active">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
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

      {error && <div className="dashboard-error">{error}</div>}

      <main className="dashboard-content">
        <div className="dashboard-welcome">
          <h2>
            {getTimeBasedGreeting()}
            {user?.name ? `, ${user.name}` : ''}
          </h2>
          <p>Watching every deploy. Every ping. Every line of code.</p>
        </div>
        
        {/* Conditionally show GitHub link prompt */}
        {githubLinkInfo.needsLink && renderGitHubLinkPrompt()}
        
        <div className="dashboard-overview">
          <div className="overview-card health-overview">
            <h3>Health Monitoring Overview</h3>
            {healthStats.loading ? (
              <div className="card-loading">
                <div className="spinner small"></div>
                <p>Loading health stats...</p>
              </div>
            ) : (
              <div className="health-metrics">
                <div className="metric-item">
                  <div className="metric-value">{healthStats.totalChecks}</div>
                  <div className="metric-label">Total Checks</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{healthStats.upChecks}</div>
                  <div className="metric-label">Up</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{healthStats.downChecks}</div>
                  <div className="metric-label">Down</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{healthStats.healthPercentage.toFixed(1)}%</div>
                  <div className="metric-label">Health Rate</div>
                </div>
              </div>
            )}
            <Link to="/health-checks" className="card-btn">Manage Health Checks</Link>
          </div>
          
          <div className="overview-card github-overview">
            <h3>CodeTrack Overview</h3>
            {githubStats.loading ? (
              <div className="card-loading">
                <div className="spinner small"></div>
                <p>Loading CodeTrack stats...</p>
              </div>
            ) : (
              <div className="github-metrics">
                <div className="metric-item">
                  <div className="metric-value">{githubStats.repositories.length}</div>
                  <div className="metric-label">Repositories</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{githubStats.totalCommits}</div>
                  <div className="metric-label">Commits</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{githubStats.totalLines.toLocaleString()}</div>
                  <div className="metric-label">Lines Changed</div>
                </div>
              </div>
            )}
            <Link to="/codetrack" className="card-btn">View All Projects</Link>
          </div>
        </div>

        {/* <div className="dashboard-cards">
          <div className="dashboard-card">
            <h3>Service Health Tracker</h3>
            <p>Monitor your application health and performance with real-time alerts and tracking.</p>
            <div className="card-footer">
              <Link to="/health-checks" className="card-btn">View Health Checks</Link>
            </div>
          </div>
          
          <div className="dashboard-card">
            <h3>CodeTrack</h3>
            <p>Track your personal repository activity, contributions, and code statistics across all projects.</p>
            <div className="card-footer">
              <Link to="/codetrack" className="card-btn">View My Projects</Link>
            </div>
          </div>
        </div> */}
        
        {githubStats.repositories.length > 0 && (
          <div className="repositories-section">
            <h3>Your Active Repositories</h3>
            <div className="repositories-table-wrapper">
              <table className="repositories-table">
                <thead>
                  <tr>
                    <th>Repository</th>
                    <th>Commits</th>
                    <th>Lines Added</th>
                    <th>Lines Deleted</th>
                    <th>Net Lines</th>
                  </tr>
                </thead>
                <tbody>
                  {githubStats.per_project_contributions && githubStats.per_project_contributions.map((contribution, index) => {
                    return (
                      <tr key={index}>
                        <td>
                          <a href={contribution.repository_url} target="_blank" rel="noopener noreferrer" className="repo-name">
                            {contribution.repository_name}
                          </a>
                        </td>
                        <td>{contribution.commits || 0}</td>
                        <td className="lines-added">{contribution.lines_added || 0}</td>
                        <td className="lines-deleted">{contribution.lines_deleted || 0}</td>
                        <td className={`net-lines ${contribution.net_lines > 0 ? 'positive' : contribution.net_lines < 0 ? 'negative' : ''}`}>
                          {contribution.net_lines || 0}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard; 