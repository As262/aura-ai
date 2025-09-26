import React, { useState, useEffect } from 'react';
import ApiService from '../services/ApiService';
import './ConnectionStatus.css';

const ConnectionStatus = () => {
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    setIsChecking(true);
    try {
      const status = await ApiService.testConnection();
      setConnectionStatus(status);
    } catch (error) {
      setConnectionStatus({ connected: false, gpu_available: false });
    } finally {
      setIsChecking(false);
    }
  };

  if (isChecking) {
    return (
      <div className="connection-status checking">
        <div className="status-indicator">⚡</div>
        <span>Checking connection...</span>
      </div>
    );
  }

  const getStatusText = () => {
    if (!connectionStatus?.connected) {
      return 'Demo Mode';
    }
    
    if (connectionStatus.gpu_available) {
      return `🚀 GPU Mode - ${connectionStatus.gpu_name || 'GPU Enabled'}`;
    }
    
    return 'CPU Mode';
  };

  const getStatusClass = () => {
    if (!connectionStatus?.connected) return 'disconnected';
    return connectionStatus.gpu_available ? 'gpu-enabled' : 'connected';
  };

  return (
    <div className={`connection-status ${getStatusClass()}`}>
      <div className="status-indicator">
        {!connectionStatus?.connected ? '�' : 
         connectionStatus.gpu_available ? '⚡' : '�'}
      </div>
      <span>
        {getStatusText()}
      </span>
      {connectionStatus?.gpu_memory && (
        <span className="gpu-memory">({connectionStatus.gpu_memory})</span>
      )}
      <button 
        className="refresh-btn" 
        onClick={checkConnection}
        title="Refresh connection status"
      >
        🔄
      </button>
    </div>
  );
};

export default ConnectionStatus;