import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import './Header.css';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      // If user is logged in, navigate to features
      if (location.pathname === '/') {
        const featuresSection = document.getElementById('features');
        if (featuresSection) {
          featuresSection.scrollIntoView({ behavior: 'smooth' });
        }
      } else {
        navigate('/');
      }
    } else {
      // If user is not logged in, navigate to login
      navigate('/login');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <span className="logo-text">AuraAI</span>
        </Link>
        
        <nav className="nav">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/aesthetic-analyzer" className="nav-link">Aesthetic Analyzer</Link>
          <Link to="/convo-decoder" className="nav-link">Convo Decoder</Link>
        </nav>
        
        <div className="header-actions">
          <ThemeToggle />
          {isAuthenticated ? (
            <div className="user-menu">
              <div className="user-info">
                <img 
                  src={user.avatar} 
                  alt={user.name} 
                  className="user-avatar"
                />
                <span className="user-name">{user.name}</span>
              </div>
              <button 
                className="btn btn-secondary btn-logout" 
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          ) : (
            <button 
              className="btn btn-primary btn-get-started" 
              onClick={handleGetStarted}
            >
              <span className="btn-icon">🚀</span>
              Get Started
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;