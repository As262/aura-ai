import React, { createContext, useContext } from 'react';
import useUsageStatus from '../hooks/useUsageStatus';

const UsageContext = createContext(null);

export function UsageProvider({ children }) {
  const { usage, refresh } = useUsageStatus();

  const performAnalysis = async (analysisFunction) => {
    // Check if user can still use the service
    if (usage && !usage.can_use) {
      return {
        success: false,
        error: 'Usage limit exceeded',
        usage_limit_exceeded: true,
        current_usage: usage.usage_count,
        limit: usage.limit
      };
    }

    // Perform the analysis
    const result = await analysisFunction();
    
    // If successful, refresh usage data
    if (result.success) {
      setTimeout(() => refresh(), 500);
    }
    
    return result;
  };

  const incrementMock = () => {
    // This is a placeholder for manual increment calls
    console.warn('incrementUsage not implemented on client');
  };

  return (
    <UsageContext.Provider value={{ 
      usage, 
      refresh, 
      incrementUsage: incrementMock,
      performAnalysis
    }}>
      {children}
    </UsageContext.Provider>
  );
}

export function useUsage() {
  return useContext(UsageContext);
}
