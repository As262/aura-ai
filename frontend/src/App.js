import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import Header from './components/Header';
import Footer from './components/Footer';
import ConnectionStatus from './components/ConnectionStatus';
import LandingPage from './pages/LandingPage';
import AestheticAnalyzer from './pages/AestheticAnalyzer';
import ConvoDecoder from './pages/ConvoDecoder';
import Auth from './pages/Auth';
import './App.css';

function App() {
  return (
    <ErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <Router>
              <div className="App">
                <Header />
                <ConnectionStatus />
                <main className="main-content">
                  <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route 
                      path="/aesthetic-analyzer" 
                      element={
                        <ErrorBoundary>
                          <AestheticAnalyzer />
                        </ErrorBoundary>
                      } 
                    />
                    <Route 
                      path="/convo-decoder" 
                      element={
                        <ErrorBoundary>
                          <ConvoDecoder />
                        </ErrorBoundary>
                      } 
                    />
                    <Route path="/login" element={<Auth />} />
                    <Route path="/signup" element={<Auth />} />
                  </Routes>
                </main>
                <Footer />
              </div>
            </Router>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
