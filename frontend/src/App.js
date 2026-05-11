import React, { useState } from 'react';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';

export default function App() {
  const [results, setResults] = useState(null);

  return results
    ? <ResultsPage results={results} onReset={() => setResults(null)} />
    : <UploadPage  onResults={setResults} />;
}
