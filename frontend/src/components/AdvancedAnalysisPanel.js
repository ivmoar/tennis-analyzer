import React, { useEffect, useMemo, useState } from 'react';

const CORE_METRICS = [
  'elbow_angle',
  'shoulder_angle',
  'knee_angle',
  'trunk_tilt',
  'torso_rotation',
  'arm_extension',
  'stance_width',
  'hip_separation',
];

function formatValue(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1000) return value.toFixed(1);
    if (Math.abs(value) >= 100) return value.toFixed(2);
    return value.toFixed(4).replace(/\.?0+$/, '');
  }
  return value;
}

function downloadJson(results) {
  const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `tennis-analysis-${results.video_id || 'results'}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function SummaryTile({ label, value }) {
  return (
    <div className="advanced-summary-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="advanced-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function MetricsTable({ aggregatedMetrics }) {
  const rows = Object.entries(aggregatedMetrics || {});
  if (!rows.length) return null;

  return (
    <div className="advanced-table-wrap">
      <table className="advanced-table">
        <thead>
          <tr>
            <th>Métrica</th>
            <th>Media</th>
            <th>Std</th>
            <th>Mín</th>
            <th>Máx</th>
            <th>P25</th>
            <th>P50</th>
            <th>P75</th>
            <th>Rango</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([key, stats]) => (
            <tr key={key} className={CORE_METRICS.includes(key) ? 'row-highlight' : ''}>
              <td>{key}</td>
              <td>{formatValue(stats.mean)}</td>
              <td>{formatValue(stats.std)}</td>
              <td>{formatValue(stats.min)}</td>
              <td>{formatValue(stats.max)}</td>
              <td>{formatValue(stats.p25)}</td>
              <td>{formatValue(stats.p50)}</td>
              <td>{formatValue(stats.p75)}</td>
              <td>{formatValue(stats.range)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LandmarksTable({ frameData }) {
  const landmarks = frameData?.landmarks ? Object.entries(frameData.landmarks) : [];
  if (!landmarks.length) return <p className="advanced-empty">No hay landmarks detectados en este frame.</p>;

  return (
    <div className="advanced-table-wrap">
      <table className="advanced-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Landmark</th>
            <th>x</th>
            <th>y</th>
            <th>z</th>
            <th>px</th>
            <th>py</th>
            <th>pz</th>
            <th>Vis.</th>
            <th>Pres.</th>
          </tr>
        </thead>
        <tbody>
          {landmarks.map(([name, lm]) => (
            <tr key={name}>
              <td>{lm.index}</td>
              <td>{name}</td>
              <td>{formatValue(lm.x)}</td>
              <td>{formatValue(lm.y)}</td>
              <td>{formatValue(lm.z)}</td>
              <td>{formatValue(lm.pixel_x)}</td>
              <td>{formatValue(lm.pixel_y)}</td>
              <td>{formatValue(lm.pixel_z)}</td>
              <td>{formatValue(lm.visibility)}</td>
              <td>{formatValue(lm.presence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function KinematicsTable({ frameData }) {
  const landmarks = frameData?.landmarks ? Object.entries(frameData.landmarks) : [];
  if (!landmarks.length) return <p className="advanced-empty">No hay cinemática disponible en este frame.</p>;

  return (
    <div className="advanced-table-wrap">
      <table className="advanced-table">
        <thead>
          <tr>
            <th>Landmark</th>
            <th>vx</th>
            <th>vy</th>
            <th>vz</th>
            <th>Vel.</th>
            <th>ax</th>
            <th>ay</th>
            <th>az</th>
            <th>Acel.</th>
          </tr>
        </thead>
        <tbody>
          {landmarks.map(([name, kin]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>{formatValue(kin.vx)}</td>
              <td>{formatValue(kin.vy)}</td>
              <td>{formatValue(kin.vz)}</td>
              <td>{formatValue(kin.speed)}</td>
              <td>{formatValue(kin.ax)}</td>
              <td>{formatValue(kin.ay)}</td>
              <td>{formatValue(kin.az)}</td>
              <td>{formatValue(kin.acceleration)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AngleKinematicsTable({ frameData }) {
  const angles = frameData?.angles ? Object.entries(frameData.angles) : [];
  if (!angles.length) return null;

  return (
    <div className="advanced-table-wrap compact">
      <table className="advanced-table">
        <thead>
          <tr>
            <th>Magnitud angular</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {angles.map(([name, value]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>{formatValue(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FeatureVectorTable({ names = [], values = [] }) {
  if (!names.length || !values.length) return null;

  return (
    <div className="advanced-table-wrap features">
      <table className="advanced-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Feature</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {names.map((name, i) => (
            <tr key={`${name}-${i}`}>
              <td>{i}</td>
              <td>{name}</td>
              <td>{formatValue(values[i])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdvancedAnalysisPanel({ results, currentFrame }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedFrame, setSelectedFrame] = useState(0);
  const maxFrame = Math.max((results.n_frames || 1) - 1, 0);

  useEffect(() => {
    if (currentFrame !== null && currentFrame !== undefined) {
      setSelectedFrame(Math.min(Math.max(currentFrame, 0), maxFrame));
    }
  }, [currentFrame, maxFrame]);

  const landmarkFrame = results.landmarks_series?.[selectedFrame] || null;
  const kinematicsFrame = results.kinematics_series?.[selectedFrame] || null;
  const metricFrame = results.metrics_series?.[selectedFrame] || null;

  const compactMetricFrame = useMemo(() => {
    if (!metricFrame) return [];
    return Object.entries(metricFrame)
      .filter(([, value]) => typeof value === 'number')
      .slice(0, 36);
  }, [metricFrame]);

  return (
    <div className="advanced-panel">
      <div className="advanced-header">
        <div>
          <p className="advanced-eyebrow">Datos completos de MediaPipe</p>
          <h2>Análisis biomecánico avanzado</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="advanced-export-btn" onClick={() => downloadJson(results)}>
            Exportar JSON
          </button>
          <button
            className="advanced-export-btn"
            style={{ background: '#5f5e5a' }}
            onClick={() => setIsExpanded(v => !v)}
          >
            {isExpanded ? 'Colapsar ▲' : 'Expandir ▼'}
          </button>
        </div>
      </div>

      {!isExpanded && (
        <p style={{ fontSize: '0.82rem', color: '#888780', textAlign: 'center', padding: '0.5rem 0' }}>
          Datos de landmarks, cinemática y vector de features del modelo ML
        </p>
      )}

      {isExpanded && (
        <>
          <div className="advanced-summary-grid">
            <SummaryTile label="Landmarks por frame" value={results.landmark_names?.length || 0} />
            <SummaryTile label="Frames analizados" value={results.n_frames || 0} />
            <SummaryTile label="FPS" value={formatValue(results.fps)} />
            <SummaryTile label="Métricas agregadas" value={Object.keys(results.aggregated_metrics || {}).length} />
            <SummaryTile label="Features ML" value={results.feature_vector?.length || 0} />
            <SummaryTile label="Fases detectadas" value={results.phases?.length || 0} />
          </div>

          <Section title="Fases y timing del golpe">
            <div className="phase-grid">
              {(results.phases || []).map(phase => (
                <div key={phase.name} className="phase-card">
                  <strong>{phase.name}</strong>
                  <span>Frames {phase.start_frame}–{phase.end_frame}</span>
                  <span>{phase.start_sec}s – {phase.end_sec}s</span>
                  <em>{phase.duration_sec}s</em>
                </div>
              ))}
            </div>
            <div className="event-grid">
              {Object.entries(results.event_timing || {}).map(([key, value]) => (
                <div key={key}>
                  <span>{key}</span>
                  <strong>{formatValue(value)}</strong>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Métricas agregadas completas">
            <MetricsTable aggregatedMetrics={results.aggregated_metrics} />
          </Section>

          <Section title="Explorador frame a frame">
            <div className="frame-control">
              <label htmlFor="advanced-frame">Frame seleccionado</label>
              <input
                id="advanced-frame"
                type="range"
                min="0"
                max={maxFrame}
                value={selectedFrame}
                onChange={e => setSelectedFrame(Number(e.target.value))}
              />
              <input
                type="number"
                min="0"
                max={maxFrame}
                value={selectedFrame}
                onChange={e => setSelectedFrame(Math.min(Math.max(Number(e.target.value), 0), maxFrame))}
              />
            </div>

            <div className="frame-metric-grid">
              {compactMetricFrame.map(([key, value]) => (
                <div key={key}>
                  <span>{key}</span>
                  <strong>{formatValue(value)}</strong>
                </div>
              ))}
            </div>
          </Section>

          <Section title="33 landmarks del frame seleccionado">
            <LandmarksTable frameData={landmarkFrame} />
          </Section>

          <Section title="Velocidades y aceleraciones articulares">
            <KinematicsTable frameData={kinematicsFrame} />
            <AngleKinematicsTable frameData={kinematicsFrame} />
          </Section>

          <Section title="Vector de entrenamiento del modelo">
            <FeatureVectorTable names={results.feature_names} values={results.feature_vector} />
          </Section>
        </>
      )}
    </div>
  );
}
