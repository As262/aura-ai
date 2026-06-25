import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  useEffect(() => {
    const elements = Array.from(document.querySelectorAll('.fade-on-scroll'));
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // No JS-animation path: leave everything visible.
    if (reduce || !('IntersectionObserver' in window)) return;

    // Hide ONLY content that starts below the fold, so anything already on
    // screen renders immediately and nothing can stay permanently blank.
    elements.forEach((el) => {
      if (el.getBoundingClientRect().top > window.innerHeight * 0.85) {
        el.classList.add('is-hidden');
      }
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.remove('is-hidden');
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    elements.forEach((el) => observer.observe(el));

    // Failsafe: never leave anything hidden for more than 2.5s.
    const failsafe = setTimeout(() => {
      elements.forEach((el) => el.classList.remove('is-hidden'));
    }, 2500);

    return () => {
      observer.disconnect();
      clearTimeout(failsafe);
    };
  }, []);

  return (
    <div className="landing-page">
      {/* Hero */}
      <section className="hero-band">
        <div className="hero-inner fade-on-scroll">
          <span className="hero-eyebrow">Neural Intelligence — Local &amp; Private</span>
          <h1 className="hero-headline">
            Precision Analysis<br />For Image &amp; Conversation
          </h1>
          <p className="hero-lede">
            Aura AI reads the craft in a photograph and the dynamics in a conversation.
            Engineered for creators who want the truth, rendered with restraint.
          </p>
          <div className="hero-actions">
            <Link to="/aesthetic-analyzer" className="btn btn-primary btn-lg">Analyze Images</Link>
            <Link to="/convo-decoder" className="btn btn-secondary btn-lg">Decode Conversations</Link>
          </div>

          <div className="hero-stats">
            <div className="stat">
              <div className="stat-number">99.9%</div>
              <div className="stat-label">Accuracy</div>
            </div>
            <div className="stat">
              <div className="stat-number">~3s</div>
              <div className="stat-label">Processing</div>
            </div>
            <div className="stat">
              <div className="stat-number">100%</div>
              <div className="stat-label">On-Device</div>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="capabilities">
        <div className="section-head fade-on-scroll">
          <span className="eyebrow">Capabilities</span>
          <h2 className="section-title">Two Instruments. One Discipline.</h2>
        </div>

        <div className="capability-grid">
          <article className="capability-card fade-on-scroll">
            <span className="capability-index">01</span>
            <h3 className="capability-title">Aesthetic Analysis</h3>
            <p className="capability-body">
              Computer-vision scoring of composition, colour harmony, lighting and technical
              quality — driven by a trained convolutional model, not guesswork.
            </p>
            <div className="capability-tags">
              <span className="tag">CNN</span>
              <span className="tag">Composition</span>
              <span className="tag">Colour</span>
            </div>
            <Link to="/aesthetic-analyzer" className="capability-link">Explore Analysis →</Link>
          </article>

          <article className="capability-card fade-on-scroll">
            <span className="capability-index">02</span>
            <h3 className="capability-title">Conversation Decoding</h3>
            <p className="capability-body">
              Real-time sentiment and engagement modelling of chat logs — interest level,
              reciprocity and momentum, read straight from the language.
            </p>
            <div className="capability-tags">
              <span className="tag">NLP</span>
              <span className="tag">Sentiment</span>
              <span className="tag">Engagement</span>
            </div>
            <Link to="/convo-decoder" className="capability-link">Decode Messages →</Link>
          </article>
        </div>
      </section>

      {/* Principles */}
      <section className="principles">
        <div className="section-head fade-on-scroll">
          <span className="eyebrow">Engineering</span>
          <h2 className="section-title">Built On Restraint</h2>
        </div>
        <div className="principle-grid">
          <div className="principle fade-on-scroll">
            <h4 className="principle-title">Deep Learning</h4>
            <p className="principle-body">Trained neural architectures, running on local hardware.</p>
          </div>
          <div className="principle fade-on-scroll">
            <h4 className="principle-title">Computer Vision</h4>
            <p className="principle-body">State-of-the-art image analysis with measurable scoring.</p>
          </div>
          <div className="principle fade-on-scroll">
            <h4 className="principle-title">Language Models</h4>
            <p className="principle-body">Context-aware sentiment and conversational dynamics.</p>
          </div>
          <div className="principle fade-on-scroll">
            <h4 className="principle-title">Privacy First</h4>
            <p className="principle-body">Your data stays local. Nothing stored, nothing shared.</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-band fade-on-scroll">
        <h2 className="cta-headline">Begin The Analysis</h2>
        <Link to="/aesthetic-analyzer" className="btn btn-primary btn-lg">Get Started</Link>
      </section>
    </div>
  );
};

export default LandingPage;
