import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const heroRef = useRef(null);
  const featuresRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
          }
        });
      },
      { threshold: 0.1 }
    );

    const elements = document.querySelectorAll('.fade-on-scroll');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section ref={heroRef} className="hero-section">
        <div className="container">
          <div className="hero-grid">
            <div className="hero-content fade-on-scroll">
              <div className="hero-badge">
                <span className="badge-icon">⚡</span>
                <span>Neural Intelligence Powered</span>
              </div>
              
              <h1 className="text-hero">
                Transform Reality with
                <span className="hero-gradient"> Aura AI</span>
              </h1>
              
              <p className="hero-description text-body">
                Experience the future of artificial intelligence. Analyze images, decode conversations, 
                and unlock insights with our cutting-edge neural networks. Built for creators, 
                innovators, and digital pioneers.
              </p>
              
              <div className="hero-actions">
                <Link to="/aesthetic-analyzer" className="btn btn-primary btn-lg">
                  <span>Analyze Images</span>
                  <span className="btn-icon"></span>
                </Link>
                <Link to="/convo-decoder" className="btn btn-secondary btn-lg">
                  <span>Decode Conversations</span>
                  <span className="btn-icon"></span>
                </Link>
              </div>
              
              <div className="hero-stats">
                <div className="stat-item">
                  <div className="stat-number">99.9%</div>
                  <div className="stat-label">Accuracy</div>
                </div>
                <div className="stat-divider"></div>
                <div className="stat-item">
                  <div className="stat-number">~10s</div>
                  <div className="stat-label">Processing</div>
                </div>
                <div className="stat-divider"></div>
                <div className="stat-item">
                  <div className="stat-number">∞</div>
                  <div className="stat-label">Possibilities</div>
                </div>
              </div>
            </div>
            
            <div className="hero-visual fade-on-scroll">
              <div className="neural-sphere">
                <div className="sphere-inner">
                  <div className="neural-connections">
                    {Array.from({ length: 12 }).map((_, i) => (
                      <div key={i} className={`connection connection-${i + 1}`}></div>
                    ))}
                  </div>
                  <div className="neural-core">
                    <div className="core-pulse"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className="features-section">
        <div className="container">
          <div className="section-header fade-on-scroll">
            <h2 className="text-xl">
              Unleash the Power of <span className="text-gradient">Neural Intelligence</span>
            </h2>
            <p className="text-body">
              Discover what makes Aura AI the ultimate tool for digital analysis and insight generation
            </p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card glass fade-on-scroll">
              <h3 className="text-lg">Aesthetic Analysis</h3>
              <p className="text-body">
                Advanced computer vision to understand visual aesthetics, color harmony, 
                and artistic composition in your images.
              </p>
              <div className="feature-tech">
                <span className="tech-tag">CNN</span>
                <span className="tech-tag">Vision Transformer</span>
                <span className="tech-tag">StyleGAN</span>
              </div>
              <Link to="/aesthetic-analyzer" className="feature-link">
                Explore Analysis →
              </Link>
            </div>

            <div className="feature-card glass fade-on-scroll">
              <h3 className="text-lg">Conversation Decoding</h3>
              <p className="text-body">
                Natural language processing to analyze communication patterns, 
                sentiment, and conversational dynamics.
              </p>
              <div className="feature-tech">
                <span className="tech-tag">GPT</span>
                <span className="tech-tag">BERT</span>
                <span className="tech-tag">Transformer</span>
              </div>
              <Link to="/convo-decoder" className="feature-link">
                Decode Messages →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="tech-section">
        <div className="container">
          <div className="tech-content fade-on-scroll">
            <h2 className="text-xl text-center">
              Built on <span className="text-gradient">Cutting-Edge Technology</span>
            </h2>
            
            <div className="tech-grid">
              <div className="tech-item fade-on-scroll">
                <div className="tech-icon">🧠</div>
                <h4>Deep Learning</h4>
                <p>Advanced neural architectures</p>
              </div>
              <div className="tech-item fade-on-scroll">
                <div className="tech-icon">🔮</div>
                <h4>Computer Vision</h4>
                <p>State-of-the-art image analysis</p>
              </div>
              <div className="tech-item fade-on-scroll">
                <div className="tech-icon">📊</div>
                <h4>NLP Processing</h4>
                <p>Context-aware language models</p>
              </div>
              <div className="tech-item fade-on-scroll privacy-card">
                <div className="tech-icon">🔒</div>
                <h4>Privacy First</h4>
                <p>Your data stays local. Nothing stored, nothing shared. Complete privacy guaranteed.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;