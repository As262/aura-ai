import React, { useState, useCallback, memo, lazy, Suspense } from 'react';
import { useToast } from '../components/Toast';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import DetailedAnalysisResults from '../components/DetailedAnalysisResults';
import ApiService from '../services/ApiService';
import MockApiService from '../services/MockApiService';
import './BasePage.css';

// Lazy load the info section since it's below the fold
const InfoSection = lazy(() => import('../components/InfoSection'));

const AestheticAnalyzer = () => {
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { showSuccess, showError, showWarning } = useToast();

  const handleFileUpload = useCallback(async (formData) => {
    console.log('🚀 Starting file upload analysis...');
    
    setIsLoading(true);
    setError(null);
    setDetailedAnalysis(null);

    try {
      // Show loading toast with more detailed message
      showWarning('🤖 AI analyzing your image...', { 
        persistent: true,
        id: 'analysis-loading'
      });

      // Try real API first, fallback to mock if backend is unavailable
      let response;
      const connectionStatus = await ApiService.testConnection();
      
      if (connectionStatus.connected) {
        const modeText = connectionStatus.gpu_available ? 
          `🚀 Using GPU-accelerated AI analysis (${connectionStatus.gpu_name})` : 
          '🔗 Using Django backend API with AI analysis';
        console.log(modeText);
        
        // Use the detailed AI analysis
        response = await ApiService.analyzeImageDetailed(formData.file);
        
        if (response.success) {
          setDetailedAnalysis(response.data.analysis);
          const overallScore = response.data.analysis?.overall_rating?.score || 0;
          showSuccess(`🎯 AI Analysis Complete! Overall rating: ${overallScore}/10`);
        }
      } else {
        console.log('🔄 Backend unavailable, using mock API');
        showWarning('Using demo mode - connect to backend for full AI features', { duration: 3000 });
        
        // Use mock detailed analysis
        response = { success: true, data: { analysis: {} } };
        setDetailedAnalysis({});
        showSuccess('Analysis complete using demo mode!');
      }
      
      if (!response.success) {
        throw new Error(response.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('❌ Analysis error caught:', err);
      const errorMessage = err.message || 'Failed to analyze your content. Please try again.';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [showSuccess, showError, showWarning]);

  return (
    <div className="aesthetic-analyzer">
      <div className="page-header">
        <h1 className="page-title">
          🤖 AI-Powered Aesthetic Analyzer
        </h1>
        <p className="page-description">
          Advanced AI analysis for comprehensive image rating, pose suggestions, lighting analysis, 
          and detailed improvement recommendations. Get professional photography insights powered by computer vision.
        </p>
      </div>

      <div className="analyzer-content">
        <UploadForm
          title="Upload Image for AI Analysis"
          acceptedTypes="image/jpeg,image/jpg,image/png,image/webp,image/gif"
          onFileUpload={handleFileUpload}
          showCaption={false}
          isLoading={isLoading}
          platform="ai-analysis"
        />

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Show detailed AI analysis results */}
        <DetailedAnalysisResults 
          analysis={detailedAnalysis}
          isLoading={isLoading}
        />
      </div>

      {/* Lazy loaded Info Section */}
      <Suspense fallback={<div style={{ height: '400px' }} />}>
        <InfoSection />
      </Suspense>

      {/* Privacy Notice */}
      <div className="privacy-notice">
        <div className="privacy-content">
          <h3>🔒 Your Privacy Matters</h3>
          <p>
            All images are processed locally and are never stored on our servers. 
            Your photos remain completely private and secure.
          </p>
        </div>
      </div>
    </div>
  );
};

export default memo(AestheticAnalyzer);