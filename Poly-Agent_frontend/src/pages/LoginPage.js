import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import '../styles/AuthPages.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const LoginPage = () => {
  const [userInput, setUserInput] = useState(''); // Can be either username or email
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Check for success message from registration
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the message from state after displaying it
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!userInput.trim() || !password.trim()) {
      setError('Please enter all fields');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    
    try {
      // Determine if input is email or username
      const isEmail = userInput.includes('@');
      
      // Prepare login data
      const loginData = {
        password: password
      };
      
      // Add either email or username based on input
      if (isEmail) {
        loginData.email = userInput;
      } else {
        loginData.username = userInput;
      }
      
      // Send login request
      const loginResponse = await fetch('/api/users/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'include',
        body: JSON.stringify(loginData)
      });

      if (loginResponse.ok) {
        const data = await loginResponse.json();
        // Store user data in localStorage or context if needed
        localStorage.setItem('user', JSON.stringify(data));
        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        const errorData = await loginResponse.json();
        throw new Error(errorData.error || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-logo-container">
          <img src={logo} alt="Poly-Agent Logo" className="auth-logo" />
        </div>
        
        <h1 className="auth-title">Login to Poly-Agent</h1>
        <p className="auth-subtitle">Access your health checks and GitHub analytics</p>
        
        {successMessage && <div className="auth-success">{successMessage}</div>}
        {error && <div className="auth-error">{error}</div>}
        
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="userInput">Username or Email</label>
            <div className="input-with-icon">
              <i className="fas fa-user input-icon"></i>
              <input
                type="text"
                id="userInput"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Enter your username or email"
                required
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-with-icon">
              <i className="fas fa-lock input-icon"></i>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
          </div>
          
          <button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              'Login'
            )}
          </button>
        </form>
        
        <div className="auth-links">
          <Link to="/forgot-password" className="auth-link">Forgot Password?</Link>
          <div className="auth-separator" />
          <p>Don't have an account?</p>
          <Link to="/register" className="auth-link primary">Create Account</Link>
        </div>
        
        <div className="auth-home-link">
          <Link to="/" className="back-to-home">
            <i className="fas fa-arrow-left"></i> Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 