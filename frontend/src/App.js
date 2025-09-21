import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import AestheticAnalyzer from './pages/AestheticAnalyzer';
import ConvoDecoder from './pages/ConvoDecoder';
import Auth from './pages/Auth';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <div className="App">
            <Header />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/aesthetic-analyzer" element={<AestheticAnalyzer />} />
                <Route path="/convo-decoder" element={<ConvoDecoder />} />
                <Route path="/login" element={<Auth />} />
                <Route path="/signup" element={<Auth />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
