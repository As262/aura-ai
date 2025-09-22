// Mock API service for AuraAI features
class MockApiService {
  
  // Simulate network delay
  static delay(ms = 2000) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Mock Aesthetic Analyzer API
  static async analyzeAesthetic(file, caption, platform = 'instagram') {
    await this.delay(2000);
    
    try {
      // Simulate random errors (5% chance)
      if (Math.random() < 0.05) {
        throw new Error('Service temporarily unavailable. Please try again.');
      }

      // Simulate platform-specific rate limiting
      if (this.isRateLimited(platform)) {
        throw new Error(`Rate limit exceeded for ${platform}. Please wait before making another request.`);
      }
      
      // Simulate analysis based on file type and caption content
      const results = {
        aestheticScore: this.generateScore(70, 100),
        captionTone: this.getRandomTone(),
        hashtagSuggestions: this.getRandomHashtags(platform),
        visualStyle: this.getRandomVisualStyle(platform),
        colorPalette: this.getRandomColorPalette(),
        postingPattern: this.getRandomPostingPattern(platform),
        engagementPrediction: this.generateScore(75, 100),
        audienceMatch: this.getRandomAudienceMatch(),
        contentCategories: this.getRandomContentCategories(),
        moodBoard: this.getRandomMoodBoard(),
        platform: platform,
        timestamp: new Date().toISOString()
      };

      return { success: true, data: results };
    } catch (error) {
      console.error('Aesthetic analysis error:', error);
      return { 
        success: false, 
        error: error.message,
        code: 'ANALYSIS_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  // Mock Conversation Decoder API
  static async analyzeConversation(file) {
    await this.delay(2500);
    
    try {
      // Simulate random errors (3% chance)
      if (Math.random() < 0.03) {
        throw new Error('Failed to process conversation file. Please ensure the file format is supported.');
      }

      // Simulate file size validation
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        throw new Error('File too large. Please upload a file smaller than 5MB.');
      }
      
      const results = {
        replyDelay: this.getRandomReplyDelay(),
        conversationBalance: this.getRandomBalance(),
        communicationStyle: this.getRandomCommStyle(),
        moodAnalysis: this.getRandomMood(),
        romanticInterest: this.getRandomRomanticCues(),
        personalityTraits: this.getRandomPersonalityTraits(),
        responseLength: this.getRandomResponseLength(),
        emojiUsage: this.getRandomEmojiPattern(),
        engagementLevel: this.generateScore(75, 100),
        conversationStarter: this.getRandomStarterStyle(),
        socialMetrics: this.getRandomSocialMetrics(),
        communicationHealth: this.getRandomHealthScore(),
        timestamp: new Date().toISOString()
      };

      return { success: true, data: results };
    } catch (error) {
      console.error('Conversation analysis error:', error);
      return { 
        success: false, 
        error: error.message,
        code: 'CONVERSATION_ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  // Rate limiting simulation
  static rateLimitStore = new Map();
  
  static isRateLimited(platform) {
    const key = `${platform}_requests`;
    const now = Date.now();
    const windowMs = 60 * 1000; // 1 minute window
    const maxRequests = 10; // 10 requests per minute
    
    if (!this.rateLimitStore.has(key)) {
      this.rateLimitStore.set(key, []);
    }
    
    const requests = this.rateLimitStore.get(key);
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < windowMs);
    
    if (validRequests.length >= maxRequests) {
      return true;
    }
    
    // Add current request
    validRequests.push(now);
    this.rateLimitStore.set(key, validRequests);
    
    return false;
  }

  // Network status simulation
  static simulateNetworkIssue() {
    if (Math.random() < 0.02) { // 2% chance
      throw new Error('Network connection lost. Please check your internet connection and try again.');
    }
  }

  // Enhanced error handling for file validation
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

    if (file.size < 1024) { // Less than 1KB
      throw new Error('File appears to be corrupted or empty');
    }
  }

  // Helper methods for generating random mock data
  static generateScore(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  static getRandomTone() {
    const tones = [
      'Inspirational & Uplifting',
      'Casual & Friendly', 
      'Professional & Polished',
      'Creative & Artistic',
      'Minimalist & Clean',
      'Bold & Confident',
      'Humorous & Playful',
      'Thoughtful & Reflective'
    ];
    return tones[Math.floor(Math.random() * tones.length)];
  }

  static getRandomHashtags(platform = 'instagram') {
    const platformSpecificHashtags = {
      instagram: [
        ['#aesthetic', '#vibes', '#mood', '#inspiration', '#lifestyle'],
        ['#photography', '#art', '#creative', '#visualart', '#capture'],
        ['#minimalist', '#clean', '#simple', '#modernart', '#design'],
        ['#colorful', '#vibrant', '#energetic', '#bold', '#expression'],
        ['#vintage', '#retro', '#classic', '#timeless', '#nostalgia'],
        ['#nature', '#outdoor', '#adventure', '#explore', '#wanderlust'],
        ['#fashionista', '#style', '#outfit', '#trendy', '#chic'],
        ['#foodie', '#delicious', '#yummy', '#cooking', '#recipe']
      ],
      tiktok: [
        ['#fyp', '#foryou', '#viral', '#trending', '#tiktok'],
        ['#dance', '#music', '#trend', '#challenge', '#duet'],
        ['#comedy', '#funny', '#humor', '#meme', '#laugh'],
        ['#aesthetic', '#vibes', '#mood', '#style', '#outfit'],
        ['#tutorial', '#howto', '#tips', '#diy', '#lifehack']
      ],
      twitter: [
        ['#Breaking', '#News', '#Update', '#Thread', '#Opinion'],
        ['#Tech', '#AI', '#Innovation', '#Future', '#Digital'],
        ['#Motivation', '#Success', '#Goals', '#Growth', '#Mindset'],
        ['#Community', '#Discussion', '#Thoughts', '#Perspective', '#Ideas']
      ],
      youtube: [
        ['#Tutorial', '#HowTo', '#Guide', '#Tips', '#Learn'],
        ['#Review', '#Unboxing', '#Tech', '#Gaming', '#Entertainment'],
        ['#Vlog', '#Daily', '#Lifestyle', '#Travel', '#Adventure'],
        ['#Music', '#Cover', '#Original', '#Performance', '#Artist']
      ],
      linkedin: [
        ['#Professional', '#Career', '#Leadership', '#Business', '#Success'],
        ['#Networking', '#Industry', '#Insights', '#Growth', '#Innovation'],
        ['#Workplace', '#Skills', '#Development', '#Strategy', '#Trends']
      ]
    };
    
    const hashtagSets = platformSpecificHashtags[platform] || platformSpecificHashtags.instagram;
    return hashtagSets[Math.floor(Math.random() * hashtagSets.length)];
  }

  static getRandomVisualStyle(platform = 'instagram') {
    const platformStyles = {
      instagram: [
        'Minimalist Modern', 'Vintage Aesthetic', 'Bold & Colorful', 
        'Moody & Dramatic', 'Clean & Bright', 'Artistic & Creative', 
        'Urban & Edgy', 'Soft & Dreamy'
      ],
      tiktok: [
        'Dynamic & Energetic', 'Trendy & Fresh', 'Pop Culture Vibes',
        'Quick & Snappy', 'Gen-Z Aesthetic', 'Viral Ready'
      ],
      youtube: [
        'Professional & Polished', 'Cinematic Quality', 'Thumbnail Worthy',
        'Engaging & Clear', 'Brand Consistent', 'High Production Value'
      ],
      twitter: [
        'Clean & Professional', 'News Worthy', 'Discussion Starter',
        'Shareable Content', 'Topic Focused'
      ],
      linkedin: [
        'Corporate & Professional', 'Industry Standard', 'Business Focused',
        'Executive Level', 'Thought Leadership'
      ]
    };
    
    const styles = platformStyles[platform] || platformStyles.instagram;
    return styles[Math.floor(Math.random() * styles.length)];
  }

  static getRandomColorPalette() {
    const palettes = [
      { primary: 'Soft Pink', secondary: 'Cream White', accent: 'Gold' },
      { primary: 'Deep Blue', secondary: 'Light Gray', accent: 'Orange' },
      { primary: 'Forest Green', secondary: 'Beige', accent: 'Rust' },
      { primary: 'Purple', secondary: 'Lavender', accent: 'Yellow' },
      { primary: 'Black', secondary: 'White', accent: 'Red' },
      { primary: 'Teal', secondary: 'Coral', accent: 'Gold' },
      { primary: 'Sage Green', secondary: 'Cream', accent: 'Terracotta' },
      { primary: 'Navy Blue', secondary: 'Blush', accent: 'Bronze' }
    ];
    return palettes[Math.floor(Math.random() * palettes.length)];
  }

  static getRandomPostingPattern(platform = 'instagram') {
    const platformPatterns = {
      instagram: [
        'Consistent Daily Poster', 'Weekend Warrior', 'Sporadic Creator',
        'Strategic Scheduler', 'Spontaneous Sharer', 'Curated Perfectionist',
        'Story Enthusiast', 'Feed Perfectionist'
      ],
      tiktok: [
        'Multiple Daily Posts', 'Trend Chaser', 'Peak Hours Poster',
        'Viral Content Creator', 'Consistent Creator', 'Weekend Trendsetter'
      ],
      youtube: [
        'Weekly Uploader', 'Consistent Scheduler', 'Series Creator',
        'Long-form Producer', 'Quality over Quantity', 'Strategic Releaser'
      ],
      twitter: [
        'Real-time Responder', 'Thread Creator', 'News Commentator',
        'Daily Tweeter', 'Conversation Starter', 'Thought Leader'
      ],
      linkedin: [
        'Weekly Thought Leader', 'Industry Commentator', 'Professional Updater',
        'Business Insights Sharer', 'Network Engager', 'Content Curator'
      ]
    };
    
    const patterns = platformPatterns[platform] || platformPatterns.instagram;
    return patterns[Math.floor(Math.random() * patterns.length)];
  }

  static getRandomAudienceMatch() {
    const matches = [
      'Gen-Z Creatives',
      'Millennial Professionals',
      'Art Enthusiasts',
      'Lifestyle Influencers',
      'Travel Lovers',
      'Fashion Forward',
      'Fitness Community',
      'Food & Culture'
    ];
    return matches[Math.floor(Math.random() * matches.length)];
  }

  static getRandomContentCategories() {
    const categories = [
      ['Lifestyle', 'Fashion', 'Travel'],
      ['Art', 'Photography', 'Design'],
      ['Food', 'Culture', 'Adventure'],
      ['Fitness', 'Wellness', 'Mindfulness'],
      ['Tech', 'Innovation', 'Creativity'],
      ['Nature', 'Sustainability', 'Outdoor']
    ];
    return categories[Math.floor(Math.random() * categories.length)];
  }

  static getRandomMoodBoard() {
    const moods = [
      ['Ethereal', 'Dreamy', 'Soft'],
      ['Bold', 'Confident', 'Striking'],
      ['Minimal', 'Clean', 'Sophisticated'],
      ['Warm', 'Cozy', 'Inviting'],
      ['Fresh', 'Energetic', 'Vibrant'],
      ['Mysterious', 'Moody', 'Artistic']
    ];
    return moods[Math.floor(Math.random() * moods.length)];
  }

  // Conversation analysis helper methods
  static getRandomReplyDelay() {
    const delays = [
      'Instant Responder (< 1 min)',
      'Quick Replier (1-5 mins)',
      'Thoughtful Responder (10-30 mins)',
      'Casual Replier (1-2 hours)',
      'Delayed Responder (3+ hours)',
      'Strategic Timing (varies)',
      'Night Owl Replier',
      'Morning Person'
    ];
    return delays[Math.floor(Math.random() * delays.length)];
  }

  static getRandomBalance() {
    const balances = [
      'Perfectly Balanced',
      'Slightly Talkative',
      'Great Listener',
      'Conversation Driver',
      'Reactive Communicator',
      'Question Asker',
      'Story Sharer',
      'Supportive Responder'
    ];
    return balances[Math.floor(Math.random() * balances.length)];
  }

  static getRandomCommStyle() {
    const styles = [
      'Enthusiastic & Energetic',
      'Calm & Thoughtful',
      'Witty & Humorous',
      'Direct & Clear',
      'Supportive & Caring',
      'Analytical & Detailed',
      'Casual & Relaxed',
      'Expressive & Emotional'
    ];
    return styles[Math.floor(Math.random() * styles.length)];
  }

  static getRandomMood() {
    const moods = [
      { dominant: 'Positive', secondary: 'Playful', intensity: 'High' },
      { dominant: 'Neutral', secondary: 'Curious', intensity: 'Medium' },
      { dominant: 'Excited', secondary: 'Enthusiastic', intensity: 'Very High' },
      { dominant: 'Calm', secondary: 'Thoughtful', intensity: 'Low' },
      { dominant: 'Supportive', secondary: 'Caring', intensity: 'High' },
      { dominant: 'Humorous', secondary: 'Witty', intensity: 'Medium' },
      { dominant: 'Analytical', secondary: 'Logical', intensity: 'Medium' },
      { dominant: 'Creative', secondary: 'Imaginative', intensity: 'High' }
    ];
    return moods[Math.floor(Math.random() * moods.length)];
  }

  static getRandomRomanticCues() {
    const cues = [
      'High Flirtation Level',
      'Subtle Romantic Interest',
      'Friendly & Platonic',
      'Professional Tone',
      'Caring & Intimate',
      'Playful Teasing',
      'Sweet & Affectionate',
      'Respectful Distance'
    ];
    return cues[Math.floor(Math.random() * cues.length)];
  }

  static getRandomPersonalityTraits() {
    const traitSets = [
      ['Empathetic', 'Outgoing', 'Creative', 'Optimistic'],
      ['Analytical', 'Thoughtful', 'Reliable', 'Curious'],
      ['Humorous', 'Spontaneous', 'Energetic', 'Social'],
      ['Supportive', 'Patient', 'Wise', 'Calming'],
      ['Adventurous', 'Bold', 'Independent', 'Confident'],
      ['Artistic', 'Intuitive', 'Passionate', 'Expressive'],
      ['Logical', 'Organized', 'Focused', 'Detail-oriented'],
      ['Caring', 'Gentle', 'Understanding', 'Nurturing']
    ];
    return traitSets[Math.floor(Math.random() * traitSets.length)];
  }

  static getRandomResponseLength() {
    const lengths = [
      'Concise Communicator',
      'Detailed Explainer',
      'Balanced Responder',
      'Brief & Direct',
      'Story Teller',
      'Context Provider',
      'Bullet Point Master',
      'Paragraph Writer'
    ];
    return lengths[Math.floor(Math.random() * lengths.length)];
  }

  static getRandomEmojiPattern() {
    const patterns = [
      'Emoji Enthusiast 😍🎉✨',
      'Minimal Emoji User 😊',
      'Emotional Expresser 💕😢😂',
      'No Emoji Style',
      'Heart Collector ❤️💙💚',
      'Face Expression Pro 😄😅🤔',
      'Nature Lover 🌸🌿🦋',
      'Food Emoji Fan 🍕🌮🍰'
    ];
    return patterns[Math.floor(Math.random() * patterns.length)];
  }

  static getRandomStarterStyle() {
    const styles = [
      'Question Master',
      'Topic Introducer',
      'Reactive Responder',
      'Story Sharer',
      'Check-in Champion',
      'Random Fact Dropper',
      'Meme Sender',
      'Update Giver'
    ];
    return styles[Math.floor(Math.random() * styles.length)];
  }

  static getRandomSocialMetrics() {
    return {
      initiationRate: this.generateScore(20, 80),
      responseRate: this.generateScore(80, 100),
      conversationLength: this.generateScore(5, 50),
      topicDiversity: this.generateScore(30, 90)
    };
  }

  static getRandomHealthScore() {
    const scores = [
      { score: this.generateScore(85, 100), status: 'Excellent Communication' },
      { score: this.generateScore(70, 84), status: 'Good Communication' },
      { score: this.generateScore(55, 69), status: 'Average Communication' },
      { score: this.generateScore(40, 54), status: 'Needs Improvement' }
    ];
    return scores[Math.floor(Math.random() * scores.length)];
  }
}

export default MockApiService;