import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ReferenceArea, ResponsiveContainer,
} from 'recharts';

const METRICS = [
  { key: 'elbow_angle',    label: 'Codo',    color: '#E24B4A', lo: 100, hi: 160 },
  { key: 'shoulder_angle', label: 'Hombro',  color: '#378ADD', lo: 60,  hi: 120 },
  { key: 'knee_angle',     label: 'Rodilla', color: '#1D9E75', lo: 130, hi: 170 },
  { key: 'trunk_tilt',     label: 'Tronco',  color: '#EF9F27', lo: 0,   hi: 20  },
  { key: 'torso_rotation', label: 'Rotación', color: '#7A5CFF' },
  { key: 'arm_extension',  label: 'Extensión brazo', color: '#0F6E56' },
  { key: 'right_wrist_speed', label: 'Muñeca der. vel.', color: '#D14C8B' },
  { key: 'left_wrist_speed',  label: 'Muñeca izq. vel.', color: '#5D7A1F' },
];

const PALETTE = ['#E24B4A', '#378ADD', '#1D9E75', '#EF9F27', '#7A5CFF', '#D14C8B', '#0F6E56', '#5D7A1F'];

const PHASE_STYLES = {
  'preparación':    { fill: '#378ADD', opacity: 0.08 },
  'backswing':      { fill: '#EF9F27', opacity: 0.10 },
  'impacto':        { fill: '#E24B4A', opacity: 0.11 },
  'follow-through': { fill: '#1D9E75', opacity: 0.09 },
};

export default function MetricsChart({ metricsSeries, phases, currentFrame, onFrameClick }) {
  const [active, setActive] = useState('elbow_angle');

  const dynamicMetrics = React.useMemo(() => {
    if (!metricsSeries?.length) return [];
    const first = metricsSeries.find(Boolean) || {};
    const extraKeys = Object.keys(first)
      .filter(key => typeof first[key] === 'number')
      .filter(key => !METRICS.some(m => m.key === key))
      .map((key, i) => ({
        key,
        label: key.replaceAll('_', ' '),
        color: PALETTE[i % PALETTE.length],
      }));
    return [...METRICS.filter(m => first[m.key] !== undefined), ...extraKeys];
  }, [metricsSeries]);

  if (!metricsSeries?.length || !dynamicMetrics.length) return null;

  const metric = dynamicMetrics.find(m => m.key === active) || dynamicMetrics[0];

  const data = metricsSeries.map((m, i) => ({
    frame: i,
    value: m && metric ? m[metric.key] : null,
  })).filter(d => d.value !== null);

  const handleChartClick = (e) => {
    if (e?.activePayload?.[0] && onFrameClick) {
      onFrameClick(e.activePayload[0].payload.frame);
    }
  };

  return (
    <div>
      {/* Selector de métrica */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        {dynamicMetrics.map(m => (
          <button
            key={m.key}
            onClick={() => setActive(m.key)}
            style={{
              padding: '0.3rem 0.85rem',
              borderRadius: '20px',
              fontSize: '0.8rem',
              fontWeight: '500',
              background: metric?.key === m.key ? m.color : '#f5f5f4',
              color:      metric?.key === m.key ? '#fff'   : '#5f5e5a',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      <p style={{ fontSize: '0.72rem', color: '#a3a39c', marginBottom: '0.4rem' }}>
        Haz clic en la gráfica para saltar al frame en el vídeo
      </p>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart
          data={data}
          margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
          onClick={handleChartClick}
          style={{ cursor: onFrameClick ? 'pointer' : 'default' }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0ee" />
          <XAxis
            dataKey="frame"
            tick={{ fontSize: 10, fill: '#a3a39c' }}
            label={{ value: 'Fotograma', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#a3a39c' }}
          />
          <YAxis tick={{ fontSize: 10, fill: '#a3a39c' }} />
          <Tooltip
            formatter={(v) => [v, metric.label]}
            labelFormatter={(l) => `Fotograma ${l}`}
            contentStyle={{ fontSize: '0.8rem', borderRadius: '8px', border: '1px solid #e5e5e3' }}
          />

          {/* Bandas de fase */}
          {(phases || []).map(phase => {
            const ps = PHASE_STYLES[phase.name] || { fill: '#888', opacity: 0.07 };
            return (
              <ReferenceArea
                key={phase.name}
                x1={phase.start_frame}
                x2={phase.end_frame}
                fill={ps.fill}
                fillOpacity={ps.opacity}
                ifOverflow="extendDomain"
              />
            );
          })}

          {/* Rango óptimo de la métrica activa */}
          {metric.lo !== undefined && metric.hi !== undefined && (
            <>
              <ReferenceArea
                y1={metric.lo} y2={metric.hi}
                fill={metric.color}
                fillOpacity={0.06}
                label={{ value: 'Rango óptimo', position: 'insideTopRight', fontSize: 9, fill: metric.color }}
              />
              <ReferenceLine y={metric.lo} stroke={metric.color} strokeDasharray="3 3" strokeOpacity={0.4} />
              <ReferenceLine y={metric.hi} stroke={metric.color} strokeDasharray="3 3" strokeOpacity={0.4} />
            </>
          )}

          {/* Cursor de frame actual */}
          {currentFrame !== null && (
            <ReferenceLine
              x={currentFrame}
              stroke="#1a1a18"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              label={{ value: `▶ ${currentFrame}`, position: 'top', fontSize: 9, fill: '#1a1a18' }}
            />
          )}

          <Line
            type="monotone"
            dataKey="value"
            stroke={metric.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, cursor: 'pointer' }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Leyenda de fases */}
      {(phases || []).length > 0 && (
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
          {phases.map(phase => {
            const ps = PHASE_STYLES[phase.name] || { fill: '#888' };
            return (
              <span key={phase.name} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem', color: '#5f5e5a' }}>
                <span style={{
                  display: 'inline-block', width: '10px', height: '10px',
                  background: ps.fill, opacity: 0.7, borderRadius: '2px', flexShrink: 0,
                }} />
                {phase.name}
                <span style={{ color: '#a3a39c' }}>{phase.start_frame}–{phase.end_frame}</span>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
