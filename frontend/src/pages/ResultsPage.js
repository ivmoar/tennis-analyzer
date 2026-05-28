import React, { useRef, useState, useCallback } from 'react';

import ScoreGauge       from '../components/ScoreGauge';
import MetricsChart     from '../components/MetricsChart';
import MetricsBreakdown from '../components/MetricsBreakdown';
import FeedbackCard     from '../components/FeedbackCard';
import VideoPlayer      from '../components/VideoPlayer';
import AdvancedAnalysisPanel from '../components/AdvancedAnalysisPanel';

const s = {
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
    fontSize: '0.78rem',
    fontWeight: '700',
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
  const videoRef    = useRef(null);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [fps,          setFps]          = useState(30);

  const detectionPct = Math.round((results.detection_rate || 0) * 100);

  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current && results.n_frames) {
      const calculated = results.n_frames / videoRef.current.duration;
      setFps(calculated || 30);
    }
  }, [results.n_frames]);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentFrame(Math.floor(videoRef.current.currentTime * fps));
    }
  }, [fps]);

  const handleFrameClick = useCallback((frame) => {
    if (videoRef.current) {
      videoRef.current.currentTime = frame / fps;
    }
  }, [fps]);

  return (
    <div className="page-results">
      <div className="results-header">
        <div>
          <h2 style={{ fontWeight: '700', color: '#1a1a18' }}>Resultados del análisis</h2>
          <p style={{ fontSize: '0.85rem', color: '#888780', marginTop: '0.15rem' }}>
            Golpe de derecha · Análisis biomecánico completo
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button style={s.btn} className="no-print" onClick={() => window.print()}>Exportar PDF</button>
          <button style={s.btn} className="no-print" onClick={onReset}>← Nuevo análisis</button>
        </div>
      </div>

      <div>
        <div className="results-grid">

          {/* Columna izquierda */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={s.card}>
              <p style={s.cardTitle}>Puntuación global</p>
              <ScoreGauge score={results.score} />
              <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '12px',
                  fontSize: '0.72rem',
                  fontWeight: '600',
                  background: results.scoring_method === 'model' ? '#E1F5EE' : '#f5f5f4',
                  color:      results.scoring_method === 'model' ? '#0F6E56' : '#888780',
                  border: `1px solid ${results.scoring_method === 'model' ? 'rgba(29,158,117,0.3)' : '#e5e5e3'}`,
                }}>
                  {results.scoring_method === 'model' ? '🌲 Random Forest' : '📏 Scoring por rangos'}
                </span>
              </div>
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
              <div style={s.detectionBadge}>✓ Análisis completado</div>
            </div>

            <div style={s.card}>
              <p style={s.cardTitle}>Desglose técnico</p>
              <MetricsBreakdown breakdown={results.breakdown} />
            </div>
          </div>

          {/* Columna derecha */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={s.card}>
              <p style={s.cardTitle}>Vídeo anotado</p>
              <VideoPlayer
                ref={videoRef}
                url={results.annotated_video_url}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
              />
              {!results.annotated_video_url && (
                <div style={{
                  textAlign: 'center', padding: '2rem 1rem',
                  color: '#a3a39c', fontSize: '0.85rem', lineHeight: 1.6,
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📹</div>
                  Modo demo — sube tu propio vídeo para ver<br />el análisis con landmarks dibujados
                </div>
              )}
            </div>

            <div style={s.card}>
              <p style={s.cardTitle}>Evolución de métricas cinemáticas</p>
              <MetricsChart
                metricsSeries={results.metrics_series}
                phases={results.phases}
                currentFrame={currentFrame}
                onFrameClick={handleFrameClick}
              />
            </div>

            <FeedbackCard feedback={results.feedback} />
          </div>

        </div>

        <AdvancedAnalysisPanel results={results} currentFrame={currentFrame} />
      </div>
    </div>
  );
}
