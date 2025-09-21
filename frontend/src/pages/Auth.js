import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const Auth = () => {
  const location = useLocation();
  const [isLogin, setIsLogin] = useState(location.pathname === '/login');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const { login, signup, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleModeSwitch = (loginMode) => {
    setIsLogin(loginMode);
    setError('');
    setFormData({
      name: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
    
    // Update URL without page reload
    window.history.pushState(null, '', loginMode ? '/login' : '/signup');
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (isLogin) {
      // Login validation
      if (!formData.email || !formData.password) {
        setError('Please fill in all fields');
        return;
      }

      const result = await login(formData.email, formData.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error);
      }
    } else {
      // Signup validation
      if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
        setError('Please fill in all fields');
        return;
      }

      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      if (formData.password.length < 6) {
        setError('Password must be at least 6 characters long');
        return;
      }

      const result = await signup(formData.name, formData.email, formData.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error);
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card animated">
        <div className="auth-header">
          <h2 className={`auth-title ${isLogin ? 'login-mode' : 'signup-mode'}`}>
            {isLogin ? 'Welcome Back' : 'Join AuraAI'}
          </h2>
          <p className="auth-subtitle">
            {isLogin ? 'Sign in to your AuraAI account' : 'Create your AuraAI account'}
          </p>
        </div>

        {/* Mode Toggle Buttons */}
        <div className="auth-toggle">
          <button
            type="button"
            className={`toggle-btn ${isLogin ? 'active' : ''}`}
            onClick={() => handleModeSwitch(true)}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`toggle-btn ${!isLogin ? 'active' : ''}`}
            onClick={() => handleModeSwitch(false)}
          >
            Sign Up
          </button>
          <div className={`toggle-indicator ${isLogin ? 'login-position' : 'signup-position'}`}></div>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          
          {/* Animated form fields container */}
          <div className={`form-fields ${isLogin ? 'login-fields' : 'signup-fields'}`}>
            {/* Name field - only visible in signup mode */}
            <div className={`form-group name-field ${isLogin ? 'hidden' : 'visible'}`}>
              <label htmlFor="name">Full Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                autoComplete="name"
              />
            </div>

            {/* Email field */}
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter your email"
                autoComplete="email"
                required
              />
            </div>

            {/* Password field */}
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                autoComplete={isLogin ? "current-password" : "new-password"}
                required
              />
            </div>

            {/* Confirm Password field - only visible in signup mode */}
            <div className={`form-group confirm-password-field ${isLogin ? 'hidden' : 'visible'}`}>
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm your password"
                autoComplete="new-password"
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary btn-full auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading-spinner">
                <span className="spinner"></span>
                {isLogin ? 'Signing in...' : 'Creating account...'}
              </span>
            ) : (
              <>
                <span className="btn-icon">{isLogin ? '🔑' : '✨'}</span>
                {isLogin ? 'Sign In' : 'Create Account'}
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              type="button"
              className="auth-link-btn"
              onClick={() => handleModeSwitch(!isLogin)}
            >
              {isLogin ? 'Sign up here' : 'Sign in here'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Auth;