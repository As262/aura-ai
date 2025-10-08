import React, { useState } from 'react';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import ApiService from '../services/ApiService';
import MockApiService from '../services/MockApiService';
import './BasePage.css';

const ConvoDecoder = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (formData) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // Try real API first, fallback to mock if backend is unavailable
      let response;
      const backendAvailable = await ApiService.testConnection();
      
      if (backendAvailable) {
        console.log('🔗 Using Django backend API');
        response = await ApiService.analyzeConversation(formData.file);
      } else {
        console.log('🔄 Backend unavailable, using mock API');
        response = await MockApiService.analyzeConversation(formData.file);
      }
      
      if (response.success) {
        setResults(response.data);
      } else {
        throw new Error(response.error || 'Analysis failed');
      }
    } catch (err) {
      setError('Failed to analyze your conversation. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

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
        <UploadForm
          title="Upload Your Chat Log"
          acceptedTypes=".txt,.json,.csv,.log"
          onFileUpload={handleFileUpload}
          showCaption={false}
          isLoading={isLoading}
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