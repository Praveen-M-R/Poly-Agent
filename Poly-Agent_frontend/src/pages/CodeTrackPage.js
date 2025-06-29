import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import '../styles/CodeTrack.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const CodeTrackPage = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [githubData, setGithubData] = useState({
    projects: [],
    contributions: [],
    totalCommits: 0,
    totalLinesAdded: 0,
    totalLinesDeleted: 0,
    netLines: 0,
    loading: true
  });
  const [githubLinkInfo, setGithubLinkInfo] = useState({
    needsLink: false,
    error: null
  });
  const [githubUsername, setGithubUsername] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is authenticated
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

  // Fetch GitHub data - moved outside useEffect
  const fetchGithubData = async () => {
    if (!user) return;

    try {
      // Get GitHub stats
      const statsResponse = await fetch('/api/codetrack/stats/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!statsResponse.ok) {
        // If we couldn't get stats, likely need to link GitHub account
        const errorData = await statsResponse.json();
        setGithubLinkInfo({
          needsLink: true,
          error: errorData
        });
        
        setGithubData(prev => ({ ...prev, loading: false }));
        return;
      }

      const statsData = await statsResponse.json();
      
      // Reset GitHub link info since we got successful stats
      setGithubLinkInfo({ needsLink: false, error: null });
      
      // Get repository stats
      const reposResponse = await fetch('/api/codetrack/repositories/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      let reposData = { projects: [] };
      if (reposResponse.ok) {
        reposData = await reposResponse.json();
      }
      
      setGithubData({
        projects: reposData.projects || [],
        contributions: reposData.projects || [],
        totalCommits: statsData.total_commits || 0,
        totalLinesAdded: statsData.total_lines_added || 0,
        totalLinesDeleted: statsData.total_lines_deleted || 0,
        netLines: statsData.net_lines || 0,
        lastSync: statsData.last_synced,
        loading: false
      });
    } catch (err) {
      console.error('Error fetching GitHub data:', err);
      setGithubData(prev => ({ ...prev, loading: false }));
      setError('Failed to load GitHub data. Please try again later.');
    }
  };

  useEffect(() => {
    if (!isLoading && user) {
      fetchGithubData();
    }
  }, [isLoading, user]);

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

  // Handle linking GitHub account
  const handleLinkGitHub = async (e) => {
    e.preventDefault();
    if (!githubUsername) return;
    
    setIsLinking(true);
    setError('');
    setSuccessMessage('');
    
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
        setSuccessMessage(`Successfully linked to GitHub username: ${githubUsername}`);
        setGithubUsername('');
        // Refresh data after successful link
        setGithubData(prev => ({ ...prev, loading: true }));
        fetchGithubData();
      } else {
        // Handle errors from the API
        const errorData = await response.json();
        console.error('Error linking GitHub account:', errorData);
        setError(errorData.error || 'Failed to link GitHub account. Please try again.');
      }
    } catch (err) {
      console.error('Error linking GitHub account:', err);
      setError('Network error when trying to link GitHub account. Please try again.');
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
          <button type="submit" disabled={isLinking} className="card-btn">
            {isLinking ? 'Linking...' : 'Link GitHub Account'}
          </button>
        </form>
        
        <div className="auto-link-section">
          <p>Or let us try to find your GitHub account automatically:</p>
          <button 
            className="auto-link-button"
            onClick={async () => {
              setIsLinking(true);
              setError('');
              setSuccessMessage('');
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
                  setSuccessMessage(`Successfully linked to GitHub username: ${data.github_username}`);
                  setGithubUsername('');
                  // Refresh data after successful link
                  setGithubData(prev => ({ ...prev, loading: true }));
                  fetchGithubData();
                } else {
                  // Handle errors from the API
                  const errorData = await response.json();
                  console.error('Error auto-linking GitHub account:', errorData);
                  setError(errorData.error || 'Failed to auto-link GitHub account. Please try entering your username manually.');
                }
              } catch (err) {
                console.error('Error auto-linking GitHub account:', err);
                setError('Network error when trying to link GitHub account. Please try again.');
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
        <p>Loading CodeTrack data...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>CodeTrack</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/codetrack" className="nav-link active">CodeTrack</Link>
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
      {successMessage && <div className="dashboard-success">{successMessage}</div>}

      <main className="dashboard-content">
        <div className="codetrack-header">
          <h2>Your Repository Contributions</h2>
          <p>Track your contributions across all projects</p>
        </div>
        
        {/* Show GitHub Link UI if needed */}
        {githubLinkInfo.needsLink && renderGitHubLinkPrompt()}
        
        <div className="dashboard-overview">
          <div className="overview-card contribution-overview">
            <h3>Contribution Summary</h3>
            {githubData.loading ? (
              <div className="card-loading">
                <div className="spinner small"></div>
                <p>Loading contribution data...</p>
              </div>
            ) : (
              <div className="github-metrics">
                <div className="metric-item">
                  <div className="metric-value">{githubData.projects.length}</div>
                  <div className="metric-label">Repositories</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{githubData.totalCommits}</div>
                  <div className="metric-label">Total Commits</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value" style={{ color: '#28a745' }}>{githubData.totalLinesAdded}</div>
                  <div className="metric-label">Lines Added</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value" style={{ color: '#d73a49' }}>{githubData.totalLinesDeleted}</div>
                  <div className="metric-label">Lines Deleted</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value" style={{ color: githubData.netLines > 0 ? '#28a745' : '#d73a49' }}>
                    {githubData.netLines}
                  </div>
                  <div className="metric-label">Net Lines</div>
                </div>
              </div>
            )}
            {githubData.lastSync && (
              <div className="sync-info">
                Last synced: {new Date(githubData.lastSync).toLocaleString()}
              </div>
            )}
          </div>
        </div>
        
        {githubData.contributions.length > 0 ? (
          <div className="repositories-section">
            <h3>Project Contributions</h3>
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
                  {githubData.contributions.map((contribution, index) => {
                    return (
                      <tr key={index}>
                        <td>
                          <a href={contribution.repository_url} target="_blank" rel="noopener noreferrer" className="repo-name">
                            {contribution.repository_name}
                            {contribution.repository_is_private && <span className="repo-private-badge">Private</span>}
                          </a>
                          {contribution.repository_description && (
                            <div className="repo-description">{contribution.repository_description}</div>
                          )}
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
        ) : !githubData.loading && !githubLinkInfo.needsLink && (
          <div className="empty-state">
            <h3>No Repository Contributions Found</h3>
            <p>We couldn't find any GitHub contributions for your account. If you've recently made contributions, they may not have been synced yet.</p>
          </div>
        )}
        
        {!githubLinkInfo.needsLink && (
          <div className="codetrack-actions">
            <button 
              className="sync-button" 
              onClick={async () => {
                try {
                  setGithubData(prev => ({ ...prev, loading: true }));
                  
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
                    credentials: 'include'
                  });
                  
                  if (response.ok) {
                    setSuccessMessage('GitHub data synced successfully!');
                    // Refresh data after sync
                    fetchGithubData();
                  } else {
                    setError('Failed to sync GitHub data. Please try again.');
                    setGithubData(prev => ({ ...prev, loading: false }));
                  }
                } catch (error) {
                  console.error('Error syncing data:', error);
                  setError('Failed to sync GitHub data. Please try again.');
                  setGithubData(prev => ({ ...prev, loading: false }));
                }
              }}
            >
              Sync GitHub Data
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default CodeTrackPage; 