import React, { useState } from 'react';
import Navbar      from './components/Navbar';
import LandingPage from './pages/LandingPage';
import UploadPage  from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import AboutPage   from './pages/AboutPage';
import { demoResults } from './services/demoData';

export default function App() {
  const [results, setResults] = useState(null);
  const [page,    setPage]    = useState('landing');

  const handleNavigate = (dest) => {
    setResults(null);
    setPage(dest);
  };

  const handleResults = (data) => {
    setResults(data);
    setPage('results');
  };

  const handleDemo = () => {
    setResults(demoResults);
    setPage('results');
  };

  return (
    <>
      <Navbar page={results ? 'results' : page} onNavigate={handleNavigate} />
      {results
        ? <ResultsPage results={results} onReset={() => handleNavigate('upload')} />
        : page === 'about'
        ? <AboutPage />
        : page === 'upload'
        ? <UploadPage onResults={handleResults} />
        : <LandingPage onStart={() => handleNavigate('upload')} onAbout={() => handleNavigate('about')} onDemo={handleDemo} />
      }
    </>
  );
}
