import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const ProfilePage = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [githubProfile, setGithubProfile] = useState(null);
  const [isLoadingGithub, setIsLoadingGithub] = useState(true);
  const [githubUsername, setGithubUsername] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Load user data from localStorage
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    
    // Fetch user profile data
    const fetchProfile = async () => {
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
          // Now fetch GitHub profile data
          fetchGithubProfile();
        } else {
          // If not authenticated, redirect to login
          navigate('/login');
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
        setError('Failed to load profile data. Please try again.');
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [navigate]);

  // Fetch GitHub profile data
  const fetchGithubProfile = async () => {
    setIsLoadingGithub(true);
    try {
      // First try the sync status endpoint
      const response = await fetch('/api/codetrack/sync/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setGithubProfile(data);
      } else {
        // If that fails, we don't have a GitHub profile linked
        setGithubProfile(null);
      }
    } catch (err) {
      console.error('Failed to fetch GitHub profile:', err);
      setGithubProfile(null);
    } finally {
      setIsLoadingGithub(false);
      setIsLoading(false);
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
        const data = await response.json();
        setSuccessMessage(`Successfully linked to GitHub username: ${githubUsername}`);
        setGithubUsername('');
        // Refresh GitHub profile data
        fetchGithubProfile();
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

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logo} alt="Poly-Agent Logo" className="dashboard-logo" />
          <h1>User Profile</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/profile" className="nav-link active">Profile</Link>
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
        <div className="profile-container">
          <h2>Your Profile</h2>
          
          {user && (
            <div className="profile-details">
              <div className="profile-section">
                <h3>Personal Information</h3>
                <div className="profile-field">
                  <span className="field-label">Name:</span>
                  <span className="field-value">{user.name || 'Not provided'}</span>
                </div>
                <div className="profile-field">
                  <span className="field-label">Username:</span>
                  <span className="field-value">{user.username}</span>
                </div>
                <div className="profile-field">
                  <span className="field-label">Email:</span>
                  <span className="field-value">{user.email}</span>
                </div>
              </div>
              
              <div className="profile-section">
                <h3>GitHub Integration</h3>
                {isLoadingGithub ? (
                  <div className="loading-indicator">
                    <div className="spinner small"></div>
                    <p>Loading GitHub profile...</p>
                  </div>
                ) : githubProfile && githubProfile.status === "success" ? (
                  <>
                    <div className="profile-field">
                      <span className="field-label">GitHub Username:</span>
                      <span className="field-value">{githubProfile.github_username}</span>
                    </div>
                    <div className="profile-field">
                      <span className="field-label">Repositories:</span>
                      <span className="field-value">{githubProfile.repositories_count || 0}</span>
                    </div>
                    <div className="profile-field">
                      <span className="field-label">Last Synced:</span>
                      <span className="field-value">
                        {new Date(githubProfile.last_synced).toLocaleString()}
                      </span>
                    </div>
                    <button 
                      className="profile-btn" 
                      onClick={fetchGithubProfile}
                      disabled={isLinking}
                    >
                      Refresh GitHub Data
                    </button>
                  </>
                ) : (
                  <>
                    <p className="github-status-message">
                      You don't have a GitHub account linked. Link your account to track your code contributions.
                    </p>
                    <form onSubmit={handleLinkGitHub} className="github-link-form">
                      <input
                        type="text"
                        placeholder="Enter your GitHub username"
                        value={githubUsername}
                        onChange={(e) => setGithubUsername(e.target.value)}
                        disabled={isLinking}
                        required
                      />
                      <button 
                        type="submit"
                        className="profile-btn"
                        disabled={isLinking}
                      >
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
                              // Refresh GitHub profile data
                              fetchGithubProfile();
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
                  </>
                )}
              </div>
              
              <div className="profile-section">
                <h3>Account Settings</h3>
                <button className="profile-btn">Change Password</button>
                <button className="profile-btn">Update Profile</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ProfilePage; 