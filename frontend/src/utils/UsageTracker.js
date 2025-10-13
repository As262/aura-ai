// Usage tracking utility for localStorage-based IP tracking
class UsageTracker {
  constructor() {
    this.STORAGE_KEY = 'aura_ai_usage_tracking';
    this.LIMITS = {
      aesthetic_analyzer: 5,
      convo_decoder: 15
    };
  }

  // Get current usage data from localStorage
  getUsageData() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (!data) {
        return this.initializeUsageData();
      }
      return JSON.parse(data);
    } catch (error) {
      console.error('Error reading usage data:', error);
      return this.initializeUsageData();
    }
  }

  // Initialize new usage data structure
  initializeUsageData() {
    const data = {
      aesthetic_analyzer: {
        count: 0,
        limit: this.LIMITS.aesthetic_analyzer,
        remaining: this.LIMITS.aesthetic_analyzer,
        lastReset: Date.now()
      },
      convo_decoder: {
        count: 0,
        limit: this.LIMITS.convo_decoder,
        remaining: this.LIMITS.convo_decoder,
        lastReset: Date.now()
      }
    };
    this.saveUsageData(data);
    return data;
  }

  // Save usage data to localStorage
  saveUsageData(data) {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving usage data:', error);
    }
  }

  // Get usage for a specific feature
  getFeatureUsage(feature) {
    const data = this.getUsageData();
    return data[feature] || {
      count: 0,
      limit: this.LIMITS[feature] || 0,
      remaining: this.LIMITS[feature] || 0,
      lastReset: Date.now()
    };
  }

  // Check if user can use a feature
  canUseFeature(feature) {
    const usage = this.getFeatureUsage(feature);
    return usage.remaining > 0;
  }

  // Increment usage for a feature
  incrementUsage(feature) {
    const data = this.getUsageData();
    
    if (!data[feature]) {
      data[feature] = {
        count: 0,
        limit: this.LIMITS[feature] || 0,
        remaining: this.LIMITS[feature] || 0,
        lastReset: Date.now()
      };
    }

    if (data[feature].remaining > 0) {
      data[feature].count += 1;
      data[feature].remaining = Math.max(0, data[feature].limit - data[feature].count);
      this.saveUsageData(data);
      
      // Trigger event for other components to update
      window.dispatchEvent(new CustomEvent('usageUpdated', { 
        detail: { feature, usage: data[feature] } 
      }));
      
      return true;
    }
    return false;
  }

  // Reset usage for a specific feature
  resetFeature(feature) {
    const data = this.getUsageData();
    if (data[feature]) {
      data[feature].count = 0;
      data[feature].remaining = data[feature].limit;
      data[feature].lastReset = Date.now();
      this.saveUsageData(data);
      
      window.dispatchEvent(new CustomEvent('usageUpdated', { 
        detail: { feature, usage: data[feature] } 
      }));
    }
  }

  // Reset all usage
  resetAll() {
    const data = this.initializeUsageData();
    window.dispatchEvent(new CustomEvent('usageUpdated', { 
      detail: { feature: 'all', usage: data } 
    }));
  }

  // Get all usage data
  getAllUsage() {
    return this.getUsageData();
  }
}

// Export singleton instance
export default new UsageTracker();
