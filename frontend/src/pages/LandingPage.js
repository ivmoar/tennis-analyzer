import React from 'react';

const s = {
  page: {
    minHeight: 'calc(100vh - 64px)',
    background: '#fff',
    display: 'flex',
    flexDirection: 'column',
  },
  hero: {
    background: 'linear-gradient(135deg, #0d6e50 0%, #1D9E75 50%, #378ADD 100%)',
    padding: '5rem 1.5rem 4rem',
    textAlign: 'center',
    color: '#fff',
  },
  heroEyebrow: {
    display: 'inline-block',
    background: 'rgba(255,255,255,0.15)',
    border: '1px solid rgba(255,255,255,0.3)',
    borderRadius: '20px',
    padding: '0.3rem 1rem',
    fontSize: '0.8rem',
    fontWeight: '600',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    marginBottom: '1.5rem',
  },
  heroTitle: {
    fontSize: 'clamp(2rem, 5vw, 3.5rem)',
    fontWeight: '800',
    lineHeight: 1.15,
    marginBottom: '1.25rem',
    letterSpacing: '-0.02em',
    maxWidth: '800px',
    margin: '0 auto 1.25rem',
  },
  heroSub: {
    fontSize: '1.1rem',
    opacity: 0.88,
    maxWidth: '560px',
    margin: '0 auto 2.5rem',
    lineHeight: 1.7,
  },
  heroCta: {
    display: 'inline-block',
    padding: '0.95rem 2.5rem',
    background: '#fff',
    color: '#0d6e50',
    borderRadius: '12px',
    fontWeight: '700',
    fontSize: '1rem',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
    transition: 'transform 0.15s, box-shadow 0.15s',
    fontFamily: 'inherit',
  },
  heroSecondary: {
    marginLeft: '1rem',
    display: 'inline-block',
    padding: '0.95rem 2rem',
    background: 'transparent',
    color: '#fff',
    borderRadius: '12px',
    fontWeight: '600',
    fontSize: '1rem',
    border: '2px solid rgba(255,255,255,0.5)',
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'border-color 0.15s',
  },
  stats: {
    display: 'flex',
    justifyContent: 'center',
    gap: '3rem',
    marginTop: '3.5rem',
    paddingTop: '2rem',
    borderTop: '1px solid rgba(255,255,255,0.2)',
    flexWrap: 'wrap',
  },
  statItem: {
    textAlign: 'center',
  },
  statNum: {
    fontSize: '2rem',
    fontWeight: '800',
    display: 'block',
  },
  statLabel: {
    fontSize: '0.82rem',
    opacity: 0.75,
    marginTop: '0.2rem',
  },
  features: {
    padding: '4rem 1.5rem',
    background: '#f5f5f4',
    flex: 1,
  },
  featuresInner: {
    maxWidth: '1100px',
    margin: '0 auto',
  },
  featuresTitle: {
    textAlign: 'center',
    fontSize: '1.6rem',
    fontWeight: '800',
    color: '#1a1a18',
    marginBottom: '0.5rem',
  },
  featuresSub: {
    textAlign: 'center',
    color: '#5f5e5a',
    marginBottom: '3rem',
    fontSize: '0.95rem',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '1.25rem',
  },
  featureCard: {
    background: '#fff',
    borderRadius: '16px',
    padding: '1.75rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  featureIcon: {
    width: '44px',
    height: '44px',
    borderRadius: '12px',
    background: '#E1F5EE',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.3rem',
    marginBottom: '1rem',
  },
  featureTitle: {
    fontWeight: '700',
    fontSize: '1rem',
    color: '#1a1a18',
    marginBottom: '0.4rem',
  },
  featureDesc: {
    fontSize: '0.88rem',
    color: '#5f5e5a',
    lineHeight: 1.6,
  },
};

const FEATURES = [
  {
    icon: '🦾',
    title: 'Estimación de pose en tiempo real',
    desc: 'MediaPipe Pose Landmarker detecta 33 puntos anatómicos en cada fotograma del vídeo con alta precisión.',
  },
  {
    icon: '📐',
    title: 'Métricas biomecánicas',
    desc: 'Calcula ángulos de codo, hombro, rodilla, inclinación de tronco y separación de cadera automáticamente.',
  },
  {
    icon: '🌲',
    title: 'Puntuación con Machine Learning',
    desc: 'Un modelo Random Forest entrenado evalúa la calidad técnica del golpe en una escala de 0 a 100.',
  },
  {
    icon: '🤖',
    title: 'Feedback personalizado con IA',
    desc: 'Claude (Anthropic) genera recomendaciones específicas y accionables basadas en tus métricas.',
  },
  {
    icon: '📊',
    title: 'Análisis frame a frame',
    desc: 'Visualiza la evolución de cada métrica durante todo el movimiento e identifica el momento exacto de los errores.',
  },
  {
    icon: '⬇',
    title: 'Informe exportable en PDF',
    desc: 'Descarga un informe completo con puntuación, métricas y feedback para compartir con tu entrenador.',
  },
];

export default function LandingPage({ onStart, onAbout, onDemo }) {
  return (
    <div style={s.page}>
      <div style={s.hero}>
        <span style={s.heroEyebrow}>TFE · UNIR 2026</span>
        <h1 style={s.heroTitle}>Analiza tu técnica de tenis con Inteligencia Artificial</h1>
        <p style={s.heroSub}>
          Sube un vídeo de tu golpe de derecha y recibe métricas biomecánicas detalladas,
          puntuación técnica y feedback personalizado generado por IA en segundos.
        </p>
        <div className="landing-hero-btns">
          <button style={s.heroCta} onClick={onStart}>
            Analizar mi golpe →
          </button>
          <button style={{ ...s.heroSecondary, marginLeft: 0 }} onClick={onDemo}>
            Ver demo
          </button>
          <button style={{ ...s.heroSecondary, marginLeft: 0 }} onClick={onAbout}>
            Cómo funciona
          </button>
        </div>
        <div style={s.stats}>
          {[
            { num: '33',   label: 'Puntos anatómicos detectados' },
            { num: '5',    label: 'Métricas biomecánicas' },
            { num: '0–100', label: 'Escala de puntuación' },
            { num: 'IA',   label: 'Feedback con Claude API' },
          ].map(st => (
            <div key={st.label} style={s.statItem}>
              <span style={s.statNum}>{st.num}</span>
              <span style={s.statLabel}>{st.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={s.features}>
        <div style={s.featuresInner}>
          <h2 style={s.featuresTitle}>Todo lo que necesitas para mejorar</h2>
          <p style={s.featuresSub}>Un sistema completo de análisis técnico en una sola herramienta</p>
          <div style={s.grid}>
            {FEATURES.map(f => (
              <div key={f.title} style={s.featureCard}>
                <div style={s.featureIcon}>{f.icon}</div>
                <p style={s.featureTitle}>{f.title}</p>
                <p style={s.featureDesc}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
