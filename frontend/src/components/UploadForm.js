import React, { useState } from 'react';
import './UploadForm.css';

const UploadForm = ({ 
  title, 
  acceptedTypes, 
  onFileUpload, 
  showCaption = false, 
  isLoading = false,
  children 
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [caption, setCaption] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files[0]);
    }
  };

  const handleFiles = (file) => {
    const formData = {
      file: file,
      caption: showCaption ? caption : null
    };
    onFileUpload(formData);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Form submission logic can be added here if needed
  };

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
            <div className="upload-icon">
              📁
            </div>
            <div className="upload-text">
              <h3>Drop your file here or click to browse</h3>
              <p>Accepted formats: {acceptedTypes}</p>
            </div>
          </label>
          
          {isLoading && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Processing your file...</p>
            </div>
          )}
        </div>
        
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