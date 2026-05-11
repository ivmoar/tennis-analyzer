import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ReferenceArea, ResponsiveContainer, Legend,
} from 'recharts';

const METRICS = [
  { key: 'elbow_angle',    label: 'Codo',    color: '#E24B4A', lo: 100, hi: 160 },
  { key: 'shoulder_angle', label: 'Hombro',  color: '#378ADD', lo: 60,  hi: 120 },
  { key: 'knee_angle',     label: 'Rodilla', color: '#1D9E75', lo: 130, hi: 170 },
  { key: 'trunk_tilt',     label: 'Tronco',  color: '#EF9F27', lo: 0,   hi: 20  },
];

export default function MetricsChart({ metricsSeries }) {
  const [active, setActive] = useState('elbow_angle');

  if (!metricsSeries?.length) return null;

  const metric = METRICS.find(m => m.key === active);

  const data = metricsSeries.map((m, i) => ({
    frame: i,
    value: m ? m[active] : null,
  })).filter(d => d.value !== null);

  return (
    <div>
      {/* Selector de métrica */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {METRICS.map(m => (
          <button
            key={m.key}
            onClick={() => setActive(m.key)}
            style={{
              padding: '0.3rem 0.85rem',
              borderRadius: '20px',
              fontSize: '0.8rem',
              fontWeight: '500',
              background: active === m.key ? m.color : '#f5f5f4',
              color:      active === m.key ? '#fff'   : '#5f5e5a',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0ee" />
          <XAxis
            dataKey="frame"
            tick={{ fontSize: 10, fill: '#a3a39c' }}
            label={{ value: 'Fotograma', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#a3a39c' }}
          />
          <YAxis tick={{ fontSize: 10, fill: '#a3a39c' }} unit="°" />
          <Tooltip
            formatter={(v) => [`${v}°`, metric.label]}
            labelFormatter={(l) => `Fotograma ${l}`}
            contentStyle={{ fontSize: '0.8rem', borderRadius: '8px', border: '1px solid #e5e5e3' }}
          />
          {/* Banda del rango óptimo */}
          <ReferenceArea
            y1={metric.lo} y2={metric.hi}
            fill={metric.color}
            fillOpacity={0.08}
            label={{ value: 'Rango óptimo', position: 'insideTopRight', fontSize: 9, fill: metric.color }}
          />
          <ReferenceLine y={metric.lo} stroke={metric.color} strokeDasharray="3 3" strokeOpacity={0.4} />
          <ReferenceLine y={metric.hi} stroke={metric.color} strokeDasharray="3 3" strokeOpacity={0.4} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={metric.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
