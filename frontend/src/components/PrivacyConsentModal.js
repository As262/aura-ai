import React from 'react';
import './PrivacyConsentModal.css';

const PrivacyConsentModal = ({ isOpen, onAccept, onDecline }) => {
  if (!isOpen) return null;

  return (
    <div className="privacy-modal-overlay" onClick={onDecline}>
      <div className="privacy-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="privacy-compact-body">
          <span className="privacy-icon">🔒</span>
          <p className="privacy-message">
            Your files are processed locally and never stored. Completely private & secure.
          </p>
        </div>
        
        <div className="privacy-modal-footer">
          <button 
            className="privacy-btn privacy-btn-decline" 
            onClick={onDecline}
          >
            Cancel
          </button>
          <button 
            className="privacy-btn privacy-btn-accept" 
            onClick={onAccept}
          >
            Got it, Proceed
          </button>
        </div>
      </div>
    </div>
  );
};

export default PrivacyConsentModal;
