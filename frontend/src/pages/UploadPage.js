import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeVideo } from '../services/api';

const styles = {
  header: {
    textAlign: 'center',
    maxWidth: '560px',
  },
  logo: {
    fontSize: '2.5rem',
    marginBottom: '0.5rem',
  },
  subtitle: {
    color: '#5f5e5a',
    marginTop: '0.5rem',
    fontSize: '1rem',
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '2rem',
    width: '100%',
    maxWidth: '560px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  dropzone: (isDragActive, hasFile) => ({
    border: `2px dashed ${isDragActive ? '#1D9E75' : hasFile ? '#378ADD' : '#d3d1c7'}`,
    borderRadius: '12px',
    padding: '2.5rem 1.5rem',
    textAlign: 'center',
    cursor: 'pointer',
    background: isDragActive ? '#E1F5EE' : hasFile ? '#E6F1FB' : '#fafaf9',
    transition: 'all 0.2s',
  }),
  dropIcon: {
    fontSize: '2.5rem',
    marginBottom: '0.75rem',
  },
  dropText: {
    fontWeight: '600',
    fontSize: '1rem',
    color: '#1a1a18',
  },
  dropHint: {
    fontSize: '0.85rem',
    color: '#888780',
    marginTop: '0.25rem',
  },
  fileInfo: {
    background: '#E6F1FB',
    borderRadius: '8px',
    padding: '0.75rem 1rem',
    marginTop: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    fontSize: '0.9rem',
  },
  fileName: {
    fontWeight: '500',
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  options: {
    marginTop: '1.25rem',
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '1rem',
    fontSize: '0.9rem',
  },
  select: {
    padding: '0.4rem 0.75rem',
    borderRadius: '8px',
    border: '1px solid #d3d1c7',
    fontFamily: 'inherit',
    fontSize: '0.9rem',
    background: '#fff',
    cursor: 'pointer',
  },
  btn: {
    width: '100%',
    marginTop: '1.5rem',
    padding: '0.85rem',
    fontSize: '1rem',
    fontWeight: '600',
    color: '#fff',
    background: '#1D9E75',
    borderRadius: '10px',
  },
  progress: {
    marginTop: '1.25rem',
  },
  progressBar: (pct) => ({
    height: '6px',
    borderRadius: '3px',
    background: '#e5e5e3',
    overflow: 'hidden',
    marginTop: '0.5rem',
  }),
  progressFill: (pct) => ({
    height: '100%',
    width: `${pct}%`,
    background: '#1D9E75',
    borderRadius: '3px',
    transition: 'width 0.3s',
  }),
  error: {
    background: '#FCEBEB',
    color: '#A32D2D',
    borderRadius: '8px',
    padding: '0.75rem 1rem',
    marginTop: '1rem',
    fontSize: '0.9rem',
  },
  step: {
    flex: 1,
    background: '#fff',
    borderRadius: '12px',
    padding: '1rem',
    textAlign: 'center',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  stepNum: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    background: '#E1F5EE',
    color: '#0F6E56',
    fontWeight: '700',
    fontSize: '0.85rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 0.5rem',
  },
  stepText: {
    fontSize: '0.8rem',
    color: '#5f5e5a',
  },
};

const STATUS = {
  IDLE:       'idle',
  UPLOADING:  'uploading',
  ANALYZING:  'analyzing',
  DONE:       'done',
  ERROR:      'error',
};

export default function UploadPage({ onResults }) {
  const [file,     setFile]     = useState(null);
  const [side,     setSide]     = useState('right');
  const [status,   setStatus]   = useState(STATUS.IDLE);
  const [progress, setProgress] = useState(0);
  const [error,    setError]    = useState('');

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) { setFile(accepted[0]); setError(''); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/mp4': [], 'video/quicktime': [], 'video/x-msvideo': [] },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024,
  });

  const handleAnalyze = async () => {
    if (!file) return;
    setStatus(STATUS.UPLOADING);
    setProgress(0);
    setError('');
    try {
      const data = await analyzeVideo(file, side, (pct) => {
        setProgress(pct);
        if (pct === 100) setStatus(STATUS.ANALYZING);
      });
      setStatus(STATUS.DONE);
      onResults(data);
    } catch (err) {
      setStatus(STATUS.ERROR);
      setError(err?.response?.data?.detail || 'Error al analizar el vídeo. Inténtalo de nuevo.');
    }
  };

  const isLoading = status === STATUS.UPLOADING || status === STATUS.ANALYZING;
  const statusLabel = status === STATUS.UPLOADING
    ? `Subiendo... ${progress}%`
    : status === STATUS.ANALYZING
    ? 'Analizando pose y calculando métricas...'
    : '';

  return (
    <div className="page-upload">
      <div style={styles.header}>
        <div style={styles.logo}>🎾</div>
        <h1>TennisAnalyzer</h1>
        <p style={styles.subtitle}>
          Análisis automático de la técnica de golpe de derecha mediante visión por computador e IA
        </p>
      </div>

      <div className="upload-steps">
        {[
          { n: '1', text: 'Sube un vídeo de tu golpe de derecha' },
          { n: '2', text: 'El sistema analiza tu técnica con IA' },
          { n: '3', text: 'Recibe métricas y feedback personalizado' },
        ].map(s => (
          <div key={s.n} style={styles.step}>
            <div style={styles.stepNum}>{s.n}</div>
            <p style={styles.stepText}>{s.text}</p>
          </div>
        ))}
      </div>

      <div style={styles.card}>
        <div {...getRootProps()} style={styles.dropzone(isDragActive, !!file)}>
          <input {...getInputProps()} />
          <div style={styles.dropIcon}>{file ? '📹' : '⬆️'}</div>
          <p style={styles.dropText}>
            {isDragActive ? 'Suelta el vídeo aquí' : 'Arrastra tu vídeo aquí'}
          </p>
          <p style={styles.dropHint}>o haz clic para seleccionarlo · MP4, MOV, AVI · máx. 100 MB</p>
        </div>

        {file && (
          <div style={styles.fileInfo}>
            <span>📄</span>
            <span style={styles.fileName}>{file.name}</span>
            <span style={{ color: '#888780', fontSize: '0.8rem' }}>
              {(file.size / 1024 / 1024).toFixed(1)} MB
            </span>
          </div>
        )}

        <div style={styles.options}>
          <label style={{ fontWeight: '500' }}>Lado dominante:</label>
          <select
            style={styles.select}
            value={side}
            onChange={e => setSide(e.target.value)}
            disabled={isLoading}
          >
            <option value="right">Diestro (derecha)</option>
            <option value="left">Zurdo (izquierda)</option>
          </select>
        </div>

        {isLoading && (
          <div style={styles.progress}>
            <p style={{ fontSize: '0.85rem', color: '#5f5e5a' }}>{statusLabel}</p>
            <div style={styles.progressBar(progress)}>
              <div style={styles.progressFill(status === STATUS.ANALYZING ? 100 : progress)} />
            </div>
          </div>
        )}

        {error && <div style={styles.error}>⚠️ {error}</div>}

        <button
          style={styles.btn}
          onClick={handleAnalyze}
          disabled={!file || isLoading}
        >
          {isLoading ? 'Analizando...' : 'Analizar golpe'}
        </button>
      </div>
    </div>
  );
}
