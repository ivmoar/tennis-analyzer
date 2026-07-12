import React from 'react';

export default function Navbar({ page, onNavigate }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-logo" onClick={() => onNavigate('landing')} role="button" tabIndex={0}>
          <div className="navbar-logo-icon">🎾</div>
          <div className="navbar-logo-text">
            <span className="navbar-logo-name">Ivanalyze</span>
            <span className="navbar-logo-sub">Análisis biomecánico con IA</span>
          </div>
        </div>

        <div className="navbar-links">
          <button
            className={`navbar-link ${page === 'upload' || page === 'results' ? 'active' : ''}`}
            onClick={() => onNavigate('upload')}
          >
            Analizar
          </button>
          <button
            className={`navbar-link ${page === 'about' ? 'active' : ''}`}
            onClick={() => onNavigate('about')}
          >
            Cómo funciona
          </button>
          <span className="navbar-badge">UNIR · TFE 2026</span>
        </div>
      </div>
    </nav>
  );
}
