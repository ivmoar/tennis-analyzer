import React from 'react';

const COLOR = {
  ok:   { zone: '#1D9E75', bg: '#E1F5EE', text: '#0F6E56', label: 'Óptimo' },
  low:  { zone: '#EF9F27', bg: '#FAEEDA', text: '#854F0B', label: 'Bajo'   },
  high: { zone: '#E24B4A', bg: '#FCEBEB', text: '#A32D2D', label: 'Alto'   },
};

function RangeBar({ value, rangeMin, rangeMax }) {
  const padding = (rangeMax - rangeMin) * 0.6;
  const scaleMin = Math.max(0, rangeMin - padding);
  const scaleMax = rangeMax + padding;
  const span = scaleMax - scaleMin;

  const pct  = v => Math.min(100, Math.max(0, ((v - scaleMin) / span) * 100));
  const zoneL = pct(rangeMin);
  const zoneW = pct(rangeMax) - zoneL;
  const needle = pct(value);

  const inRange = value >= rangeMin && value <= rangeMax;
  const needleColor = inRange ? '#1D9E75' : value < rangeMin ? '#EF9F27' : '#E24B4A';

  return (
    <div style={{ position: 'relative', margin: '0.5rem 0 0.15rem' }}>
      {/* Track */}
      <div style={{ height: '8px', background: '#e5e5e3', borderRadius: '4px', position: 'relative', overflow: 'visible' }}>
        {/* Zona óptima */}
        <div style={{
          position: 'absolute',
          left: `${zoneL}%`,
          width: `${zoneW}%`,
          height: '100%',
          background: '#1D9E75',
          opacity: 0.25,
          borderRadius: '2px',
        }} />
        {/* Needle */}
        <div style={{
          position: 'absolute',
          left: `${needle}%`,
          top: '-4px',
          transform: 'translateX(-50%)',
          width: '4px',
          height: '16px',
          background: needleColor,
          borderRadius: '2px',
          boxShadow: `0 0 0 2px white, 0 0 0 3px ${needleColor}`,
          transition: 'left 0.5s ease',
        }} />
      </div>
      {/* Etiquetas de escala */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem' }}>
        <span style={{ fontSize: '0.68rem', color: '#a3a39c' }}>{Math.round(scaleMin)}°</span>
        <span style={{ fontSize: '0.68rem', color: '#1D9E75', fontWeight: '600' }}>
          {rangeMin}–{rangeMax}° ideal
        </span>
        <span style={{ fontSize: '0.68rem', color: '#a3a39c' }}>{Math.round(scaleMax)}°</span>
      </div>
    </div>
  );
}

export default function MetricsBreakdown({ breakdown }) {
  if (!breakdown) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
      {Object.entries(breakdown).map(([key, info]) => {
        const col = COLOR[info.status] || COLOR.ok;
        return (
          <div key={key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: '600', fontSize: '0.88rem', color: '#1a1a18' }}>{info.label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1rem', fontWeight: '700', color: '#1a1a18' }}>{info.value}°</span>
                <span style={{
                  padding: '0.15rem 0.55rem',
                  borderRadius: '10px',
                  background: col.bg,
                  color: col.text,
                  fontSize: '0.72rem',
                  fontWeight: '700',
                }}>
                  {col.label}
                </span>
              </div>
            </div>
            <RangeBar value={info.value} rangeMin={info.range[0]} rangeMax={info.range[1]} />
          </div>
        );
      })}
    </div>
  );
}
