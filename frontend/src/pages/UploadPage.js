import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeVideo } from '../services/api';

const ANALYSIS_STEPS = [
  { id: 'upload',   label: 'Subiendo vídeo',                   icon: '⬆️' },
  { id: 'pose',     label: 'Extrayendo pose con MediaPipe',     icon: '🦾' },
  { id: 'metrics',  label: 'Calculando métricas biomecánicas',  icon: '📐' },
  { id: 'scoring',  label: 'Puntuando con Random Forest',       icon: '🌲' },
  { id: 'feedback', label: 'Generando feedback con Claude AI',  icon: '🤖' },
];

const STATUS = { IDLE: 'idle', UPLOADING: 'uploading', ANALYZING: 'analyzing', DONE: 'done', ERROR: 'error' };

function AnalysisLoader({ uploadProgress, analysisStep }) {
  return (
    <div>
      <div className="loader-header">
        <div className="loader-spinner" />
        <p className="loader-title">Analizando tu golpe…</p>
        <p className="loader-subtitle">Este proceso tarda entre 20 y 40 segundos</p>
      </div>

      {ANALYSIS_STEPS.map((step, i) => {
        const isUploadStep = i === 0;
        let state = 'pending';
        if (isUploadStep) {
          state = uploadProgress < 100 ? 'active' : 'done';
        } else {
          if (analysisStep > i - 1) state = 'done';
          else if (analysisStep === i - 1) state = 'active';
        }

        return (
          <div key={step.id} className={`loader-step step-${state}`}>
            <span className="loader-step-icon">
              {state === 'done' ? '✓' : state === 'active' ? step.icon : '○'}
            </span>
            <div className="loader-step-text">
              <p className="loader-step-label">{step.label}</p>
              {isUploadStep && state === 'active' && (
                <div>
                  <div className="upload-progress-bar">
                    <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <p className="upload-progress-pct">{uploadProgress}%</p>
                </div>
              )}
              {state === 'active' && !isUploadStep && (
                <p className="loader-step-sub">Procesando…</p>
              )}
            </div>
            <div className="loader-step-dot" />
          </div>
        );
      })}
    </div>
  );
}

export default function UploadPage({ onResults }) {
  const [mode,           setMode]           = useState('upload'); // 'upload' | 'camera'
  const [file,           setFile]           = useState(null);
  const [side,           setSide]           = useState('right');
  const [status,         setStatus]         = useState(STATUS.IDLE);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisStep,   setAnalysisStep]   = useState(-1);
  const [error,          setError]          = useState('');
  const stepTimers  = useRef([]);
  const cameraInput = useRef(null);

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) { setFile(accepted[0]); setError(''); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/mp4': [], 'video/quicktime': [], 'video/x-msvideo': [] },
    maxFiles: 1,
    maxSize: 200 * 1024 * 1024,
  });

  const handleCameraChange = (e) => {
    const picked = e.target.files?.[0];
    if (picked) { setFile(picked); setError(''); }
    // Reset input so re-selecting the same file triggers onChange again
    e.target.value = '';
  };

  const handleModeChange = (next) => {
    setMode(next);
    setFile(null);
    setError('');
  };

  const clearStepTimers = () => {
    stepTimers.current.forEach(clearTimeout);
    stepTimers.current = [];
  };

  useEffect(() => () => clearStepTimers(), []);

  const startAnalysisSteps = () => {
    setAnalysisStep(0);
    [0, 6000, 11000, 15000].forEach((delay, i) => {
      const t = setTimeout(() => setAnalysisStep(i), delay);
      stepTimers.current.push(t);
    });
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setStatus(STATUS.UPLOADING);
    setUploadProgress(0);
    setAnalysisStep(-1);
    setError('');
    clearStepTimers();

    try {
      const data = await analyzeVideo(file, side, (pct) => {
        setUploadProgress(pct);
        if (pct === 100) {
          setStatus(STATUS.ANALYZING);
          startAnalysisSteps();
        }
      });
      clearStepTimers();
      setStatus(STATUS.DONE);
      onResults(data);
    } catch (err) {
      clearStepTimers();
      setStatus(STATUS.ERROR);
      setError(err?.response?.data?.detail || 'Error al analizar el vídeo. Inténtalo de nuevo.');
    }
  };

  const isLoading = status === STATUS.UPLOADING || status === STATUS.ANALYZING;

  const dropzoneClass = [
    'dropzone-area',
    isDragActive ? 'drag-active' : '',
    file && mode === 'upload' && !isDragActive ? 'has-file' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <span className="upload-hero-badge">🎾 Análisis con IA</span>
        <h1>Analiza tu técnica</h1>
        <p>Sube o graba un vídeo de tu golpe de derecha y recibe métricas biomecánicas y feedback personalizado en segundos</p>
      </div>

      <div className="upload-body">
        <div className="upload-card">

          {/* Tabs — solo visibles cuando no se está analizando */}
          {!isLoading && (
            <div className="upload-tabs">
              <button
                className={`upload-tab ${mode === 'upload' ? 'active' : ''}`}
                onClick={() => handleModeChange('upload')}
              >
                📁 Subir vídeo
              </button>
              <button
                className={`upload-tab ${mode === 'camera' ? 'active' : ''}`}
                onClick={() => handleModeChange('camera')}
              >
                🎥 Grabar ahora
              </button>
            </div>
          )}

          {/* Input oculto para cámara */}
          <input
            ref={cameraInput}
            type="file"
            accept="video/*"
            capture="camcorder"
            style={{ display: 'none' }}
            onChange={handleCameraChange}
          />

          {!isLoading && (
            <>
              {/* ── Modo subir ── */}
              {mode === 'upload' && (
                <div {...getRootProps()} className={dropzoneClass}>
                  <input {...getInputProps()} />
                  <div className="dropzone-icon-wrap">
                    {file ? '✅' : isDragActive ? '📂' : '🎥'}
                  </div>
                  <p className="dropzone-title">
                    {isDragActive ? 'Suelta aquí' : file ? 'Vídeo listo' : 'Arrastra tu vídeo aquí'}
                  </p>
                  {!file && <p className="dropzone-hint">MP4 · MOV · AVI · máx. 200 MB</p>}
                  {!file && !isDragActive && (
                    <span className="dropzone-tap-hint">📱 Toca para seleccionar desde el móvil</span>
                  )}
                  {file && <p className="dropzone-hint">Toca para cambiar el vídeo</p>}
                </div>
              )}

              {/* ── Modo cámara ── */}
              {mode === 'camera' && (
                <div className={`camera-panel ${file ? 'has-file' : ''}`}>
                  <div className="camera-icon-wrap">
                    {file ? '✅' : '🎬'}
                  </div>
                  <p className="camera-title">
                    {file ? 'Vídeo grabado' : 'Graba tu golpe de derecha'}
                  </p>
                  <p className="camera-hint">
                    {file
                      ? 'Listo para analizar. Pulsa el botón de abajo.'
                      : 'Se abrirá la cámara de tu dispositivo directamente'}
                  </p>
                  <button
                    className="camera-trigger-btn"
                    onClick={() => cameraInput.current?.click()}
                  >
                    {file ? '🔄 Grabar de nuevo' : '📹 Abrir cámara'}
                  </button>
                </div>
              )}

              {/* Chip con el fichero seleccionado — aparece en ambos modos */}
              {file && (
                <div className="file-chip">
                  <span style={{ fontSize: '1.2rem' }}>📄</span>
                  <span className="file-chip-name">{file.name}</span>
                  <span className="file-chip-size">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
                </div>
              )}

              <div className="side-toggle">
                <span className="side-toggle-label">Lado dominante</span>
                <div className="side-pills">
                  <button
                    className={`side-pill ${side === 'right' ? 'active' : ''}`}
                    onClick={() => setSide('right')}
                  >
                    Diestro
                  </button>
                  <button
                    className={`side-pill ${side === 'left' ? 'active' : ''}`}
                    onClick={() => setSide('left')}
                  >
                    Zurdo
                  </button>
                </div>
              </div>
            </>
          )}

          {isLoading && (
            <AnalysisLoader uploadProgress={uploadProgress} analysisStep={analysisStep} />
          )}

          {error && <div className="upload-error">⚠️ {error}</div>}

          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={!file || isLoading}
          >
            {isLoading ? 'Analizando…' : '⚡ Analizar golpe'}
          </button>
        </div>
      </div>
    </div>
  );
}
