import React, { useState, useCallback, memo, lazy, Suspense } from 'react';
import { useToast } from '../components/Toast';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import ApiService from '../services/ApiService';
import MockApiService from '../services/MockApiService';
import './AestheticAnalyzer.css';

// Lazy load the info section since it's below the fold
const InfoSection = lazy(() => import('../components/InfoSection'));

const AestheticAnalyzer = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { showSuccess, showError, showWarning } = useToast();

  const handleFileUpload = useCallback(async (formData) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // Show loading toast
      showWarning('Analyzing your content...', { 
        persistent: true,
        id: 'analysis-loading'
      });

      // Try real API first, fallback to mock if backend is unavailable
      let response;
      const backendAvailable = await ApiService.testConnection();
      
      if (backendAvailable) {
        console.log('🔗 Using Django backend API');
        response = await ApiService.analyzeAesthetic(
          formData.file, 
          formData.caption, 
          'instagram'
        );
      } else {
        console.log('🔄 Backend unavailable, using mock API');
        showWarning('Using demo mode - connect to backend for full features', { duration: 3000 });
        response = await MockApiService.analyzeAesthetic(
          formData.file, 
          formData.caption, 
          'instagram'
        );
      }
      
      if (response.success) {
        setResults(response.data);
        const scoreText = response.data.aestheticScore || response.data.aesthetic_score || 'N/A';
        showSuccess(`Analysis complete! Your Instagram content scored ${scoreText}% aesthetic appeal.`);
      } else {
        throw new Error(response.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze your content. Please try again.');
      showError(err.message || 'Failed to analyze your content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [showSuccess, showError, showWarning]);

  return (
    <div className="aesthetic-analyzer">
      <div className="page-header">
        <h1 className="page-title">
          📸 Aesthetic Analyzer
        </h1>
        <p className="page-description">
          Upload your Instagram posts and discover your unique aesthetic signature, 
          visual style, and the vibes you project on Instagram. Get personalized insights 
          to enhance your Instagram presence.
        </p>
      </div>

      <div className="analyzer-content">
        <UploadForm
          title="Upload Your Instagram Post"
          acceptedTypes="image/*"
          onFileUpload={handleFileUpload}
          showCaption={true}
          isLoading={isLoading}
          platform="instagram"
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

      {/* Lazy loaded Info Section */}
      <Suspense fallback={<div style={{ height: '400px' }} />}>
        <InfoSection />
      </Suspense>
    </div>
  );
};

export default memo(AestheticAnalyzer);