import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import AccessibilityUtils from '../utils/AccessibilityUtils';
import './Header.css';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const mobileMenuRef = useRef(null);
  const userMenuRef = useRef(null);
  const mobileMenuButtonRef = useRef(null);
  const userMenuButtonRef = useRef(null);

  // Handle mobile menu toggle
  const toggleMobileMenu = () => {
    setIsMenuOpen(!isMenuOpen);
    if (!isMenuOpen) {
      AccessibilityUtils.announceToScreenReader('Navigation menu opened');
    } else {
      AccessibilityUtils.announceToScreenReader('Navigation menu closed');
    }
  };

  // Handle user menu toggle
  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
    if (!isUserMenuOpen) {
      AccessibilityUtils.announceToScreenReader('User menu opened');
    } else {
      AccessibilityUtils.announceToScreenReader('User menu closed');
    }
  };

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target) &&
          !mobileMenuButtonRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target) &&
          userMenuButtonRef.current && !userMenuButtonRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscapeKey);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, []);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      // If user is logged in, navigate to features
      if (location.pathname === '/') {
        const featuresSection = document.getElementById('features');
        if (featuresSection) {
          featuresSection.scrollIntoView({ behavior: 'smooth' });
          AccessibilityUtils.manageFocus(featuresSection);
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
    AccessibilityUtils.announceToScreenReader('Successfully logged out');
  };

  return (
    <header className="header" role="banner">
      <div className="header-container">
        <Link 
          to="/" 
          className="logo"
          aria-label="AuraAI - Go to homepage"
        >
          <span className="logo-text">AuraAI</span>
        </Link>
        
        {/* Mobile menu button */}
        <button
          ref={mobileMenuButtonRef}
          className="mobile-menu-button"
          onClick={toggleMobileMenu}
          aria-expanded={isMenuOpen}
          aria-controls="main-navigation"
          aria-label="Toggle navigation menu"
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>
        
        <nav 
          ref={mobileMenuRef}
          className={`nav ${isMenuOpen ? 'nav--open' : ''}`}
          id="main-navigation"
          role="navigation"
          aria-label="Main navigation"
        >
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'nav-link--active' : ''}`}
            aria-current={location.pathname === '/' ? 'page' : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            Home
          </Link>
          <Link 
            to="/aesthetic-analyzer" 
            className={`nav-link ${location.pathname === '/aesthetic-analyzer' ? 'nav-link--active' : ''}`}
            aria-current={location.pathname === '/aesthetic-analyzer' ? 'page' : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            Aesthetic Analyzer
          </Link>
          <Link 
            to="/convo-decoder" 
            className={`nav-link ${location.pathname === '/convo-decoder' ? 'nav-link--active' : ''}`}
            aria-current={location.pathname === '/convo-decoder' ? 'page' : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            Convo Decoder
          </Link>
        </nav>
        
        <div className="header-actions">
          <ThemeToggle />
          {isAuthenticated ? (
            <div className="user-menu-container">
              <button
                ref={userMenuButtonRef}
                className="user-menu-trigger"
                onClick={toggleUserMenu}
                aria-expanded={isUserMenuOpen}
                aria-controls="user-menu"
                aria-label={`User menu for ${user?.name || 'user'}`}
              >
                <img 
                  src={user?.avatar} 
                  alt="" 
                  className="user-avatar"
                  role="presentation"
                />
                <span className="user-name" aria-hidden="true">{user?.name}</span>
                <svg 
                  className={`user-menu-arrow ${isUserMenuOpen ? 'user-menu-arrow--open' : ''}`}
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none"
                  aria-hidden="true"
                >
                  <path d="m6 9 6 6 6-6" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </button>
              
              <div 
                ref={userMenuRef}
                className={`user-menu ${isUserMenuOpen ? 'user-menu--open' : ''}`}
                id="user-menu"
                role="menu"
                aria-labelledby="user-menu-trigger"
              >
                <div className="user-info" role="menuitem" tabIndex="-1">
                  <div className="user-details">
                    <strong>{user?.name}</strong>
                    <span className="user-email">{user?.email}</span>
                  </div>
                </div>
                <hr className="user-menu-divider" role="separator" />
                <button 
                  className="user-menu-item" 
                  role="menuitem"
                  onClick={handleLogout}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="2"/>
                    <polyline points="16,17 21,12 16,7" stroke="currentColor" strokeWidth="2"/>
                    <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <button 
              className="btn btn-primary btn-get-started" 
              onClick={handleGetStarted}
              aria-label="Get started with AuraAI"
            >
              Get Started
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;