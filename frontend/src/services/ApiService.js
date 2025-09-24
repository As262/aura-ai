// API service for AuraAI backend integration
class ApiService {
  static baseURL = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api`;

  // Helper method for making HTTP requests
  static async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      return { success: true, data };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return { 
        success: false, 
        error: error.message,
        code: 'API_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  // Health check
  static async healthCheck() {
    return await this.makeRequest('/health/');
  }

  // User authentication
  static async registerUser(userData) {
    return await this.makeRequest('/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  static async loginUser(credentials) {
    return await this.makeRequest('/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  // User profile
  static async getUserProfile() {
    return await this.makeRequest('/profile/');
  }

  static async updateUserProfile(profileData) {
    return await this.makeRequest('/profile/', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  // Aesthetic Analysis
  static async analyzeAesthetic(file, caption = '', platform = 'instagram') {
    try {
      // Validate file
      this.validateFile(file, ['image/jpeg', 'image/png', 'image/webp', 'image/gif']);

      const formData = new FormData();
      formData.append('image', file);
      
      // Add metadata as JSON string if needed
      const metadata = { caption, platform };
      formData.append('metadata', JSON.stringify(metadata));

      const result = await this.makeRequest('/aesthetic-analysis/', {
        method: 'POST',
        body: formData,
      });

      // If successful, enhance the result with frontend-specific data
      if (result.success) {
        result.data = {
          ...result.data,
          platform,
          caption,
          // Add client-side enhancements
          hashtagSuggestions: this.generateHashtags(platform),
          visualStyle: this.determineVisualStyle(platform),
          postingPattern: this.getPostingPattern(platform),
          audienceMatch: this.getAudienceMatch(),
          contentCategories: this.getContentCategories(),
          moodBoard: this.getMoodBoard(),
        };
      }

      return result;
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        code: 'AESTHETIC_ANALYSIS_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  // Conversation Analysis
  static async analyzeConversation(file) {
    try {
      // Validate file for conversation analysis
      this.validateFile(file, [
        'text/plain', 
        'application/json', 
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ]);

      // For text files, read content and send as text
      if (file.type === 'text/plain' || file.type === 'application/json') {
        const text = await this.readFileAsText(file);
        return await this.makeRequest('/conversation-analysis/', {
          method: 'POST',
          body: JSON.stringify({ conversation_text: text }),
        });
      }

      // For other files, send as form data
      const formData = new FormData();
      formData.append('file', file);

      return await this.makeRequest('/conversation-analysis/', {
        method: 'POST',
        body: formData,
      });
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        code: 'CONVERSATION_ANALYSIS_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  // Helper methods
  static validateFile(file, allowedTypes, maxSize = 10 * 1024 * 1024) {
    if (!file) {
      throw new Error('No file provided');
    }

    if (!allowedTypes.includes(file.type)) {
      throw new Error(`Unsupported file type. Please upload: ${allowedTypes.join(', ')}`);
    }

    if (file.size > maxSize) {
      const maxSizeMB = Math.round(maxSize / (1024 * 1024));
      throw new Error(`File too large. Maximum size allowed: ${maxSizeMB}MB`);
    }

    if (file.size < 100) { // Less than 100 bytes
      throw new Error('File appears to be corrupted or empty');
    }
  }

  static readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  // Client-side enhancement methods (fallback for enhanced UX)
  static generateHashtags(platform = 'instagram') {
    const platformHashtags = {
      instagram: ['#aesthetic', '#vibes', '#mood', '#inspiration', '#lifestyle'],
      tiktok: ['#fyp', '#foryou', '#viral', '#trending', '#tiktok'],
      twitter: ['#Breaking', '#News', '#Update', '#Thread', '#Opinion'],
      youtube: ['#Tutorial', '#HowTo', '#Guide', '#Tips', '#Learn'],
      linkedin: ['#Professional', '#Career', '#Leadership', '#Business', '#Success']
    };
    
    return platformHashtags[platform] || platformHashtags.instagram;
  }

  static determineVisualStyle(platform = 'instagram') {
    const platformStyles = {
      instagram: 'Minimalist Modern',
      tiktok: 'Dynamic & Energetic',
      youtube: 'Professional & Polished',
      twitter: 'Clean & Professional',
      linkedin: 'Corporate & Professional'
    };
    
    return platformStyles[platform] || platformStyles.instagram;
  }

  static getPostingPattern(platform = 'instagram') {
    const patterns = {
      instagram: 'Consistent Daily Poster',
      tiktok: 'Multiple Daily Posts',
      youtube: 'Weekly Uploader',
      twitter: 'Real-time Responder',
      linkedin: 'Weekly Thought Leader'
    };
    
    return patterns[platform] || patterns.instagram;
  }

  static getAudienceMatch() {
    const matches = [
      'Gen-Z Creatives',
      'Millennial Professionals',
      'Art Enthusiasts',
      'Lifestyle Influencers'
    ];
    return matches[Math.floor(Math.random() * matches.length)];
  }

  static getContentCategories() {
    const categories = [
      ['Lifestyle', 'Fashion', 'Travel'],
      ['Art', 'Photography', 'Design'],
      ['Food', 'Culture', 'Adventure'],
      ['Tech', 'Innovation', 'Creativity']
    ];
    return categories[Math.floor(Math.random() * categories.length)];
  }

  static getMoodBoard() {
    const moods = [
      ['Ethereal', 'Dreamy', 'Soft'],
      ['Bold', 'Confident', 'Striking'],
      ['Minimal', 'Clean', 'Sophisticated'],
      ['Warm', 'Cozy', 'Inviting']
    ];
    return moods[Math.floor(Math.random() * moods.length)];
  }

  // Connection testing
  static async testConnection() {
    try {
      const health = await this.healthCheck();
      if (health.success) {
        console.log('✅ Backend connection successful');
        return true;
      } else {
        console.error('❌ Backend health check failed:', health.error);
        return false;
      }
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      return false;
    }
  }
}

export default ApiService;