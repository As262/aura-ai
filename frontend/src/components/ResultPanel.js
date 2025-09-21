import React from 'react';
import './ResultPanel.css';

const ResultPanel = ({ title, results, isVisible = false }) => {
  if (!isVisible || !results) {
    return null;
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
                <span className="nested-value">{nestedValue}</span>
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
              {value}
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
        {Object.entries(results).map(([key, value]) => 
          renderResultItem(key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()), value)
        )}
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
};

export default ResultPanel;