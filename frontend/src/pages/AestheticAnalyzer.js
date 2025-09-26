import React, { useState, useCallback, memo, lazy, Suspense } from 'react';
import { useToast } from '../components/Toast';
import UploadForm from '../components/UploadForm';
import ResultPanel from '../components/ResultPanel';
import DetailedAnalysisResults from '../components/DetailedAnalysisResults';
import ApiService from '../services/ApiService';
import MockApiService from '../services/MockApiService';
import './AestheticAnalyzer.css';

// Lazy load the info section since it's below the fold
const InfoSection = lazy(() => import('../components/InfoSection'));

const AestheticAnalyzer = () => {
  const [results, setResults] = useState(null);
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisMode, setAnalysisMode] = useState('detailed'); // 'basic' or 'detailed'
  const { showSuccess, showError, showWarning } = useToast();

  const handleFileUpload = useCallback(async (formData) => {
    setIsLoading(true);
    setError(null);
    setResults(null);
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
        
        if (analysisMode === 'detailed') {
          // Use the new detailed AI analysis
          response = await ApiService.analyzeImageDetailed(formData.file);
          
          if (response.success) {
            setDetailedAnalysis(response.data.analysis);
            const overallScore = response.data.analysis?.overall_rating?.score || 0;
            showSuccess(`🎯 AI Analysis Complete! Overall rating: ${overallScore}/10`);
          }
        } else {
          // Use basic aesthetic analysis
          response = await ApiService.analyzeAesthetic(
            formData.file, 
            formData.caption, 
            'instagram'
          );
          
          if (response.success) {
            setResults(response.data);
            const scoreText = response.data.aestheticScore || response.data.aesthetic_score || 'N/A';
            showSuccess(`Analysis complete! Your Instagram content scored ${scoreText}% aesthetic appeal.`);
          }
        }
      } else {
        console.log('🔄 Backend unavailable, using mock API');
        showWarning('Using demo mode - connect to backend for full AI features', { duration: 3000 });
        response = await MockApiService.analyzeAesthetic(
          formData.file, 
          formData.caption, 
          'instagram'
        );
        
        if (response.success) {
          setResults(response.data);
          const scoreText = response.data.aestheticScore || response.data.aesthetic_score || 'N/A';
          showSuccess(`Demo analysis complete! Your content scored ${scoreText}% aesthetic appeal.`);
        }
      }
      
      if (!response.success) {
        throw new Error(response.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze your content. Please try again.');
      showError(err.message || 'Failed to analyze your content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [analysisMode, showSuccess, showError, showWarning]);

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
        
        {/* Analysis Mode Toggle */}
        <div className="analysis-mode-toggle">
          <button 
            className={`mode-btn ${analysisMode === 'detailed' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('detailed')}
          >
            🎯 AI Analysis
            <span className="mode-desc">Detailed ratings & suggestions</span>
          </button>
          <button 
            className={`mode-btn ${analysisMode === 'basic' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('basic')}
          >
            📱 Social Media
            <span className="mode-desc">Instagram-focused analysis</span>
          </button>
        </div>
      </div>

      <div className="analyzer-content">
        <UploadForm
          title={analysisMode === 'detailed' ? "Upload Image for AI Analysis" : "Upload Your Instagram Post"}
          acceptedTypes="image/jpeg,image/jpg,image/png,image/webp,image/gif"
          onFileUpload={handleFileUpload}
          showCaption={analysisMode === 'basic'}
          isLoading={isLoading}
          platform={analysisMode === 'detailed' ? 'ai-analysis' : 'instagram'}
        />

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Show detailed AI analysis results */}
        {analysisMode === 'detailed' && (
          <DetailedAnalysisResults 
            analysis={detailedAnalysis}
            isLoading={isLoading}
          />
        )}

        {/* Show basic social media analysis results */}
        {analysisMode === 'basic' && (
          <ResultPanel
            title="Your Aesthetic Analysis"
            results={results}
            isVisible={!!results && !isLoading}
          />
        )}
      </div>

      {/* Lazy loaded Info Section */}
      <Suspense fallback={<div style={{ height: '400px' }} />}>
        <InfoSection />
      </Suspense>
    </div>
  );
};

export default memo(AestheticAnalyzer);