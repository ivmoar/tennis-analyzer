import React from 'react';

export default function FeedbackCard({ feedback }) {
  if (!feedback) return null;

  const paragraphs = feedback.split('\n\n').filter(Boolean);

  return (
    <div style={{
      background: '#fff',
      borderRadius: '16px',
      padding: '1.5rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      borderLeft: '4px solid #1D9E75',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <span style={{ fontSize: '1.2rem' }}>💬</span>
        <p style={{
          fontSize: '0.8rem',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: '#888780',
        }}>
          Feedback del entrenador virtual
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {paragraphs.map((para, i) => (
          <p key={i} style={{
            fontSize: '0.92rem',
            lineHeight: '1.7',
            color: '#3d3d3a',
          }}>
            {para.startsWith('-') || para.startsWith('•')
              ? para.split('\n').map((line, j) => (
                  <span key={j} style={{ display: 'block', paddingLeft: '0.75rem', position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 0, color: '#1D9E75' }}>›</span>
                    {line.replace(/^[-•]\s*/, '')}
                  </span>
                ))
              : para
            }
          </p>
        ))}
      </div>
    </div>
  );
}
