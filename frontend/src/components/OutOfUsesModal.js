import React from 'react';
import './OutOfUsesModal.css';

const OutOfUsesModal = ({ isOpen, onClose, featureName, usedCount, limit }) => {
  if (!isOpen) return null;

  return (
    <div className="out-of-uses-overlay" onClick={onClose}>
      <div className="out-of-uses-modal" onClick={(e) => e.stopPropagation()}>
        <button className="out-of-uses-close" onClick={onClose} aria-label="Close">
          ✕
        </button>
        
        <div className="out-of-uses-content">
          <div className="out-of-uses-header">
            <div className="out-of-uses-icon">⚠️</div>
            <div className="out-of-uses-info">
              <h2>You're Out of Uses!</h2>
              <p>You've used all <strong>{usedCount}/{limit}</strong> {featureName} analyses</p>
            </div>
          </div>
          
          <div className="out-of-uses-action">
            <a href="/pricing" className="upgrade-button">
              ⭐ View Pricing Plans
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OutOfUsesModal;
