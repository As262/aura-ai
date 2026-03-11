import React from 'react';
import './ResultPanel.css';

const ResultPanel = ({ title, results, isVisible = false }) => {
  console.log('🎯 ResultPanel props:', { title, results, isVisible });
  
  if (!isVisible || !results) {
    console.log('🎯 ResultPanel not rendering:', { isVisible, hasResults: !!results });
    return null;
  }

  try {
  
  // Check if we have formatted_text - display it instead of JSON
  if (results.formatted_text) {
    return (
      <div className="result-panel formatted-text-panel">
        <h2 className="result-title">{title || 'Analysis Results'}</h2>
        <pre className="formatted-analysis-text">{results.formatted_text}</pre>
      </div>
    );
  }

  const renderResultItem = (key, value) => {
    if (Array.isArray(value)) {
      return (
        <div key={key} className="result-item">
          <h4 className="result-label">{key}</h4>
          <div className="result-list">
            {value.map((item, index) => (
              <span key={index} className="result-tag">
                {item}
              </span>
            ))}
          </div>
        </div>
      );
    }

    if (typeof value === 'object' && value !== null) {
      return (
        <div key={key} className="result-item">
          <h4 className="result-label">{key}</h4>
          <div className="result-nested">
            {Object.entries(value).map(([nestedKey, nestedValue]) => (
              <div key={nestedKey} className="result-nested-item">
                <span className="nested-label">{nestedKey}:</span>
                <span className="nested-value">
                  {typeof nestedValue === 'object' && nestedValue !== null 
                    ? JSON.stringify(nestedValue, null, 2)
                    : String(nestedValue)
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return (
      <div key={key} className="result-item">
        <h4 className="result-label">{key}</h4>
        <div className="result-value">
          {typeof value === 'number' && key.toLowerCase().includes('score') ? (
            <div className="score-container">
              <div className="score-bar">
                <div 
                  className="score-fill" 
                  style={{ width: `${value}%` }}
                ></div>
              </div>
              <span className="score-text">{value}/100</span>
            </div>
          ) : (
            <span className={`result-text ${getValueClass(key, value)}`}>
              {typeof value === 'object' && value !== null 
                ? JSON.stringify(value, null, 2)
                : String(value)
              }
            </span>
          )}
        </div>
      </div>
    );
  };

  const getValueClass = (key, value) => {
    if (typeof value === 'number') {
      if (value >= 80) return 'value-high';
      if (value >= 60) return 'value-medium';
      return 'value-low';
    }
    
    if (typeof value === 'string') {
      const lowerValue = value.toLowerCase();
      if (lowerValue.includes('positive') || lowerValue.includes('high') || lowerValue.includes('good')) {
        return 'value-positive';
      }
      if (lowerValue.includes('negative') || lowerValue.includes('low') || lowerValue.includes('poor')) {
        return 'value-negative';
      }
    }
    
    return 'value-neutral';
  };

  return (
    <div className="result-panel">
      <div className="result-header">
        <h2 className="result-title">{title}</h2>
        <div className="result-indicator">
          <span className="indicator-dot"></span>
          Analysis Complete
        </div>
      </div>
      
      <div className="result-content">
        {Object.entries(results).map(([key, value]) => {
          // Filter for social media relevant items only
          const socialMediaKeys = [
            'aesthetic_score', 'aestheticScore', 'platform', 
            'engagement_potential', 'hashtag_recommendations', 
            'best_posting_time', 'platform_optimization'
          ];
          
          // If this is social media analysis, show only relevant items
          const isSocialMedia = results.platform || results.result?.platform;
          if (isSocialMedia && !socialMediaKeys.includes(key) && !key.includes('score')) {
            return null; // Skip non-social media items
          }
          
          return renderResultItem(key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()), value);
        })}
      </div>
      
      <div className="result-actions">
        <button className="btn btn-secondary" onClick={() => window.print()}>
          📊 Export Results
        </button>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>
          🔄 Analyze Another
        </button>
      </div>
    </div>
  );
  } catch (error) {
    console.error('❌ ResultPanel render error:', error);
    return (
      <div className="result-panel error">
        <div className="result-header">
          <h2 className="result-title">Display Error</h2>
        </div>
        <div className="result-content">
          <p>Unable to display results. Please try again.</p>
        </div>
      </div>
    );
  }
};

export default ResultPanel;