import React, { useState, useEffect } from 'react';
import ApiService from '../services/ApiService';
import './ConnectionStatus.css';

const ConnectionStatus = () => {
  const [isConnected, setIsConnected] = useState(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    setIsChecking(true);
    try {
      const connected = await ApiService.testConnection();
      setIsConnected(connected);
    } catch (error) {
      setIsConnected(false);
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

  return (
    <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
      <div className="status-indicator">
        {isConnected ? '🟢' : '🔴'}
      </div>
      <span>
        {isConnected ? 'Backend Connected' : 'Demo Mode'}
      </span>
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