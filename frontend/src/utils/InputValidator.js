// Input validation utilities for forms and user input
class InputValidator {
  
  // Email validation with comprehensive regex
  static EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  
  // Password strength requirements
  static PASSWORD_REQUIREMENTS = {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: false // Optional for better UX
  };

  // Common weak passwords to block
  static WEAK_PASSWORDS = [
    'password', '123456', '123456789', 'qwerty', 'abc123',
    'password123', 'admin', 'letmein', 'welcome', 'monkey',
    '1234567890', 'password1', 'qwerty123', 'admin123'
  ];

  /**
   * Validates email address
   */
  static validateEmail(email) {
    const result = { isValid: true, errors: [], suggestions: [] };
    
    if (!email) {
      result.isValid = false;
      result.errors.push('Email is required');
      return result;
    }

    // Trim and normalize
    email = email.trim().toLowerCase();

    // Length check
    if (email.length > 254) {
      result.isValid = false;
      result.errors.push('Email address is too long');
    }

    // Format validation
    if (!this.EMAIL_REGEX.test(email)) {
      result.isValid = false;
      result.errors.push('Please enter a valid email address');
    }

    // Check for common typos and suggest corrections
    const suggestions = this.getEmailSuggestions(email);
    if (suggestions.length > 0) {
      result.suggestions = suggestions;
    }

    // Disposable email check (basic)
    if (this.isDisposableEmail(email)) {
      result.errors.push('Disposable email addresses are not allowed');
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validates password strength
   */
  static validatePassword(password) {
    const result = { 
      isValid: true, 
      errors: [], 
      warnings: [],
      strength: 'weak',
      score: 0
    };

    if (!password) {
      result.isValid = false;
      result.errors.push('Password is required');
      return result;
    }

    const req = this.PASSWORD_REQUIREMENTS;
    let score = 0;

    // Length validation
    if (password.length < req.minLength) {
      result.isValid = false;
      result.errors.push(`Password must be at least ${req.minLength} characters long`);
    } else {
      score += Math.min(password.length * 2, 20); // Max 20 points for length
    }

    if (password.length > req.maxLength) {
      result.isValid = false;
      result.errors.push(`Password must not exceed ${req.maxLength} characters`);
    }

    // Character requirements
    if (req.requireUppercase && !/[A-Z]/.test(password)) {
      result.isValid = false;
      result.errors.push('Password must contain at least one uppercase letter');
    } else if (/[A-Z]/.test(password)) {
      score += 10;
    }

    if (req.requireLowercase && !/[a-z]/.test(password)) {
      result.isValid = false;
      result.errors.push('Password must contain at least one lowercase letter');
    } else if (/[a-z]/.test(password)) {
      score += 10;
    }

    if (req.requireNumbers && !/\d/.test(password)) {
      result.isValid = false;
      result.errors.push('Password must contain at least one number');
    } else if (/\d/.test(password)) {
      score += 10;
    }

    if (req.requireSpecialChars && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      result.isValid = false;
      result.errors.push('Password must contain at least one special character');
    } else if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      score += 15;
    }

    // Check for weak passwords
    if (this.WEAK_PASSWORDS.includes(password.toLowerCase())) {
      result.isValid = false;
      result.errors.push('This password is too common. Please choose a more secure password');
    }

    // Check for repeated characters
    if (/(.)\1{2,}/.test(password)) {
      result.warnings.push('Avoid using repeated characters');
      score -= 5;
    }

    // Check for sequential characters
    if (this.hasSequentialChars(password)) {
      result.warnings.push('Avoid using sequential characters (e.g., 123, abc)');
      score -= 5;
    }

    // Calculate strength
    result.score = Math.max(0, Math.min(100, score));
    
    if (result.score >= 80) result.strength = 'very-strong';
    else if (result.score >= 60) result.strength = 'strong';
    else if (result.score >= 40) result.strength = 'medium';
    else if (result.score >= 20) result.strength = 'weak';
    else result.strength = 'very-weak';

    return result;
  }

  /**
   * Validates name input
   */
  static validateName(name) {
    const result = { isValid: true, errors: [] };

    if (!name) {
      result.isValid = false;
      result.errors.push('Name is required');
      return result;
    }

    // Trim and validate
    name = name.trim();

    if (name.length < 2) {
      result.isValid = false;
      result.errors.push('Name must be at least 2 characters long');
    }

    if (name.length > 50) {
      result.isValid = false;
      result.errors.push('Name must not exceed 50 characters');
    }

    // Allow only letters, spaces, hyphens, and apostrophes
    if (!/^[a-zA-Z\s\-']+$/.test(name)) {
      result.isValid = false;
      result.errors.push('Name can only contain letters, spaces, hyphens, and apostrophes');
    }

    // Check for suspicious patterns
    if (/^\s+|\s+$/.test(name)) {
      result.isValid = false;
      result.errors.push('Name cannot start or end with spaces');
    }

    if (/\s{2,}/.test(name)) {
      result.isValid = false;
      result.errors.push('Name cannot contain multiple consecutive spaces');
    }

    return result;
  }

  /**
   * Sanitizes text input to prevent XSS
   */
  static sanitizeText(text) {
    if (!text) return '';
    
    return text
      .replace(/[<>]/g, '') // Remove angle brackets
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+=/gi, '') // Remove event handlers
      .trim();
  }

  /**
   * Validates and sanitizes caption/message input
   */
  static validateCaption(caption, maxLength = 2200) {
    const result = { isValid: true, errors: [], sanitized: '' };

    if (!caption) {
      result.sanitized = '';
      return result;
    }

    // Sanitize input
    const sanitized = this.sanitizeText(caption);
    result.sanitized = sanitized;

    // Length validation
    if (sanitized.length > maxLength) {
      result.isValid = false;
      result.errors.push(`Caption must not exceed ${maxLength} characters`);
    }

    // Check for spam patterns
    if (this.isSpamContent(sanitized)) {
      result.isValid = false;
      result.errors.push('Caption contains inappropriate content');
    }

    return result;
  }

  /**
   * Helper methods
   */
  static getEmailSuggestions(email) {
    const suggestions = [];
    const commonDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'];
    const parts = email.split('@');
    
    if (parts.length === 2) {
      const domain = parts[1];
      const closeMatches = commonDomains.filter(d => 
        this.levenshteinDistance(domain, d) === 1
      );
      
      suggestions.push(...closeMatches.map(d => `${parts[0]}@${d}`));
    }

    return suggestions;
  }

  static isDisposableEmail(email) {
    const disposableDomains = [
      '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
      'mailinator.com', 'throwaway.email'
    ];
    
    const domain = email.split('@')[1];
    return disposableDomains.includes(domain);
  }

  static hasSequentialChars(password) {
    const sequences = ['123', '234', '345', '456', '567', '678', '789', '890',
                      'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij'];
    
    const lowerPassword = password.toLowerCase();
    return sequences.some(seq => lowerPassword.includes(seq));
  }

  static isSpamContent(text) {
    const spamPatterns = [
      /\b(buy now|click here|free money|urgent|congratulations)\b/gi,
      /(.)\1{10,}/, // Repeated characters
      /[A-Z]{10,}/, // All caps
      /(http|www)\./gi // URLs (depending on context)
    ];

    return spamPatterns.some(pattern => pattern.test(text));
  }

  static levenshteinDistance(str1, str2) {
    const matrix = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Rate limiting check (client-side basic implementation)
   */
  static checkRateLimit(action, maxAttempts = 5, timeWindow = 15 * 60 * 1000) {
    const key = `rate_limit_${action}`;
    const now = Date.now();
    
    let attempts = JSON.parse(localStorage.getItem(key) || '[]');
    
    // Remove old attempts outside time window
    attempts = attempts.filter(timestamp => now - timestamp < timeWindow);
    
    if (attempts.length >= maxAttempts) {
      return {
        allowed: false,
        remainingTime: Math.ceil((attempts[0] + timeWindow - now) / 1000)
      };
    }

    // Add current attempt
    attempts.push(now);
    localStorage.setItem(key, JSON.stringify(attempts));

    return {
      allowed: true,
      attemptsLeft: maxAttempts - attempts.length
    };
  }
}

export default InputValidator;