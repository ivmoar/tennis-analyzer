import React from 'react';

const s = {
  page: {
    minHeight: 'calc(100vh - 64px)',
    background: '#f5f5f4',
    padding: '3rem 1.5rem',
  },
  inner: {
    maxWidth: '800px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  hero: {
    textAlign: 'center',
    paddingBottom: '1rem',
  },
  heroTitle: {
    fontSize: '2rem',
    fontWeight: '800',
    color: '#1a1a18',
    marginBottom: '0.75rem',
  },
  heroSub: {
    fontSize: '1rem',
    color: '#5f5e5a',
    maxWidth: '560px',
    margin: '0 auto',
    lineHeight: 1.7,
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '1.75rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  cardTitle: {
    fontSize: '0.78rem',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    color: '#1D9E75',
    marginBottom: '1rem',
  },
  step: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-start',
    marginBottom: '1rem',
  },
  stepNum: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: '#E1F5EE',
    color: '#0F6E56',
    fontWeight: '700',
    fontSize: '0.9rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stepText: {
    paddingTop: '0.35rem',
  },
  stepTitle: {
    fontWeight: '600',
    fontSize: '0.95rem',
    color: '#1a1a18',
    marginBottom: '0.25rem',
  },
  stepDesc: {
    fontSize: '0.88rem',
    color: '#5f5e5a',
    lineHeight: 1.6,
  },
  techGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '0.75rem',
  },
  techPill: {
    background: '#f5f5f4',
    border: '1px solid #e5e5e3',
    borderRadius: '10px',
    padding: '0.75rem 1rem',
    fontSize: '0.85rem',
    fontWeight: '500',
    color: '#1a1a18',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
};

const STEPS = [
  { n: '1', title: 'Subida del vídeo', desc: 'El usuario sube un vídeo de su golpe de derecha. El sistema acepta formatos MP4, MOV y AVI de hasta 100 MB.' },
  { n: '2', title: 'Estimación de pose', desc: 'MediaPipe Pose Landmarker detecta 33 puntos anatómicos en cada fotograma del vídeo con precisión submilimétrica.' },
  { n: '3', title: 'Extracción de métricas', desc: 'Se calculan ángulos articulares (codo, hombro, rodilla), inclinación de tronco y separación de caderas en cada frame.' },
  { n: '4', title: 'Puntuación técnica', desc: 'Un modelo Random Forest entrenado con golpes etiquetados por nivel técnico asigna una puntuación global al movimiento.' },
  { n: '5', title: 'Feedback con IA', desc: 'Claude (Anthropic) genera un feedback personalizado y accionable basado en las métricas extraídas del análisis.' },
];

const TECH = [
  { icon: '⚡', label: 'FastAPI 0.111' },
  { icon: '🦾', label: 'MediaPipe Pose' },
  { icon: '🌲', label: 'Random Forest' },
  { icon: '🤖', label: 'Claude API' },
  { icon: '⚛️', label: 'React 18' },
  { icon: '📹', label: 'OpenCV 4.9' },
];

export default function AboutPage() {
  return (
    <div style={s.page}>
      <div style={s.inner}>
        <div style={s.hero}>
          <h1 style={s.heroTitle}>Cómo funciona Ivanalyze</h1>
          <p style={s.heroSub}>
            Sistema de análisis biomecánico del golpe de derecha desarrollado como Trabajo de Fin de Estudios en la UNIR.
            Combina visión por computador, machine learning y modelos de lenguaje para ofrecer feedback técnico automatizado.
          </p>
        </div>

        <div style={s.card}>
          <p style={s.cardTitle}>Flujo de análisis</p>
          {STEPS.map(step => (
            <div key={step.n} style={step.n === '5' ? { ...s.step, marginBottom: 0 } : s.step}>
              <div style={s.stepNum}>{step.n}</div>
              <div style={s.stepText}>
                <p style={s.stepTitle}>{step.title}</p>
                <p style={s.stepDesc}>{step.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div style={s.card}>
          <p style={s.cardTitle}>Stack tecnológico</p>
          <div style={s.techGrid}>
            {TECH.map(t => (
              <div key={t.label} style={s.techPill}>
                <span>{t.icon}</span>
                <span>{t.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
