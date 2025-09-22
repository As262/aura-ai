import React, { createContext, useContext, useState, useEffect } from 'react';
import SecureStorage from '../utils/SecureStorage';
import InputValidator from '../utils/InputValidator';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    // Check for saved user in secure session storage
    const savedUser = SecureStorage.getSessionData('user');
    if (savedUser && SecureStorage.validateSession()) {
      setUser(savedUser);
    } else {
      // Clear any invalid session data
      SecureStorage.clearAllSessionData();
    }
    setIsLoading(false);
  }, []);

  const login = async (email, password) => {
    setIsLoading(true);
    setAuthError(null);
    
    try {
      // Rate limiting check
      const rateLimit = InputValidator.checkRateLimit('login', 5, 15 * 60 * 1000);
      if (!rateLimit.allowed) {
        throw new Error(`Too many login attempts. Please try again in ${Math.ceil(rateLimit.remainingTime / 60)} minutes.`);
      }

      // Input validation
      const emailValidation = InputValidator.validateEmail(email);
      if (!emailValidation.isValid) {
        throw new Error(emailValidation.errors[0]);
      }

      if (!password || password.length < 6) {
        throw new Error('Password must be at least 6 characters long');
      }

      // Mock login API call with realistic delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
      
      // In a real app, this would validate against a backend
      // For demo purposes, we'll accept any valid email/password combination
      if (password.length < 6) {
        throw new Error('Invalid credentials');
      }

      // Generate secure user data
      const userData = {
        id: generateSecureId(),
        email: emailValidation.suggestions.length > 0 ? emailValidation.suggestions[0] : email.toLowerCase().trim(),
        name: extractNameFromEmail(email),
        avatar: generateAvatarUrl(email),
        loginTime: new Date().toISOString(),
        preferences: SecureStorage.getPreference('user_preferences', {})
      };

      // Generate mock auth token
      const authToken = generateAuthToken(userData);
      
      // Store user data and token securely
      SecureStorage.setSessionData('user', userData, 480); // 8 hours
      SecureStorage.setSessionData('auth_token', authToken, 480);
      
      setUser(userData);
      setIsLoading(false);
      return { success: true, user: userData };
      
    } catch (error) {
      setIsLoading(false);
      setAuthError(error.message);
      return { success: false, error: error.message };
    }
  };

  const signup = async (name, email, password) => {
    setIsLoading(true);
    setAuthError(null);
    
    try {
      // Rate limiting check
      const rateLimit = InputValidator.checkRateLimit('signup', 3, 60 * 60 * 1000);
      if (!rateLimit.allowed) {
        throw new Error(`Too many signup attempts. Please try again in ${Math.ceil(rateLimit.remainingTime / 60)} minutes.`);
      }

      // Input validation
      const nameValidation = InputValidator.validateName(name);
      if (!nameValidation.isValid) {
        throw new Error(nameValidation.errors[0]);
      }

      const emailValidation = InputValidator.validateEmail(email);
      if (!emailValidation.isValid) {
        throw new Error(emailValidation.errors[0]);
      }

      const passwordValidation = InputValidator.validatePassword(password);
      if (!passwordValidation.isValid) {
        throw new Error(passwordValidation.errors[0]);
      }

      // Check password strength
      if (passwordValidation.strength === 'very-weak' || passwordValidation.strength === 'weak') {
        throw new Error('Password is too weak. Please choose a stronger password.');
      }

      // Mock signup API call
      await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));
      
      // Generate secure user data
      const userData = {
        id: generateSecureId(),
        email: email.toLowerCase().trim(),
        name: name.trim(),
        avatar: generateAvatarUrl(email),
        signupTime: new Date().toISOString(),
        preferences: {}
      };

      // Generate mock auth token
      const authToken = generateAuthToken(userData);
      
      // Store user data and token securely
      SecureStorage.setSessionData('user', userData, 480); // 8 hours
      SecureStorage.setSessionData('auth_token', authToken, 480);
      
      setUser(userData);
      setIsLoading(false);
      return { success: true, user: userData };
      
    } catch (error) {
      setIsLoading(false);
      setAuthError(error.message);
      return { success: false, error: error.message };
    }
  };

  // Helper methods for secure authentication
  const generateSecureId = () => {
    // Generate a cryptographically secure ID
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  };

  const extractNameFromEmail = (email) => {
    const localPart = email.split('@')[0];
    // Convert email local part to readable name
    return localPart
      .replace(/[._-]/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const generateAvatarUrl = (email) => {
    const name = extractNameFromEmail(email);
    const colors = ['4ade80', '3b82f6', 'f59e0b', 'ef4444', '8b5cf6', 'ec4899'];
    const colorIndex = email.charCodeAt(0) % colors.length;
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${colors[colorIndex]}&color=fff&size=128`;
  };

  const generateAuthToken = (userData) => {
    // Generate a mock JWT-like token
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      sub: userData.id,
      email: userData.email,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (8 * 60 * 60) // 8 hours
    }));
    const signature = btoa(Math.random().toString(36).substring(2, 15));
    return `${header}.${payload}.${signature}`;
  };

  const logout = () => {
    // Clear all session data securely
    SecureStorage.clearAllSessionData();
    setUser(null);
    setAuthError(null);
  };

  // Clear auth error
  const clearError = () => {
    setAuthError(null);
  };

  // Update user preferences
  const updateUserPreferences = (preferences) => {
    if (user) {
      const updatedUser = { ...user, preferences };
      setUser(updatedUser);
      SecureStorage.setSessionData('user', updatedUser, 480);
      SecureStorage.setPreference('user_preferences', preferences);
    }
  };

  const value = {
    user,
    isLoading,
    authError,
    login,
    signup,
    logout,
    clearError,
    updateUserPreferences,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};