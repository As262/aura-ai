import React from 'react';
import FeatureCard from '../components/FeatureCard';
import './LandingPage.css';

const LandingPage = () => {

  const scrollToFeatures = () => {
    document.getElementById('features').scrollIntoView({ 
      behavior: 'smooth' 
    });
  };

  const handleGetStarted = () => {
    document.getElementById('features').scrollIntoView({ 
      behavior: 'smooth' 
    });
  };

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              Unlock Your <span className="gradient-text">Digital Persona</span>
            </h1>
            <p className="hero-tagline">
              Discover what your Instagram posts and chat patterns reveal about your unique digital identity. 
              Get AI-powered insights into your aesthetic vibes and conversation style.
            </p>
            <div className="hero-actions">
              <button 
                className="btn btn-primary btn-large btn-hero-cta"
                onClick={handleGetStarted}
              >
                Get Started
              </button>
              <button 
                className="btn btn-outline btn-large"
                onClick={scrollToFeatures}
              >
                Learn More
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="geometric-background">
              <div className="geometric-shape shape-1"></div>
              <div className="geometric-shape shape-2"></div>
              <div className="geometric-shape shape-3"></div>
              <div className="geometric-shape shape-4"></div>
              <div className="geometric-shape shape-5"></div>
              <div className="geometric-shape shape-6"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="features-container">
          <div className="features-header">
            <h2 className="features-title">
              Discover Your <span className="gradient-text">Digital Aura</span>
            </h2>
            <p className="features-subtitle">
              Two powerful AI tools to analyze and understand your digital presence
            </p>
          </div>
          
          <div className="features-grid">
            <FeatureCard
              icon="🎨"
              title="Aesthetic Analyzer"
              description="Upload your Instagram posts and captions to discover your visual aesthetic, posting patterns, and the vibe you project to the world."
              buttonText="Try Now"
              linkTo="/aesthetic-analyzer"
            />
            <FeatureCard
              icon="💬"
              title="Convo Decoder"
              description="Analyze your chat logs to uncover your communication style, response patterns, and how you connect with others digitally."
              buttonText="Try Now"
              linkTo="/convo-decoder"
            />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats">
        <div className="stats-container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">10K+</div>
              <div className="stat-label">Posts Analyzed</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">5K+</div>
              <div className="stat-label">Happy Users</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">95%</div>
              <div className="stat-label">Accuracy Rate</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">AI Analysis</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="cta-container">
          <h2 className="cta-title">Ready to Explore Your Digital Self?</h2>
          <p className="cta-description">
            Join thousands of users who've discovered their unique digital persona
          </p>
          <button 
            className="btn btn-primary btn-large btn-cta-final"
            onClick={scrollToFeatures}
          >
            Start Your Analysis
          </button>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;