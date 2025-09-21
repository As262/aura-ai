import React, { useState } from 'react';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import MockApiService from '../services/MockApiService';
import './AestheticAnalyzer.css';

const AestheticAnalyzer = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (formData) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // Use mock API service
      const response = await MockApiService.analyzeAesthetic(formData.file, formData.caption);
      
      if (response.success) {
        setResults(response.data);
      } else {
        throw new Error('Analysis failed');
      }
    } catch (err) {
      setError('Failed to analyze your content. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="aesthetic-analyzer">
      <div className="page-header">
        <h1 className="page-title">
          🎨 Aesthetic Analyzer
        </h1>
        <p className="page-description">
          Upload your Instagram image and caption to discover your unique aesthetic signature, 
          visual style, and the vibes you project to the world.
        </p>
      </div>

      <div className="analyzer-content">
        <UploadForm
          title="Upload Your Instagram Post"
          acceptedTypes="image/*"
          onFileUpload={handleFileUpload}
          showCaption={true}
          isLoading={isLoading}
        />

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <ResultPanel
          title="Your Aesthetic Analysis"
          results={results}
          isVisible={!!results && !isLoading}
        />
      </div>

      {/* Info Section */}
      <div className="info-section">
        <h2 className="info-title">What We Analyze</h2>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-icon">🎯</div>
            <h3>Aesthetic Score</h3>
            <p>Overall visual appeal and aesthetic consistency rating</p>
          </div>
          <div className="info-card">
            <div className="info-icon">💬</div>
            <h3>Caption Tone</h3>
            <p>Emotional tone and personality reflected in your captions</p>
          </div>
          <div className="info-card">
            <div className="info-icon">#️⃣</div>
            <h3>Hashtag Strategy</h3>
            <p>Optimized hashtag suggestions based on your content style</p>
          </div>
          <div className="info-card">
            <div className="info-icon">🎨</div>
            <h3>Visual Style</h3>
            <p>Your dominant aesthetic theme and visual preferences</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AestheticAnalyzer;