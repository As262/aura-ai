import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { UsageProvider } from './contexts/UsageContext';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import Header from './components/Header';
import Footer from './components/Footer';
import ConnectionStatus from './components/ConnectionStatus';
import ScrollToTop from './components/ScrollToTop';
import LandingPage from './pages/LandingPage';
import AestheticAnalyzer from './pages/AestheticAnalyzer';
import ConvoDecoder from './pages/ConvoDecoder';
import Pricing from './pages/Pricing';
import UsageDebugPage from './pages/UsageDebugPage';
import './App.css';
import './styles/bugatti-overrides.css';

function App() {
  return (
    <ErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
      <ThemeProvider>
        <ToastProvider>
          <UsageProvider>
          <Router>
            <div className="App">
              <Header />
              <ScrollToTop />
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
                  <Route 
                    path="/pricing" 
                    element={
                      <ErrorBoundary>
                        <Pricing />
                      </ErrorBoundary>
                    } 
                  />
                  <Route 
                    path="/usage-debug" 
                    element={
                      <ErrorBoundary>
                        <UsageDebugPage />
                      </ErrorBoundary>
                    } 
                  />
                </Routes>
              </main>
              <Footer />
            </div>
          </Router>
          </UsageProvider>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
