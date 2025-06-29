import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { TransitionGroup, CSSTransition } from 'react-transition-group';
import './styles/App.css';
import WelcomePage from './pages/WelcomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import HealthChecksPage from './pages/HealthChecksPage';
import ProfilePage from './pages/ProfilePage';
import CreateHealthCheckPage from './pages/CreateHealthCheckPage';
import CheckDetailPage from './pages/CheckDetailPage';
import CheckLogsPage from './pages/CheckLogsPage';
import EditHealthCheckPage from './pages/EditHealthCheckPage';
import ReportsPage from './pages/ReportsPage';
import FailedChecksPage from './pages/FailedChecksPage';
import SettingsPage from './pages/SettingsPage';
import CodeTrackPage from './pages/CodeTrackPage';

// Wrapper component to handle transitions
const AnimatedRoutes = () => {
  const location = useLocation();
  
  return (
    <TransitionGroup>
      <CSSTransition
        key={location.key}
        classNames="page-transition"
        timeout={300}
      >
        <div className="route-container">
          <Routes location={location}>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/health-checks" element={<HealthChecksPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/health-checks/create" element={<CreateHealthCheckPage />} />
            <Route path="/check/:checkId" element={<CheckDetailPage />} />
            <Route path="/check-logs/:checkId" element={<CheckLogsPage />} />
            <Route path="/check/:checkId/edit" element={<EditHealthCheckPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/failed-checks" element={<FailedChecksPage />} />
            <Route path="/codetrack" element={<CodeTrackPage />} />
            <Route path="*" element={<div className="not-found">404 - Page Not Found</div>} />
          </Routes>
        </div>
      </CSSTransition>
    </TransitionGroup>
  );
};

function App() {
  return (
    <Router>
      <div className="app">
        <AnimatedRoutes />
      </div>
    </Router>
  );
}

export default App; 