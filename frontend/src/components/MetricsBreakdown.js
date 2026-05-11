import React from 'react';

const STATUS_COLOR = {
  ok:   { bar: '#1D9E75', bg: '#E1F5EE', text: '#0F6E56', label: 'Óptimo' },
  low:  { bar: '#EF9F27', bg: '#FAEEDA', text: '#854F0B', label: 'Bajo'   },
  high: { bar: '#E24B4A', bg: '#FCEBEB', text: '#A32D2D', label: 'Alto'   },
};

export default function MetricsBreakdown({ breakdown }) {
  if (!breakdown) return null;
  const items = Object.entries(breakdown);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
      {items.map(([key, info]) => {
        const col = STATUS_COLOR[info.status] || STATUS_COLOR.ok;
        const pct = Math.min(Math.max(info.score, 0), 100);

        return (
          <div key={key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
              <span style={{ fontWeight: '500', fontSize: '0.88rem' }}>{info.label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', color: '#888780' }}>{info.value}°</span>
                <span style={{
                  padding: '0.15rem 0.5rem',
                  borderRadius: '10px',
                  background: col.bg,
                  color: col.text,
                  fontSize: '0.75rem',
                  fontWeight: '600',
                }}>
                  {col.label}
                </span>
              </div>
            </div>
            <div style={{ height: '6px', background: '#e5e5e3', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${pct}%`,
                background: col.bar,
                borderRadius: '3px',
                transition: 'width 0.6s ease',
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.2rem' }}>
              <span style={{ fontSize: '0.7rem', color: '#a3a39c' }}>Rango: {info.range[0]}–{info.range[1]}°</span>
              <span style={{ fontSize: '0.7rem', color: '#a3a39c' }}>{Math.round(pct)}/100</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
