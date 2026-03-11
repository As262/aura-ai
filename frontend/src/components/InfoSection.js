import React, { memo } from 'react';
import './InfoSection.css';

const InfoSection = memo(() => (
  <div className="info-section">
    <h2 className="info-title">AI Analysis Features</h2>
    <div className="info-grid">
      <div className="info-card">
        <div className="info-icon">⭐</div>
        <h3>Overall Rating</h3>
        <p>Comprehensive scoring based on technical quality, composition, and aesthetic appeal</p>
      </div>
      <div className="info-card">
        <div className="info-icon">🎯</div>
        <h3>Composition Analysis</h3>
        <p>Rule of thirds, leading lines, symmetry, and other composition techniques evaluation</p>
      </div>
      <div className="info-card">
        <div className="info-icon">💡</div>
        <h3>Lighting Assessment</h3>
        <p>Professional lighting analysis including exposure, contrast, and mood evaluation</p>
      </div>
      <div className="info-card">
        <div className="info-icon">🧍</div>
        <h3>Pose & Subject Analysis</h3>
        <p>Body positioning, facial expressions, and subject placement recommendations</p>
      </div>
    </div>
  </div>
));

InfoSection.displayName = 'InfoSection';

export default InfoSection;