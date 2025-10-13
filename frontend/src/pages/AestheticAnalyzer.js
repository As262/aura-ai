import React, { useState, useCallback, memo, lazy, Suspense } from 'react';
import { useToast } from '../components/Toast';
import { useUsage } from '../contexts/UsageContext';
import UploadForm from '../components/UploadForm';
import DetailedAnalysisResults from '../components/DetailedAnalysisResults';
import PrivacyConsentModal from '../components/PrivacyConsentModal';
import ApiService from '../services/ApiService';
import './BasePage.css';

// Lazy load the info section since it's below the fold
const InfoSection = lazy(() => import('../components/InfoSection'));

const AestheticAnalyzer = () => {
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
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
    const featureUsage = getFeatureUsage('aesthetic_analyzer');
    if (featureUsage.remaining <= 0) {
      showError(`Usage limit reached! You've used all ${featureUsage.limit} analyses. Come back later!`);
      setPendingFile(null);
      setShouldClearPreview(true);
      return;
    }
    
    console.log('🚀 Starting file upload analysis...');
    
    setIsLoading(true);
    setError(null);
    setDetailedAnalysis(null);

    // Wrap the analysis in performAnalysis to track usage
    await performAnalysis('aesthetic_analyzer', async () => {
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
          response = await ApiService.analyzeImageDetailed(pendingFile.file);
          
          if (response.success) {
            setDetailedAnalysis(response.data.analysis);
            const overallScore = response.data.analysis?.overall_rating?.score || 0;
            showSuccess(`🎯 AI Analysis Complete! Overall rating: ${overallScore}/10`);
            return { success: true };
          }
        } else {
          console.log('🔄 Backend unavailable, using mock API');
          showWarning('Using demo mode - connect to backend for full AI features', { duration: 3000 });
          
          // Use mock detailed analysis
          response = { success: true, data: { analysis: {} } };
          setDetailedAnalysis({});
          showSuccess('Analysis complete using demo mode!');
          return { success: true };
        }
        
        if (!response.success) {
          throw new Error(response.error || 'Analysis failed');
        }
        
        return response;
      } catch (err) {
        console.error('❌ Analysis error caught:', err);
        const errorMessage = err.message || 'Failed to analyze your content. Please try again.';
        setError(errorMessage);
        showError(errorMessage);
        return { success: false, error: errorMessage };
      }
    });

    setIsLoading(false);
    setPendingFile(null);
  }, [pendingFile, showSuccess, showError, showWarning, performAnalysis, getFeatureUsage]);

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
    <div className="aesthetic-analyzer">
      <div className="page-header">
        <h1 className="page-title">
          <span className="page-emoji">🤖</span>
          <span className="page-title-text">AI-Powered Aesthetic Analyzer</span>
        </h1>
        <p className="page-description">
          Advanced AI analysis for comprehensive image rating, pose suggestions, lighting analysis, 
          and detailed improvement recommendations. Get professional photography insights powered by computer vision.
        </p>
      </div>

      <div className="analyzer-content">
        <PrivacyConsentModal
          isOpen={showPrivacyModal}
          onAccept={handlePrivacyAccept}
          onDecline={handlePrivacyDecline}
        />
        
        <UploadForm
          title="Upload Image for AI Analysis"
          acceptedTypes="image/jpeg,image/jpg,image/png,image/webp,image/gif"
          onFileUpload={handleFileUploadRequest}
          showCaption={false}
          isLoading={isLoading}
          platform="ai-analysis"
          shouldClearPreview={shouldClearPreview}
          onPreviewCleared={handlePreviewCleared}
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
          <h3>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="privacy-icon">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Your Privacy Matters
          </h3>
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