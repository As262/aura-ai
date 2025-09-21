import React from 'react';
import { Link } from 'react-router-dom';
import './FeatureCard.css';

const FeatureCard = ({ icon, title, description, buttonText, linkTo }) => {
  return (
    <div className="feature-card">
      <div className="feature-icon">
        {icon}
      </div>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-description">{description}</p>
      <Link to={linkTo} className="btn btn-feature">
        {buttonText}
      </Link>
    </div>
  );
};

export default FeatureCard;