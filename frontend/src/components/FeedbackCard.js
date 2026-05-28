import React from 'react';

const s = {
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '1.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    borderLeft: '4px solid #1D9E75',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  headerLabel: {
    fontSize: '0.8rem',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#888780',
  },
  summary: {
    fontSize: '0.92rem',
    lineHeight: 1.72,
    color: '#3d3d3a',
    marginBottom: '1rem',
  },
  sectionTitle: {
    fontSize: '0.78rem',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    marginBottom: '0.6rem',
  },
  item: {
    display: 'flex',
    gap: '0.55rem',
    fontSize: '0.9rem',
    lineHeight: 1.65,
    marginBottom: '0.5rem',
  },
  bullet: {
    flexShrink: 0,
    marginTop: '0.15em',
    fontWeight: '700',
  },
};

function Section({ icon, title, color, children }) {
  return (
    <div style={{ marginTop: '0.9rem' }}>
      <p style={{ ...s.sectionTitle, color }}>
        {icon} {title}
      </p>
      {children}
    </div>
  );
}

function Item({ text, bulletColor }) {
  return (
    <div style={s.item}>
      <span style={{ ...s.bullet, color: bulletColor }}>›</span>
      <span style={{ color: '#3d3d3a' }}>{text}</span>
    </div>
  );
}

export default function FeedbackCard({ feedback }) {
  if (!feedback) return null;

  // Formato estructurado {summary, issues, tips}
  if (typeof feedback === 'object') {
    const { summary = '', issues = [], tips = [] } = feedback;
    return (
      <div style={s.card}>
        <div style={s.header}>
          <span style={{ fontSize: '1.2rem' }}>💬</span>
          <p style={s.headerLabel}>Feedback del entrenador virtual</p>
        </div>

        {summary && <p style={s.summary}>{summary}</p>}

        {issues.length > 0 && (
          <Section icon="⚠️" title="Aspectos a mejorar" color="#A32D2D">
            {issues.map((issue, i) => (
              <Item key={i} text={issue} bulletColor="#E24B4A" />
            ))}
          </Section>
        )}

        {tips.length > 0 && (
          <Section icon="💡" title="Cómo mejorar" color="#0F6E56">
            {tips.map((tip, i) => (
              <Item key={i} text={tip} bulletColor="#1D9E75" />
            ))}
          </Section>
        )}
      </div>
    );
  }

  // Fallback: texto plano / markdown (compatibilidad hacia atrás)
  const paragraphs = feedback.split('\n\n').filter(Boolean);
  return (
    <div style={s.card}>
      <div style={s.header}>
        <span style={{ fontSize: '1.2rem' }}>💬</span>
        <p style={s.headerLabel}>Feedback del entrenador virtual</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {paragraphs.map((para, i) => (
          <p key={i} style={{ fontSize: '0.92rem', lineHeight: 1.7, color: '#3d3d3a' }}>
            {para}
          </p>
        ))}
      </div>
    </div>
  );
}
