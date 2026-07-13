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
  limitItem: {
    display: 'flex',
    gap: '0.65rem',
    alignItems: 'flex-start',
    marginBottom: '0.75rem',
    fontSize: '0.88rem',
    color: '#5f5e5a',
    lineHeight: 1.6,
  },
  limitBullet: {
    flexShrink: 0,
    marginTop: '0.15em',
    color: '#EF9F27',
    fontWeight: '700',
    fontSize: '1rem',
  },
  authorRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  authorAvatar: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #1D9E75 0%, #0d6e50 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.4rem',
    flexShrink: 0,
    boxShadow: '0 2px 8px rgba(29,158,117,0.3)',
  },
  authorInfo: {
    flex: 1,
  },
  authorName: {
    fontWeight: '700',
    fontSize: '1rem',
    color: '#1a1a18',
    marginBottom: '0.2rem',
  },
  authorRole: {
    fontSize: '0.82rem',
    color: '#888780',
    lineHeight: 1.5,
  },
  repoLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.5rem 1rem',
    background: '#1a1a18',
    color: '#fff',
    borderRadius: '8px',
    fontSize: '0.82rem',
    fontWeight: '600',
    textDecoration: 'none',
    flexShrink: 0,
  },
};

const STEPS = [
  { n: '1', title: 'Subida del vídeo', desc: 'El usuario sube un vídeo de su golpe de derecha. El sistema acepta formatos MP4, MOV y AVI de hasta 200 MB.' },
  { n: '2', title: 'Validación del contenido', desc: 'YOLOv8 verifica que el vídeo contiene un jugador con raqueta antes de procesarlo. Si no se detecta golpe real, se rechaza con un mensaje descriptivo.' },
  { n: '3', title: 'Estimación de pose', desc: 'MediaPipe Pose Landmarker detecta 33 puntos anatómicos en cada fotograma del vídeo con alta precisión.' },
  { n: '4', title: 'Extracción de métricas', desc: 'Se calculan ángulos articulares (codo, hombro, rodilla), inclinación de tronco, rotación de torso y velocidad de muñeca frame a frame. El sistema detecta automáticamente las fases del golpe (preparación, backswing, impacto y follow-through).' },
  { n: '5', title: 'Puntuación técnica', desc: 'Un modelo Random Forest entrenado con vídeos etiquetados por nivel técnico asigna una puntuación global de 0 a 100. Cuando no hay modelo disponible, se usa un sistema de scoring por rangos biomecánicos.' },
  { n: '6', title: 'Feedback con IA', desc: 'Claude (Anthropic) genera un resumen, una lista de aspectos a mejorar y consejos prácticos personalizados a partir de las métricas del análisis, con apoyo de un índice biomecánico de referencia (RAG).' },
];

const TECH = [
  { icon: '⚡', label: 'FastAPI 0.111' },
  { icon: '🦾', label: 'MediaPipe Pose' },
  { icon: '🌲', label: 'Random Forest' },
  { icon: '🤖', label: 'Claude API' },
  { icon: '⚛️', label: 'React 18' },
  { icon: '📹', label: 'OpenCV 4.9' },
  { icon: '🎯', label: 'YOLOv8' },
  { icon: '📚', label: 'ChromaDB (RAG)' },
];

const LIMITS = [
  'Solo analiza el golpe de derecha. Revés, saque y volea no están soportados.',
  'El modelo de puntuación fue entrenado con un corpus pequeño (~93 muestras). Las puntuaciones son orientativas y pueden no reflejar el nivel real en casos atípicos.',
  'El tiempo de procesamiento depende de la resolución y duración del vídeo. Vídeos 4K pueden tardar más de un minuto en servidores de CPU compartida.',
  'La detección de pose puede fallar si el jugador está parcialmente ocluido, hay contraluz intenso o la cámara se mueve mucho.',
  'El feedback de Claude está generado por un modelo de lenguaje y no reemplaza la valoración de un entrenador certificado.',
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
          {STEPS.map((step, i) => (
            <div key={step.n} style={i === STEPS.length - 1 ? { ...s.step, marginBottom: 0 } : s.step}>
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

        <div style={s.card}>
          <p style={s.cardTitle}>Limitaciones conocidas</p>
          {LIMITS.map((lim, i) => (
            <div key={i} style={i === LIMITS.length - 1 ? { ...s.limitItem, marginBottom: 0 } : s.limitItem}>
              <span style={s.limitBullet}>⚠</span>
              <span>{lim}</span>
            </div>
          ))}
        </div>

        <div style={s.card}>
          <p style={s.cardTitle}>Autor</p>
          <div style={s.authorRow}>
            <div style={s.authorAvatar}>🎓</div>
            <div style={s.authorInfo}>
              <p style={s.authorName}>Iván Moreno Aranda</p>
              <p style={s.authorRole}>
                Trabajo de Fin de Estudios · Máster en Inteligencia Artificial · UNIR, 2026<br />
                Tutor: Alejandro
              </p>
            </div>
            <a
              href="https://github.com/ivmoar/tennis-analyzer"
              target="_blank"
              rel="noopener noreferrer"
              style={s.repoLink}
            >
              <span>⌥</span> GitHub
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
