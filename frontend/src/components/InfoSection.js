import React, { memo } from 'react';
import './InfoSection.css';

const InfoSection = memo(() => (
  <div className="info-section">
    <h2 className="info-title">Instagram Aesthetic Analysis</h2>
    <div className="info-grid">
      <div className="info-card">
        <div className="info-icon">🎯</div>
        <h3>Instagram Appeal Score</h3>
        <p>Overall visual appeal rating based on Instagram's algorithmic preferences</p>
      </div>
      <div className="info-card">
        <div className="info-icon">💬</div>
        <h3>Caption Analysis</h3>
        <p>Emotional tone and engagement potential of your Instagram captions</p>
      </div>
      <div className="info-card">
        <div className="info-icon">#️⃣</div>
        <h3>Hashtag Optimization</h3>
        <p>Instagram hashtag suggestions to maximize reach and engagement</p>
      </div>
      <div className="info-card">
        <div className="info-icon">🎨</div>
        <h3>Feed Aesthetic</h3>
        <p>How your post fits with current Instagram aesthetic trends and styles</p>
      </div>
    </div>
  </div>
));

InfoSection.displayName = 'InfoSection';

export default InfoSection;