import React from 'react';
import ScoreGauge     from '../components/ScoreGauge';
import MetricsChart   from '../components/MetricsChart';
import MetricsBreakdown from '../components/MetricsBreakdown';
import FeedbackCard   from '../components/FeedbackCard';
import VideoPlayer    from '../components/VideoPlayer';

const s = {
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  btn: {
    padding: '0.5rem 1.25rem',
    background: '#fff',
    border: '1px solid #d3d1c7',
    borderRadius: '8px',
    fontSize: '0.9rem',
    fontWeight: '500',
    color: '#5f5e5a',
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '1.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  cardTitle: {
    fontSize: '0.8rem',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#888780',
    marginBottom: '1rem',
  },
  detectionBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    padding: '0.3rem 0.7rem',
    borderRadius: '20px',
    fontSize: '0.8rem',
    fontWeight: '500',
    background: '#E1F5EE',
    color: '#0F6E56',
    marginTop: '0.75rem',
  },
  statsRow: {
    display: 'flex',
    gap: '0.75rem',
    marginTop: '0.75rem',
  },
  statPill: {
    flex: 1,
    background: '#f5f5f4',
    borderRadius: '8px',
    padding: '0.5rem 0.75rem',
    textAlign: 'center',
  },
  statVal: {
    fontWeight: '700',
    fontSize: '1.1rem',
    color: '#1a1a18',
  },
  statLabel: {
    fontSize: '0.72rem',
    color: '#888780',
    marginTop: '0.1rem',
  },
};

export default function ResultsPage({ results, onReset }) {
  const detectionPct = Math.round((results.detection_rate || 0) * 100);

  return (
    <div className="page-results">
      <div className="results-header">
        <div style={s.logo}>
          <span style={{ fontSize: '1.5rem' }}>🎾</span>
          <h2 style={{ fontWeight: '700' }}>TennisAnalyzer</h2>
        </div>
        <button style={s.btn} onClick={onReset}>← Nuevo análisis</button>
      </div>

      <div className="results-grid">

        {/* Columna izquierda: puntuación + stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={s.card}>
            <p style={s.cardTitle}>Puntuación global</p>
            <ScoreGauge score={results.score} />
            <div style={s.statsRow}>
              <div style={s.statPill}>
                <div style={s.statVal}>{results.n_frames}</div>
                <div style={s.statLabel}>fotogramas</div>
              </div>
              <div style={s.statPill}>
                <div style={s.statVal}>{detectionPct}%</div>
                <div style={s.statLabel}>detección</div>
              </div>
            </div>
            <div style={s.detectionBadge}>
              ✓ Análisis completado
            </div>
          </div>

          <div style={s.card}>
            <p style={s.cardTitle}>Desglose técnico</p>
            <MetricsBreakdown breakdown={results.breakdown} />
          </div>
        </div>

        {/* Columna derecha: vídeo + gráficas + feedback */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={s.card}>
            <p style={s.cardTitle}>Vídeo anotado</p>
            <VideoPlayer url={results.annotated_video_url} />
          </div>

          <div style={s.card}>
            <p style={s.cardTitle}>Evolución de métricas cinemáticas</p>
            <MetricsChart metricsSeries={results.metrics_series} />
          </div>

          <FeedbackCard feedback={results.feedback} />
        </div>

      </div>
    </div>
  );
}
