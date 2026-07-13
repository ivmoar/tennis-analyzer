import React, { useState } from 'react';
import Navbar      from './components/Navbar';
import LandingPage from './pages/LandingPage';
import UploadPage  from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import AboutPage   from './pages/AboutPage';
import { demoResults } from './services/demoData';

function Footer() {
  return (
    <footer style={{
      background: '#1a1a18',
      color: '#888780',
      padding: '1.5rem 1.5rem',
      marginTop: 'auto',
    }}>
      <div style={{
        maxWidth: '1100px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        fontSize: '0.8rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1rem' }}>🎾</span>
          <span style={{ color: '#d3d1c7', fontWeight: '600' }}>Ivanalyze</span>
          <span>— TFE · Máster en IA · UNIR, 2026</span>
        </div>
        <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
          <span>Iván Moreno Aranda</span>
          <a
            href="https://github.com/ivmoar/tennis-analyzer"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#888780', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            ⌥ GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  const [results, setResults] = useState(null);
  const [isDemo,  setIsDemo]  = useState(false);
  const [page,    setPage]    = useState('landing');

  const handleNavigate = (dest) => {
    setResults(null);
    setIsDemo(false);
    setPage(dest);
  };

  const handleResults = (data) => {
    setResults(data);
    setIsDemo(false);
    setPage('results');
  };

  const handleDemo = () => {
    setResults(demoResults);
    setIsDemo(true);
    setPage('results');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar page={results ? 'results' : page} onNavigate={handleNavigate} />
      <div style={{ flex: 1 }}>
        {results
          ? <ResultsPage results={results} isDemo={isDemo} onReset={() => handleNavigate('upload')} />
          : page === 'about'
          ? <AboutPage />
          : page === 'upload'
          ? <UploadPage onResults={handleResults} />
          : <LandingPage onStart={() => handleNavigate('upload')} onAbout={() => handleNavigate('about')} onDemo={handleDemo} />
        }
      </div>
      <Footer />
    </div>
  );
}
