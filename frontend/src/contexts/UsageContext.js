import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import UsageTracker from '../utils/UsageTracker';

const UsageContext = createContext(null);

export function UsageProvider({ children }) {
  const [usage, setUsage] = useState({
    aesthetic_analyzer: UsageTracker.getFeatureUsage('aesthetic_analyzer'),
    convo_decoder: UsageTracker.getFeatureUsage('convo_decoder')
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Listen for usage updates from UsageTracker
  useEffect(() => {
    const handleUsageUpdate = () => {
      setUsage({
        aesthetic_analyzer: UsageTracker.getFeatureUsage('aesthetic_analyzer'),
        convo_decoder: UsageTracker.getFeatureUsage('convo_decoder')
      });
    };

    window.addEventListener('usageUpdated', handleUsageUpdate);
    return () => window.removeEventListener('usageUpdated', handleUsageUpdate);
  }, []);

  const performAnalysis = useCallback(async (feature, analysisFunction) => {
    // Validate feature
    if (!feature || !['aesthetic_analyzer', 'convo_decoder'].includes(feature)) {
      console.error('Invalid feature:', feature);
      return {
        success: false,
        error: 'Invalid feature specified'
      };
    }

    // Check if user can still use the service
    const canUse = UsageTracker.canUseFeature(feature);
    if (!canUse) {
      const featureUsage = UsageTracker.getFeatureUsage(feature);
      return {
        success: false,
        error: 'Usage limit exceeded',
        usage_limit_exceeded: true,
        current_usage: featureUsage.count,
        limit: featureUsage.limit
      };
    }

    // Perform the analysis
    const result = await analysisFunction();
    
    // If successful, increment usage
    if (result.success) {
      setIsRefreshing(true);
      UsageTracker.incrementUsage(feature);
      
      setTimeout(() => {
        setUsage({
          aesthetic_analyzer: UsageTracker.getFeatureUsage('aesthetic_analyzer'),
          convo_decoder: UsageTracker.getFeatureUsage('convo_decoder')
        });
        setIsRefreshing(false);
      }, 300);
    }
    
    return result;
  }, []);

  const refresh = useCallback(() => {
    setUsage({
      aesthetic_analyzer: UsageTracker.getFeatureUsage('aesthetic_analyzer'),
      convo_decoder: UsageTracker.getFeatureUsage('convo_decoder')
    });
  }, []);

  const resetFeature = useCallback((feature) => {
    UsageTracker.resetFeature(feature);
    refresh();
  }, [refresh]);

  const resetAll = useCallback(() => {
    UsageTracker.resetAll();
    refresh();
  }, [refresh]);

  const getFeatureUsage = useCallback((feature) => {
    return usage[feature] || { count: 0, limit: 0, remaining: 0 };
  }, [usage]);

  return (
    <UsageContext.Provider value={{ 
      usage,
      refresh,
      performAnalysis,
      isRefreshing,
      resetFeature,
      resetAll,
      getFeatureUsage
    }}>
      {children}
    </UsageContext.Provider>
  );
}

export function useUsage() {
  return useContext(UsageContext);
}
