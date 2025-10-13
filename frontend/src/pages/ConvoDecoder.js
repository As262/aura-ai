import React, { useState, useCallback } from 'react';
import { useToast } from '../components/Toast';
import { useUsage } from '../contexts/UsageContext';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import PrivacyConsentModal from '../components/PrivacyConsentModal';
import ApiService from '../services/ApiService';
import MockApiService from '../services/MockApiService';
import './BasePage.css';

const ConvoDecoder = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [shouldClearPreview, setShouldClearPreview] = useState(false);
  const { showSuccess, showError, showWarning } = useToast();
  const { performAnalysis, getFeatureUsage } = useUsage();

  const handleFileUploadRequest = useCallback((formData) => {
    // Show privacy consent modal first
    setPendingFile(formData);
    setShowPrivacyModal(true);
  }, []);

  const handlePrivacyAccept = useCallback(async () => {
    setShowPrivacyModal(false);
    
    if (!pendingFile) return;
    
    // Check usage limit first
    const featureUsage = getFeatureUsage('convo_decoder');
    if (featureUsage.remaining <= 0) {
      showError(`Usage limit reached! You've used all ${featureUsage.limit} analyses. Come back later!`);
      setPendingFile(null);
      setShouldClearPreview(true);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setResults(null);

    // Wrap the analysis in performAnalysis to track usage
    await performAnalysis('convo_decoder', async () => {
      try {
        showWarning('💬 Analyzing your conversation...', { 
          persistent: true,
          id: 'convo-loading'
        });

        // Try real API first, fallback to mock if backend is unavailable
        let response;
        const connectionStatus = await ApiService.testConnection();
        
        if (connectionStatus.connected) {
          console.log('🔗 Using Django backend API');
          response = await ApiService.analyzeConversation(pendingFile.file);
        } else {
          console.log('🔄 Backend unavailable, using mock API');
          showWarning('Using demo mode - connect to backend for full features', { duration: 3000 });
          response = await MockApiService.analyzeConversation(pendingFile.file);
        }
        
        if (response.success) {
          setResults(response.data);
          showSuccess('✅ Conversation analysis complete!');
          return { success: true };
        } else {
          throw new Error(response.error || 'Analysis failed');
        }
      } catch (err) {
        const errorMessage = 'Failed to analyze your conversation. Please try again.';
        setError(errorMessage);
        showError(errorMessage);
        console.error('Analysis error:', err);
        return { success: false, error: errorMessage };
      }
    });

    setIsLoading(false);
    setPendingFile(null);
  }, [pendingFile, performAnalysis, getFeatureUsage, showSuccess, showError, showWarning]);

  const handlePrivacyDecline = useCallback(() => {
    setShowPrivacyModal(false);
    setPendingFile(null);
    setShouldClearPreview(true);
    showWarning('Upload cancelled. Your privacy is important to us.');
  }, [showWarning]);

  const handlePreviewCleared = useCallback(() => {
    setShouldClearPreview(false);
  }, []);

  return (
    <div className="convo-decoder">
      <div className="page-header">
        <h1 className="page-title">
          💬 Convo Decoder
        </h1>
        <p className="page-description">
          Upload your chat logs to uncover your unique communication patterns, response style, 
          and how you connect with others in the digital world.
        </p>
      </div>

      <div className="analyzer-content">
        <PrivacyConsentModal
          isOpen={showPrivacyModal}
          onAccept={handlePrivacyAccept}
          onDecline={handlePrivacyDecline}
        />
        
        <UploadForm
          title="Upload Your Chat Log"
          acceptedTypes=".txt,.json,.csv,.log"
          onFileUpload={handleFileUploadRequest}
          showCaption={false}
          isLoading={isLoading}
          shouldClearPreview={shouldClearPreview}
          onPreviewCleared={handlePreviewCleared}
        />

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <ResultPanel
          title="Your Conversation Analysis"
          results={results}
          isVisible={!!results && !isLoading}
        />
      </div>

      {/* Info Section */}
      <div className="info-section">
        <h2 className="info-title">What We Decode</h2>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-icon">⏱️</div>
            <h3>Response Timing</h3>
            <p>How quickly you reply and your communication rhythm</p>
          </div>
          <div className="info-card">
            <div className="info-icon">⚖️</div>
            <h3>Conversation Balance</h3>
            <p>Whether you're a talker, listener, or perfectly balanced</p>
          </div>
          <div className="info-card">
            <div className="info-icon">🎭</div>
            <h3>Mood Patterns</h3>
            <p>Emotional tone and personality reflected in your messages</p>
          </div>
          <div className="info-card">
            <div className="info-icon">💕</div>
            <h3>Romantic Cues</h3>
            <p>Flirtation level and romantic interest indicators</p>
          </div>
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="privacy-notice">
        <div className="privacy-content">
          <h3>🔒 Your Privacy Matters</h3>
          <p>
            All chat logs are processed locally and are never stored on our servers. 
            Your conversations remain completely private and secure.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ConvoDecoder;