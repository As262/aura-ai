import React from 'react';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { 
      hasError: true,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log error to external service in production
    if (process.env.NODE_ENV === 'production') {
      this.logErrorToService(error, errorInfo);
    }
  }

  logErrorToService = (error, errorInfo) => {
    // Mock error logging service
    const errorReport = {
      id: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // In a real app, send to error tracking service (Sentry, LogRocket, etc.)
    console.log('Error logged to service:', errorReport);
  };

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom error UI
      const { customFallback: CustomFallback, showDetails = false } = this.props;
      
      if (CustomFallback) {
        return (
          <CustomFallback 
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            onRetry={this.handleRetry}
            onReload={this.handleReload}
          />
        );
      }

      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" strokeWidth="2"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </div>
            
            <h2>Something went wrong</h2>
            <p>We apologize for the inconvenience. An unexpected error has occurred.</p>
            
            {showDetails && this.state.error && (
              <details className="error-details">
                <summary>Error Details (Debug Mode)</summary>
                <div className="error-info">
                  <p><strong>Error ID:</strong> {this.state.errorId}</p>
                  <p><strong>Message:</strong> {this.state.error.message}</p>
                  <pre className="error-stack">{this.state.error.stack}</pre>
                  {this.state.errorInfo?.componentStack && (
                    <pre className="component-stack">{this.state.errorInfo.componentStack}</pre>
                  )}
                </div>
              </details>
            )}
            
            <div className="error-actions">
              <button 
                onClick={this.handleRetry} 
                className="btn btn-primary"
                aria-label="Try again"
              >
                Try Again
              </button>
              <button 
                onClick={this.handleReload} 
                className="btn btn-secondary"
                aria-label="Reload page"
              >
                Reload Page
              </button>
            </div>
            
            <div className="error-help">
              <p>If this problem persists, please:</p>
              <ul>
                <li>Check your internet connection</li>
                <li>Clear your browser cache and cookies</li>
                <li>Try using a different browser</li>
                <li>Contact support with error ID: <code>{this.state.errorId}</code></li>
              </ul>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easier usage
export const withErrorBoundary = (Component, errorBoundaryConfig = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryConfig}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

// Hook for manual error handling
export const useErrorHandler = () => {
  const handleError = (error, errorInfo = {}) => {
    // Create an error boundary-like behavior for functional components
    console.error('Manual error handler:', error, errorInfo);
    
    // In production, log to external service
    if (process.env.NODE_ENV === 'production') {
      const errorReport = {
        id: Date.now().toString(36) + Math.random().toString(36).substr(2),
        message: error.message,
        stack: error.stack,
        ...errorInfo,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };
      
      console.log('Error logged to service:', errorReport);
    }
  };

  return { handleError };
};

export default ErrorBoundary;