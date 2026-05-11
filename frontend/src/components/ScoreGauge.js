import React from 'react';

function getColor(score) {
  if (score >= 75) return { stroke: '#1D9E75', text: '#0F6E56', bg: '#E1F5EE', label: 'Técnica sólida' };
  if (score >= 50) return { stroke: '#EF9F27', text: '#854F0B', bg: '#FAEEDA', label: 'En desarrollo' };
  return             { stroke: '#E24B4A', text: '#A32D2D', bg: '#FCEBEB', label: 'Aspectos a mejorar' };
}

export default function ScoreGauge({ score }) {
  const size   = 180;
  const cx     = size / 2;
  const cy     = size / 2;
  const r      = 72;
  const stroke = 14;

  // Arco semicircular (180°) de izquierda a derecha
  const startAngle = 180;
  const endAngle   = 0;
  const pct        = Math.min(Math.max(score, 0), 100) / 100;
  const angle      = startAngle + pct * 180;

  function polar(cx, cy, r, deg) {
    const rad = (deg - 90) * Math.PI / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  }

  function arcPath(cx, cy, r, startDeg, endDeg) {
    const [sx, sy] = polar(cx, cy, r, startDeg);
    const [ex, ey] = polar(cx, cy, r, endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`;
  }

  const [nx, ny] = polar(cx, cy, r, angle);
  const col = getColor(score);

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        {/* Track */}
        <path
          d={arcPath(cx, cy, r, 180, 360)}
          fill="none"
          stroke="#e5e5e3"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={arcPath(cx, cy, r, 180, 180 + pct * 180)}
          fill="none"
          stroke={col.stroke}
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Needle dot */}
        <circle cx={nx} cy={ny} r={7} fill={col.stroke} />
        {/* Score text */}
        <text
          x={cx} y={cy - 4}
          textAnchor="middle"
          fontSize="36"
          fontWeight="700"
          fontFamily="Inter, sans-serif"
          fill={col.text}
        >
          {Math.round(score)}
        </text>
        <text
          x={cx} y={cy + 16}
          textAnchor="middle"
          fontSize="12"
          fontFamily="Inter, sans-serif"
          fill="#888780"
        >
          / 100
        </text>
      </svg>

      <div style={{
        display: 'inline-block',
        marginTop: '0.25rem',
        padding: '0.3rem 0.9rem',
        borderRadius: '20px',
        background: col.bg,
        color: col.text,
        fontWeight: '600',
        fontSize: '0.85rem',
      }}>
        {col.label}
      </div>
    </div>
  );
}
