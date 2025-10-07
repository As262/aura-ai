// API service for AuraAI backend integration
class ApiService {
  static baseURL = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api`;

  // Helper method for making HTTP requests
  static async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    console.log('🌐 Making request to:', url);
    console.log('🌐 Request options:', { ...options, body: options.body instanceof FormData ? '[FormData]' : options.body });
    
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
      console.log('🌐 FormData detected, removed Content-Type header');
    }

    try {
      console.log('🌐 Sending request...');
      const response = await fetch(url, config);
      console.log('🌐 Response status:', response.status);
      console.log('🌐 Response headers:', Object.fromEntries(response.headers.entries()));
      
      const data = await response.json();
      console.log('🌐 Response data:', data);

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

  // Aesthetic Analysis (Social Media focused)
  static async analyzeAesthetic(file, caption = '', platform = 'instagram') {
    try {
      console.log('🚀 ApiService.analyzeAesthetic called with:', { file, caption, platform });
      console.log('🚀 File details:', { name: file.name, size: file.size, type: file.type });
      
      // Validate file
      this.validateFile(file, ['image/jpeg', 'image/png', 'image/webp', 'image/gif']);
      console.log('✅ File validation passed');

      const formData = new FormData();
      formData.append('image', file);
      formData.append('analysis_type', platform);
      if (caption) {
        formData.append('caption', caption);
      }
      
      console.log('🚀 FormData created, making request to /social-media-analysis/');

      // Use social media specific endpoint
      const result = await this.makeRequest('/social-media-analysis/', {
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

  // Detailed AI Image Analysis (New comprehensive analysis)
  static async analyzeImageDetailed(file) {
    try {
      // Validate file
      this.validateFile(file, ['image/jpeg', 'image/png', 'image/webp'], 15 * 1024 * 1024); // 15MB limit

      const formData = new FormData();
      formData.append('image', file);

      const result = await this.makeRequest('/detailed-image-analysis/', {
        method: 'POST',
        body: formData,
      });

      // Add client-side processing if successful
      if (result.success && result.data.analysis) {
        const analysis = result.data.analysis;
        
        // Add interpretations and recommendations
        result.data.interpretations = {
          rating_interpretation: this.interpretRating(analysis.overall_rating?.score || 0),
          technical_summary: this.summarizeTechnical(analysis.technical_quality),
          pose_feedback: this.interpretPose(analysis.pose_analysis),
          lighting_feedback: this.interpretLighting(analysis.lighting_analysis),
          composition_tips: this.interpretComposition(analysis.composition_analysis),
          color_insights: this.interpretColors(analysis.color_analysis)
        };

        // Add priority suggestions
        result.data.priority_actions = this.prioritizeSuggestions(analysis.improvement_suggestions || []);
        
        // Add skill level recommendations
        result.data.skill_recommendations = this.getSkillRecommendations(analysis);
      }

      return result;
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        code: 'DETAILED_ANALYSIS_ERROR',
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

  // AI Analysis Interpretation Methods
  static interpretRating(score) {
    if (score >= 9) return { message: "Outstanding! This image has exceptional quality across all aspects.", level: "professional" };
    if (score >= 8) return { message: "Excellent work! Your image shows strong technical and artistic skills.", level: "advanced" };
    if (score >= 7) return { message: "Good quality image with solid fundamentals. A few tweaks could make it great!", level: "intermediate" };
    if (score >= 6) return { message: "Decent image with potential. Focus on the key areas for improvement.", level: "developing" };
    if (score >= 5) return { message: "Average quality. Practice the fundamentals to see significant improvement.", level: "beginner" };
    return { message: "Lots of room for improvement. Focus on basic photography principles.", level: "learning" };
  }

  static summarizeTechnical(technical) {
    if (!technical) return "Technical analysis not available";
    
    const issues = [];
    const strengths = [];
    
    if (technical.sharpness?.score < 5) issues.push("sharpness");
    else if (technical.sharpness?.score > 7) strengths.push("excellent sharpness");
    
    if (technical.noise?.rating === "High") issues.push("noise levels");
    else if (technical.noise?.rating === "Low") strengths.push("clean image quality");
    
    if (technical.exposure?.overall !== "Good") issues.push("exposure");
    else strengths.push("well-exposed");
    
    let summary = "";
    if (strengths.length > 0) summary += `Strengths: ${strengths.join(", ")}. `;
    if (issues.length > 0) summary += `Areas to improve: ${issues.join(", ")}.`;
    
    return summary || "Technical quality is balanced overall.";
  }

  static interpretPose(poseAnalysis) {
    if (!poseAnalysis?.detected) return "No pose detected in the image.";
    
    const score = poseAnalysis.quality_score || 0;
    if (score >= 8) return "Excellent pose! Natural and engaging positioning.";
    if (score >= 7) return "Good pose with confident body language.";
    if (score >= 6) return "Decent pose, could be more dynamic.";
    return "Pose needs work - try more natural and open positioning.";
  }

  static interpretLighting(lightingAnalysis) {
    if (!lightingAnalysis) return "Lighting analysis not available.";
    
    const quality = lightingAnalysis.overall_quality;
    const shadows = lightingAnalysis.shadows?.percentage || 0;
    
    if (quality === "Excellent") return "Perfect lighting with great balance and direction.";
    if (quality === "Good") return "Good lighting setup with minor areas for improvement.";
    if (shadows > 30) return "Consider using fill light to reduce harsh shadows.";
    return "Lighting could be improved - focus on even illumination.";
  }

  static interpretComposition(compositionAnalysis) {
    if (!compositionAnalysis) return "Composition analysis not available.";
    
    const overall = compositionAnalysis.overall_score || 0;
    if (overall >= 8) return "Excellent composition following professional guidelines.";
    if (overall >= 7) return "Good composition with strong visual appeal.";
    if (overall >= 6) return "Decent composition, try the rule of thirds for improvement.";
    return "Composition needs work - focus on subject placement and balance.";
  }

  static interpretColors(colorAnalysis) {
    if (!colorAnalysis) return "Color analysis not available.";
    
    const harmony = colorAnalysis.harmony?.score || 0;
    const saturation = colorAnalysis.saturation?.score || 0;
    
    if (harmony >= 8 && saturation >= 7) return "Excellent color palette with perfect harmony and saturation.";
    if (harmony >= 7) return "Good color harmony with natural saturation levels.";
    if (harmony >= 6) return "Decent colors, consider adjusting for better harmony.";
    return "Color palette could be improved - experiment with complementary colors.";
  }

  static prioritizeSuggestions(suggestions) {
    if (!Array.isArray(suggestions)) return [];
    
    const priorityOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
    
    return suggestions
      .sort((a, b) => (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0))
      .slice(0, 5) // Top 5 suggestions
      .map((suggestion, index) => ({
        ...suggestion,
        rank: index + 1,
        actionable: this.makeActionable(suggestion)
      }));
  }

  static makeActionable(suggestion) {
    const actionableMap = {
      'Technical': 'Use a tripod, check camera settings, or improve lighting setup',
      'Lighting': 'Add fill light, use reflectors, or change shooting angle',
      'Pose': 'Adjust body angle, relax shoulders, or change hand positioning',
      'Composition': 'Reframe the shot, move closer/further, or change perspective',
      'Color': 'Adjust white balance, modify saturation, or change color grading'
    };
    
    return actionableMap[suggestion.category] || 'Review and apply the specific suggestion provided';
  }

  static getSkillRecommendations(analysis) {
    const overallScore = analysis.overall_rating?.score || 0;
    const recommendations = [];
    
    if (overallScore < 6) {
      recommendations.push({
        skill: "Basic Photography",
        focus: "Learn fundamental composition rules and camera operation",
        resources: ["Rule of thirds", "Basic lighting", "Camera settings"]
      });
    }
    
    if (analysis.technical_quality?.sharpness?.score < 6) {
      recommendations.push({
        skill: "Camera Technique",
        focus: "Improve focus accuracy and reduce camera shake",
        resources: ["Tripod usage", "Focus techniques", "Shutter speed"]
      });
    }
    
    if (analysis.lighting_analysis?.overall_quality === "Needs Improvement") {
      recommendations.push({
        skill: "Lighting Fundamentals",
        focus: "Master natural and artificial lighting techniques",
        resources: ["Golden hour", "Fill lighting", "Light direction"]
      });
    }
    
    if (analysis.pose_analysis?.detected && analysis.pose_analysis?.quality_score < 7) {
      recommendations.push({
        skill: "Portrait Posing",
        focus: "Learn natural posing and body language techniques",
        resources: ["Posing guides", "Body angles", "Hand positioning"]
      });
    }
    
    return recommendations;
  }

  // Connection testing
  static async testConnection() {
    try {
      const health = await this.healthCheck();
      if (health.success) {
        console.log('✅ Backend connection successful');
        const gpuStatus = health.data.gpu_status || { available: false };
        return {
          connected: true,
          gpu_available: gpuStatus.available,
          gpu_name: gpuStatus.device_name || null,
          gpu_memory: gpuStatus.memory_total || null
        };
      } else {
        console.error('❌ Backend health check failed:', health.error);
        return { connected: false, gpu_available: false };
      }
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      return { connected: false, gpu_available: false };
    }
  }

  // Fetch usage status (ip-based)
  static async getUsageStatus() {
    return await this.makeRequest('/usage-status/');
  }

  static async incrementUsage() {
    return await this.makeRequest('/usage-increment/', {
      method: 'POST'
    });
  }

  // Helper method to refresh usage after analysis
  static async refreshUsage() {
    // Trigger usage refresh by calling the usage status
    const result = await this.getUsageStatus();
    if (result.success && window.__AURA_USAGE_REFRESH_CALLBACK__) {
      window.__AURA_USAGE_REFRESH_CALLBACK__(result.data);
    }
    return result;
  }

  // Wrapper to perform analysis and auto-refresh usage
  static async performAnalysisWithUsageUpdate(analysisFunction) {
    const result = await analysisFunction();
    
    // If analysis was successful, refresh usage data
    if (result.success) {
      setTimeout(() => this.refreshUsage(), 500); // Small delay to ensure backend has updated
    }
    
    return result;
  }
}

export default ApiService;