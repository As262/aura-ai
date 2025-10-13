import React, { useState, useCallback } from 'react';
import { useUsage } from '../contexts/UsageContext';
import { useToast } from '../components/Toast';
import './Pricing.css';

const Pricing = () => {
  const { getFeatureUsage, addUses } = useUsage();
  const { showSuccess, showWarning } = useToast();
  const [selectedFeature, setSelectedFeature] = useState('aesthetic_analyzer');
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Get current usage for selected feature
  const currentUsage = getFeatureUsage(selectedFeature);

  // Pricing plans (in Indian Rupees)
  const plans = {
    aesthetic_analyzer: [
      { id: 'basic', uses: 10, price: 399, popular: false },
      { id: 'standard', uses: 25, price: 799, popular: true },
      { id: 'premium', uses: 50, price: 1499, popular: false }
    ],
    convo_decoder: [
      { id: 'basic', uses: 30, price: 399, popular: false },
      { id: 'standard', uses: 75, price: 799, popular: true },
      { id: 'premium', uses: 150, price: 1499, popular: false }
    ]
  };

  const handlePurchase = useCallback(async (plan) => {
    setIsProcessing(true);
    setSelectedPlan(plan.id);

    // Simulate payment processing
    showWarning('Processing payment...', { duration: 2000 });

    setTimeout(() => {
      // Add uses to the selected feature (in real app, this would be handled by backend)
      addUses(selectedFeature, plan.uses);
      
      showSuccess(`🎉 Success! Added ${plan.uses} uses to ${selectedFeature === 'aesthetic_analyzer' ? 'Aesthetic Analyzer' : 'Convo Decoder'}!`);
      setIsProcessing(false);
      setSelectedPlan(null);
    }, 2000);
  }, [selectedFeature, addUses, showSuccess, showWarning]);

  const featureName = selectedFeature === 'aesthetic_analyzer' ? 'Aesthetic Analyzer' : 'Convo Decoder';

  return (
    <div className="pricing-page">
      <div className="pricing-header">
        <h1 className="pricing-title">
          <span className="title-icon"></span>
          Upgrade Your Usage
        </h1>
        <p className="pricing-description">
          Get more analyses and unlock the full potential of our AI-powered tools. 
          Choose the plan that works best for you.
        </p>
      </div>

      {/* Feature Selector */}
      <div className="feature-selector">
        <button
          className={`feature-tab ${selectedFeature === 'aesthetic_analyzer' ? 'active' : ''}`}
          onClick={() => setSelectedFeature('aesthetic_analyzer')}
        >
          <span className="tab-icon">🤖</span>
          <div className="tab-content">
            <span className="tab-title">Aesthetic Analyzer</span>
            <span className="tab-usage">
              {currentUsage.remaining}/{currentUsage.limit} uses left
            </span>
          </div>
        </button>
        <button
          className={`feature-tab ${selectedFeature === 'convo_decoder' ? 'active' : ''}`}
          onClick={() => setSelectedFeature('convo_decoder')}
        >
          <span className="tab-icon">💬</span>
          <div className="tab-content">
            <span className="tab-title">Convo Decoder</span>
            <span className="tab-usage">
              {getFeatureUsage('convo_decoder').remaining}/{getFeatureUsage('convo_decoder').limit} uses left
            </span>
          </div>
        </button>
      </div>

      {/* Current Usage Display */}
      <div className="current-usage-card">
        <div className="usage-info">
          <span className="usage-label">Current Usage for {featureName}</span>
          <div className="usage-stats">
            <div className="usage-stat">
              <span className="stat-value">{currentUsage.count}</span>
              <span className="stat-label">Used</span>
            </div>
            <div className="usage-divider">/</div>
            <div className="usage-stat">
              <span className="stat-value">{currentUsage.limit}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="usage-divider">•</div>
            <div className="usage-stat remaining">
              <span className="stat-value">{currentUsage.remaining}</span>
              <span className="stat-label">Remaining</span>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Plans */}
      <div className="pricing-grid">
        {plans[selectedFeature].map((plan) => (
          <div
            key={plan.id}
            className={`pricing-card ${plan.popular ? 'popular' : ''} ${selectedPlan === plan.id ? 'processing' : ''}`}
          >
            {plan.popular && <div className="popular-badge">Most Popular</div>}
            
            <div className="plan-header">
              <h3 className="plan-name">{plan.id.charAt(0).toUpperCase() + plan.id.slice(1)}</h3>
              <div className="plan-price">
                <span className="price-currency">₹</span>
                <span className="price-amount">{plan.price}</span>
              </div>
              <p className="plan-uses">
                {plan.uses === 999 ? 'Unlimited' : plan.uses} Uses
              </p>
            </div>

            <div className="plan-features">
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span className="feature-text">
                  {plan.uses === 999 ? 'Unlimited analyses' : `${plan.uses} AI analyses`}
                </span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span className="feature-text">Full feature access</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span className="feature-text">Priority processing</span>
              </div>
              {plan.id === 'unlimited' && (
                <>
                  <div className="feature-item">
                    <span className="feature-icon">✓</span>
                    <span className="feature-text">24/7 support</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">✓</span>
                    <span className="feature-text">Advanced insights</span>
                  </div>
                </>
              )}
            </div>

            <button
              className={`purchase-button ${isProcessing && selectedPlan === plan.id ? 'processing' : ''}`}
              onClick={() => handlePurchase(plan)}
              disabled={isProcessing}
            >
              {isProcessing && selectedPlan === plan.id ? (
                <>
                  <span className="processing-spinner"></span>
                  Processing...
                </>
              ) : (
                <>
                  Purchase Now
                  <span className="button-arrow">→</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Info Section */}
      <div className="pricing-info">
        <div className="info-card">
          <span className="info-icon">🔒</span>
          <h4>Secure Payment</h4>
          <p>All transactions are encrypted and secure</p>
        </div>
        <div className="info-card">
          <span className="info-icon">⚡</span>
          <h4>Instant Activation</h4>
          <p>Uses are added immediately after purchase</p>
        </div>
        <div className="info-card">
          <span className="info-icon">♻️</span>
          <h4>No Expiration</h4>
          <p>Your purchased uses never expire</p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
