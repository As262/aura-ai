import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import { useUsage } from '../contexts/UsageContext';
import AccessibilityUtils from '../utils/AccessibilityUtils';
import './Header.css';

const Header = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const mobileMenuRef = useRef(null);
  const mobileMenuButtonRef = useRef(null);

  // Handle mobile menu toggle
  const toggleMobileMenu = () => {
    setIsMenuOpen(!isMenuOpen);
    if (!isMenuOpen) {
      AccessibilityUtils.announceToScreenReader('Navigation menu opened');
    } else {
      AccessibilityUtils.announceToScreenReader('Navigation menu closed');
    }
  };

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target) &&
          !mobileMenuButtonRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscapeKey);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, []);

  // (Get Started button removed) previously used to navigate to features

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
          <Link 
            to="/pricing" 
            className={`nav-link nav-link-pricing ${location.pathname === '/pricing' ? 'nav-link--active' : ''}`}
            aria-current={location.pathname === '/pricing' ? 'page' : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="pricing-icon">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
            </svg>
            Upgrade
          </Link>
        </nav>
        
        <div className="header-actions">
          <ThemeToggle />
          {/* Usage status */}
          <UsageBadge />
        </div>
      </div>
    </header>
  );
};

function UsageBadge() {
  const location = useLocation();
  const { getFeatureUsage } = useUsage() || {};
  
  if (!getFeatureUsage) return <div className="usage-badge">--/--</div>;

  // Determine which feature to show based on current route
  let feature = null;
  let featureName = '';
  
  if (location.pathname === '/aesthetic-analyzer') {
    feature = 'aesthetic_analyzer';
    featureName = 'Aesthetic Analyzer';
  } else if (location.pathname === '/convo-decoder') {
    feature = 'convo_decoder';
    featureName = 'Convo Decoder';
  }

  // If not on a feature page, don't show usage badge
  if (!feature) return null;

  const featureUsage = getFeatureUsage(feature);
  const used = featureUsage.count ?? 0;
  const limit = featureUsage.limit ?? 0;
  const remaining = featureUsage.remaining ?? 0;

  return (
    <div 
      className="usage-badge" 
      title={`${featureName}: ${remaining} uses left`} 
      aria-live="polite"
    >
      {used}/{limit} <span className="usage-sub">({remaining} left)</span>
    </div>
  );
}

export default Header;