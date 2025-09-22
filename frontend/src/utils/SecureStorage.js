// Secure storage utility for sensitive data
class SecureStorage {
  // Use sessionStorage for temporary sensitive data
  // Use localStorage only for non-sensitive preferences
  
  static SESSION_KEY_PREFIX = 'aura_session_';
  static LOCAL_KEY_PREFIX = 'aura_pref_';
  static CRYPTO_KEY = 'aura_ai_secret_key'; // In production, this should come from environment

  /**
   * Encrypts data before storing (basic XOR encryption for demo)
   * In production, use proper encryption libraries like crypto-js
   */
  static encrypt(data) {
    try {
      const jsonString = JSON.stringify(data);
      let encrypted = '';
      
      for (let i = 0; i < jsonString.length; i++) {
        const charCode = jsonString.charCodeAt(i);
        const keyChar = this.CRYPTO_KEY.charCodeAt(i % this.CRYPTO_KEY.length);
        encrypted += String.fromCharCode(charCode ^ keyChar);
      }
      
      return btoa(encrypted); // Base64 encode
    } catch (error) {
      console.error('Encryption failed:', error);
      return null;
    }
  }

  /**
   * Decrypts stored data
   */
  static decrypt(encryptedData) {
    try {
      const encrypted = atob(encryptedData); // Base64 decode
      let decrypted = '';
      
      for (let i = 0; i < encrypted.length; i++) {
        const charCode = encrypted.charCodeAt(i);
        const keyChar = this.CRYPTO_KEY.charCodeAt(i % this.CRYPTO_KEY.length);
        decrypted += String.fromCharCode(charCode ^ keyChar);
      }
      
      return JSON.parse(decrypted);
    } catch (error) {
      console.error('Decryption failed:', error);
      return null;
    }
  }

  /**
   * Store sensitive session data (automatically expires)
   */
  static setSessionData(key, data, expirationMinutes = 60) {
    try {
      const expirationTime = Date.now() + (expirationMinutes * 60 * 1000);
      const wrappedData = {
        data: data,
        expiration: expirationTime,
        timestamp: Date.now()
      };
      
      const encrypted = this.encrypt(wrappedData);
      if (encrypted) {
        sessionStorage.setItem(this.SESSION_KEY_PREFIX + key, encrypted);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to store session data:', error);
      return false;
    }
  }

  /**
   * Retrieve sensitive session data
   */
  static getSessionData(key) {
    try {
      const encrypted = sessionStorage.getItem(this.SESSION_KEY_PREFIX + key);
      if (!encrypted) return null;

      const wrappedData = this.decrypt(encrypted);
      if (!wrappedData) return null;

      // Check if data has expired
      if (Date.now() > wrappedData.expiration) {
        this.removeSessionData(key);
        return null;
      }

      return wrappedData.data;
    } catch (error) {
      console.error('Failed to retrieve session data:', error);
      return null;
    }
  }

  /**
   * Remove session data
   */
  static removeSessionData(key) {
    try {
      sessionStorage.removeItem(this.SESSION_KEY_PREFIX + key);
      return true;
    } catch (error) {
      console.error('Failed to remove session data:', error);
      return false;
    }
  }

  /**
   * Store non-sensitive preferences
   */
  static setPreference(key, value) {
    try {
      localStorage.setItem(this.LOCAL_KEY_PREFIX + key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Failed to store preference:', error);
      return false;
    }
  }

  /**
   * Retrieve non-sensitive preferences
   */
  static getPreference(key, defaultValue = null) {
    try {
      const value = localStorage.getItem(this.LOCAL_KEY_PREFIX + key);
      return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
      console.error('Failed to retrieve preference:', error);
      return defaultValue;
    }
  }

  /**
   * Clear all session data (logout)
   */
  static clearAllSessionData() {
    try {
      const keys = Object.keys(sessionStorage);
      keys.forEach(key => {
        if (key.startsWith(this.SESSION_KEY_PREFIX)) {
          sessionStorage.removeItem(key);
        }
      });
      return true;
    } catch (error) {
      console.error('Failed to clear session data:', error);
      return false;
    }
  }

  /**
   * Validate session integrity
   */
  static validateSession() {
    const user = this.getSessionData('user');
    const token = this.getSessionData('auth_token');
    
    if (!user || !token) {
      this.clearAllSessionData();
      return false;
    }

    // Additional validation logic can be added here
    return true;
  }
}

export default SecureStorage;