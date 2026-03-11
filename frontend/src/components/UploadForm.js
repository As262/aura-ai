import React, { useState, useCallback, useEffect } from 'react';
import FileValidator from '../utils/FileValidator';
import './UploadForm.css';

const UploadForm = ({ 
  title, 
  acceptedTypes, 
  onFileUpload, 
  showCaption = false, 
  isLoading = false,
  platform = 'instagram',
  shouldClearPreview = false,
  onPreviewCleared,
  children 
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [caption, setCaption] = useState('');
  const [validationErrors, setValidationErrors] = useState([]);
  const [validationWarnings, setValidationWarnings] = useState([]);
  const [isValidating, setIsValidating] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  // Helper function for validation options
  const getValidationOptions = (platform, acceptedTypes) => {
    // Parse accepted types to determine category
    let category = 'default';
    if (acceptedTypes.includes('image/')) category = 'image';
    else if (acceptedTypes.includes('video/')) category = 'video';
    else if (acceptedTypes.includes('text/')) category = 'text';
    else if (platform === 'conversation-analysis' || acceptedTypes.includes('.txt') || acceptedTypes.includes('.log')) category = 'conversation';

    // Platform-specific size limits
    const platformSizeLimits = {
      instagram: { image: 8 * 1024 * 1024, video: 50 * 1024 * 1024 },
      tiktok: { video: 75 * 1024 * 1024 },
      twitter: { image: 5 * 1024 * 1024, video: 512 * 1024 * 1024 },
      youtube: { video: 256 * 1024 * 1024 * 1024 }, // 256GB
      snapchat: { image: 5 * 1024 * 1024, video: 60 * 1024 * 1024 },
      linkedin: { image: 8 * 1024 * 1024, video: 75 * 1024 * 1024 },
      facebook: { image: 10 * 1024 * 1024, video: 1024 * 1024 * 1024 },
      pinterest: { image: 10 * 1024 * 1024 },
      'ai-analysis': { image: 15 * 1024 * 1024 }, // 15MB for detailed AI analysis
      'conversation-analysis': { conversation: 10 * 1024 * 1024 } // 10MB for conversation files
    };

    const maxSize = platformSizeLimits[platform]?.[category] || FileValidator.MAX_SIZES[category];

    return {
      category,
      maxSize,
      allowedTypes: acceptedTypes ? acceptedTypes.split(',').map(t => t.trim()) : null
    };
  };

  const handleFiles = useCallback(async (file) => {
    // Clear previous validation messages
    setValidationErrors([]);
    setValidationWarnings([]);
    setIsValidating(true);

    try {
      // Determine validation options based on platform and accepted types
      const validationOptions = getValidationOptions(platform, acceptedTypes);
      
      // Basic synchronous validation
      const basicValidation = FileValidator.validateFile(file, validationOptions);
      
      if (!basicValidation.isValid) {
        setValidationErrors(basicValidation.errors);
        setValidationWarnings(basicValidation.warnings);
        setIsValidating(false);
        return;
      }

      // Advanced asynchronous validation
      const advancedValidation = await FileValidator.validateFileContentAdvanced(file);
      
      if (!advancedValidation.isValid) {
        setValidationErrors([...basicValidation.errors, ...advancedValidation.errors]);
        setValidationWarnings([...basicValidation.warnings, ...advancedValidation.warnings]);
        setIsValidating(false);
        return;
      }

      // Set any warnings
      if (basicValidation.warnings.length > 0 || advancedValidation.warnings.length > 0) {
        setValidationWarnings([...basicValidation.warnings, ...advancedValidation.warnings]);
      }

      // Create preview URL for images
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
        setUploadedFile(file);
      }

      // File is valid, proceed with upload
      const formData = {
        file: file,
        caption: showCaption ? caption.trim() : null,
        platform: platform,
        sanitizedFileName: FileValidator.sanitizeFileName(file.name)
      };
      
      onFileUpload(formData);
    } catch (error) {
      setValidationErrors([`Validation failed: ${error.message}`]);
    } finally {
      setIsValidating(false);
    }
  }, [onFileUpload, platform, acceptedTypes, showCaption, caption]);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files[0]);
    }
  }, [handleFiles]);

  const handleChange = useCallback((e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files[0]);
    }
  }, [handleFiles]);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Form submission logic can be added here if needed
  };

  // Clean up preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Clear preview when parent requests it
  useEffect(() => {
    if (shouldClearPreview) {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(null);
      setUploadedFile(null);
      setValidationErrors([]);
      setValidationWarnings([]);
      if (onPreviewCleared) {
        onPreviewCleared();
      }
    }
  }, [shouldClearPreview, previewUrl, onPreviewCleared]);

  return (
    <div className="upload-form">
      <h2 className="upload-title">{title}</h2>
      
      <form onSubmit={handleSubmit} className="upload-container">
        <div 
          className={`upload-area ${dragActive ? 'drag-active' : ''} ${isLoading ? 'loading' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="file-input"
            accept={acceptedTypes}
            onChange={handleChange}
            disabled={isLoading}
          />
          
          <label htmlFor="file-upload" className="upload-label">
            {previewUrl ? (
              <div className="preview-container">
                <img src={previewUrl} alt="Preview" className="preview-image" />
                <div className="preview-overlay">
                  <p className="preview-text">Click to change image</p>
                  {uploadedFile && <p className="file-name">{uploadedFile.name}</p>}
                </div>
              </div>
            ) : (
              <>
                <div className="upload-icon">
                  📁
                </div>
                <div className="upload-text">
                  <h3>Drop your file here or click to browse</h3>
                  <p>Accepted formats: {acceptedTypes}</p>
                  <p className="platform-info">
                    {platform === 'ai-analysis' ? ' AI Analysis Mode' : `Platform: ${platform}`}
                  </p>
                </div>
              </>
            )}
          </label>
          
          {(isLoading || isValidating) && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>{isValidating ? 'Validating file...' : 'Processing your file...'}</p>
            </div>
          )}
        </div>

        {/* Validation Messages */}
        {validationErrors.length > 0 && (
          <div className="validation-messages error-messages" role="alert" aria-live="polite">
            <h4>❌ File Validation Errors:</h4>
            <ul>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {validationWarnings.length > 0 && (
          <div className="validation-messages warning-messages" role="alert" aria-live="polite">
            <h4>⚠️ File Validation Warnings:</h4>
            <ul>
              {validationWarnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
        
        {showCaption && (
          <div className="caption-section">
            <label htmlFor="caption" className="caption-label">
              Caption (optional)
            </label>
            <textarea
              id="caption"
              className="caption-input"
              placeholder="Enter your Instagram caption here..."
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={4}
              disabled={isLoading}
            />
          </div>
        )}
        
        {children}
      </form>
    </div>
  );
};

export default UploadForm;