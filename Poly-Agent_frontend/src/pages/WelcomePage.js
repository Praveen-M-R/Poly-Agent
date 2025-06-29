import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/WelcomePage.css';
import logo from '../assets/Poly-Agent_logo.jpeg';

const WelcomePage = () => {
  return (
    <div className="welcome-page">
      <div className="welcome-hero">
        <div className="welcome-container">
          <div className="welcome-logo-container">
            <img src={logo} alt="Poly-Agent Logo" className="welcome-logo" />
          </div>
          <h1 className="welcome-title">Welcome to Poly Agent</h1>
          <p className="welcome-tagline">Monitor. Analyze. Visualize.</p>
          <div className="welcome-description">
            <p>
              Poly Agent is an intelligent internal tool built to streamline software development, 
              project visibility, and operational awareness. Designed for engineering teams, 
              it brings together health monitoring, code analysis, and automated project visualization.
            </p>
          </div>
          
          <div className="welcome-buttons">
            <Link to="/login" className="welcome-button primary">
              <i className="fas fa-sign-in-alt"></i> Login
            </Link>
            <Link to="/register" className="welcome-button secondary">
              <i className="fas fa-user-plus"></i> Register
            </Link>
          </div>
        </div>
      </div>
      
      <div className="welcome-features">
        <div className="welcome-container">
          <h2 className="welcome-section-title">Key Features</h2>
          
          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-heartbeat"></i>
              </div>
              <h3 className="feature-title">Health Monitoring</h3>
              <p className="feature-description">
                Track the health of your websites in real time with customizable checks and alerts
              </p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-code-branch"></i>
              </div>
              <h3 className="feature-title">GitHub Analytics</h3>
              <p className="feature-description">
                Analyze repository activity and developer contributions across your organization
              </p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-chart-line"></i>
              </div>
              <h3 className="feature-title">Performance Tracking</h3>
              <p className="feature-description">
                Monitor response times and generate detailed uptime reports
              </p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-bell"></i>
              </div>
              <h3 className="feature-title">Alert System</h3>
              <p className="feature-description">
                Receive immediate notifications when your services experience issues
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage; 