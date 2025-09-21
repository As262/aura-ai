// Mock API service for AuraAI features
class MockApiService {
  
  // Simulate network delay
  static delay(ms = 2000) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Mock Aesthetic Analyzer API
  static async analyzeAesthetic(file, caption) {
    await this.delay(2000);
    
    // Simulate analysis based on file type and caption content
    const results = {
      aestheticScore: this.generateScore(70, 100),
      captionTone: this.getRandomTone(),
      hashtagSuggestions: this.getRandomHashtags(),
      visualStyle: this.getRandomVisualStyle(),
      colorPalette: this.getRandomColorPalette(),
      postingPattern: this.getRandomPostingPattern(),
      engagementPrediction: this.generateScore(75, 100),
      audienceMatch: this.getRandomAudienceMatch(),
      contentCategories: this.getRandomContentCategories(),
      moodBoard: this.getRandomMoodBoard()
    };

    return { success: true, data: results };
  }

  // Mock Conversation Decoder API
  static async analyzeConversation(file) {
    await this.delay(2500);
    
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
      communicationHealth: this.getRandomHealthScore()
    };

    return { success: true, data: results };
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

  static getRandomHashtags() {
    const hashtagSets = [
      ['#aesthetic', '#vibes', '#mood', '#inspiration', '#lifestyle'],
      ['#photography', '#art', '#creative', '#visualart', '#capture'],
      ['#minimalist', '#clean', '#simple', '#modernart', '#design'],
      ['#colorful', '#vibrant', '#energetic', '#bold', '#expression'],
      ['#vintage', '#retro', '#classic', '#timeless', '#nostalgia'],
      ['#nature', '#outdoor', '#adventure', '#explore', '#wanderlust'],
      ['#fashionista', '#style', '#outfit', '#trendy', '#chic'],
      ['#foodie', '#delicious', '#yummy', '#cooking', '#recipe']
    ];
    return hashtagSets[Math.floor(Math.random() * hashtagSets.length)];
  }

  static getRandomVisualStyle() {
    const styles = [
      'Minimalist Modern',
      'Vintage Aesthetic',
      'Bold & Colorful',
      'Moody & Dramatic',
      'Clean & Bright',
      'Artistic & Creative',
      'Urban & Edgy',
      'Soft & Dreamy'
    ];
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

  static getRandomPostingPattern() {
    const patterns = [
      'Consistent Daily Poster',
      'Weekend Warrior',
      'Sporadic Creator',
      'Strategic Scheduler',
      'Spontaneous Sharer',
      'Curated Perfectionist',
      'Story Enthusiast',
      'Feed Perfectionist'
    ];
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