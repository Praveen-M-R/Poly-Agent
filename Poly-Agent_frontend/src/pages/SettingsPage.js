import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';
import '../styles/Settings.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const SettingsPage = () => {
  const [user, setUser] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    notification_email: '',
    notification_slack: ''
  });
  const [password, setPassword] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserSettings = async () => {
      try {
        const response = await fetch('/api/users/settings/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user settings');
        }

        const data = await response.json();
        setUser(data);
      } catch (err) {
        console.error('Error fetching user settings:', err);
        setError(err.message || 'An error occurred while fetching user settings');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserSettings();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setUser({
      ...user,
      [name]: value
    });
    
    // Clear success message when user makes changes
    setSuccessMessage('');
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPassword({
      ...password,
      [name]: value
    });
    
    // Clear password error when user makes changes
    setPasswordError('');
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/users/settings/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(user)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update user settings');
      }
      
      setSuccessMessage('Your profile has been updated successfully!');
      
      // Update the user data just to be sure it's in sync
      const updatedData = await response.json();
      setUser(updatedData);
    } catch (err) {
      console.error('Error updating user settings:', err);
      setError(err.message || 'An error occurred while updating user settings');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    // Validate passwords match
    if (password.new_password !== password.confirm_password) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    try {
      const response = await fetch('/api/users/change-password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          old_password: password.current_password,
          new_password: password.new_password
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }
      
      // Reset password fields
      setPassword({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      
      setSuccessMessage('Your password has been changed successfully!');
    } catch (err) {
      console.error('Error changing password:', err);
      setPasswordError(err.message || 'An error occurred while changing your password');
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
        <p>Loading user settings...</p>
      </div>
    );
  }

  if (error && !user.username) {
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
          <h1>Settings</h1>
        </div>
        <div className="header-right">
          <nav className="dashboard-nav">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/health-checks" className="nav-link">Health Checks</Link>
            <Link to="/reports" className="nav-link">Reports</Link>
            <Link to="/profile" className="nav-link">Profile</Link>
          </nav>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="settings-container">
          {successMessage && (
            <div className="success-message">
              {successMessage}
            </div>
          )}
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="settings-grid">
            <div className="settings-card profile-settings">
              <h2>Profile Settings</h2>
              <form onSubmit={handleUpdateProfile}>
                <div className="form-group">
                  <label htmlFor="username">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={user.username}
                    onChange={handleInputChange}
                    disabled
                  />
                  <small>Username cannot be changed</small>
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={user.email || ''}
                    onChange={handleInputChange}
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="first_name">First Name</label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={user.first_name || ''}
                      onChange={handleInputChange}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="last_name">Last Name</label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={user.last_name || ''}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <button type="submit" className="btn btn-primary">
                  Update Profile
                </button>
              </form>
            </div>
            
            <div className="settings-card notification-settings">
              <h2>Notification Settings</h2>
              <form>
                <div className="form-group">
                  <label htmlFor="notification_email">Email Notifications</label>
                  <input
                    type="email"
                    id="notification_email"
                    name="notification_email"
                    value={user.notification_email || ''}
                    onChange={handleInputChange}
                    placeholder="Email for notifications"
                  />
                  <small>Where to send health check notifications</small>
                </div>
                
                <div className="form-group">
                  <label htmlFor="notification_slack">Slack Webhook URL</label>
                  <input
                    type="url"
                    id="notification_slack"
                    name="notification_slack"
                    value={user.notification_slack || ''}
                    onChange={handleInputChange}
                    placeholder="https://hooks.slack.com/services/..."
                  />
                  <small>Webhook URL to post notifications to Slack</small>
                </div>
                
                <button type="button" onClick={handleUpdateProfile} className="btn btn-primary">
                  Save Notification Settings
                </button>
              </form>
            </div>
            
            <div className="settings-card password-settings">
              <h2>Change Password</h2>
              {passwordError && (
                <div className="error-message">
                  {passwordError}
                </div>
              )}
              <form onSubmit={handleChangePassword}>
                <div className="form-group">
                  <label htmlFor="current_password">Current Password</label>
                  <input
                    type="password"
                    id="current_password"
                    name="current_password"
                    value={password.current_password}
                    onChange={handlePasswordChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="new_password">New Password</label>
                  <input
                    type="password"
                    id="new_password"
                    name="new_password"
                    value={password.new_password}
                    onChange={handlePasswordChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="confirm_password">Confirm New Password</label>
                  <input
                    type="password"
                    id="confirm_password"
                    name="confirm_password"
                    value={password.confirm_password}
                    onChange={handlePasswordChange}
                    required
                  />
                </div>
                
                <button type="submit" className="btn btn-primary">
                  Change Password
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SettingsPage; 