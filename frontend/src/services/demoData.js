// Datos de demo precalculados para la landing page.
// Representan un jugador con técnica media: codo y rodilla correctos,
// hombro y tronco ligeramente por encima del rango óptimo.

const N = 75; // frames a 30fps ≈ 2.5 s

function sin(x) { return Math.sin(x); }
function round1(v) { return Math.round(v * 10) / 10; }

// Series deterministas (sin Math.random) para que el demo siempre sea igual
const metricsSeries = Array.from({ length: N }, (_, i) => {
  const t  = i / N;
  const s1 = sin(Math.PI * t);          // sube y baja (0→1→0)
  const s2 = sin(2 * Math.PI * t);      // oscila dos veces

  return {
    elbow_angle:    round1(120 + 12 * s1 - 4 * s2),
    shoulder_angle: round1(118 + 16 * s1 + 5 * s2),   // media ~122° → "Alto"
    knee_angle:     round1(148 -  7 * s1 + 2 * s2),
    trunk_tilt:     round1( 18 + 10 * s1 + 1.5 * Math.abs(s2)), // media ~22° → "Alto"
    torso_rotation: round1( 22 + 35 * s1),
    arm_extension:  round1( 62 + 28 * s1),
    hip_separation: round1( 26 + 14 * s1),
  };
});

export const demoResults = {
  video_id: 'demo',
  annotated_video_url: null,   // sin vídeo en modo demo

  n_frames: N,
  fps: 30,
  detection_rate: 0.96,
  scoring_method: 'rules',

  score: 71.4,

  breakdown: {
    elbow_angle: {
      label: 'Extensión de codo',
      value: 126.2,
      score: 100,
      range: [100, 160],
      status: 'ok',
    },
    shoulder_angle: {
      label: 'Posición de hombro',
      value: 124.8,
      score: 70.3,
      range: [60, 120],
      status: 'high',
    },
    knee_angle: {
      label: 'Flexión de rodillas',
      value: 144.6,
      score: 100,
      range: [130, 170],
      status: 'ok',
    },
    trunk_tilt: {
      label: 'Inclinación de tronco',
      value: 23.4,
      score: 66.0,
      range: [0, 20],
      status: 'high',
    },
  },

  feedback: {
    summary:
      'Tu golpe de derecha muestra una técnica en desarrollo con una base sólida: ' +
      'la extensión de codo y la flexión de rodillas están dentro de los rangos óptimos. ' +
      'Los dos aspectos a trabajar son la altura del hombro y la inclinación del tronco.',
    issues: [
      'El hombro dominante alcanza 124.8° de media, superando el rango óptimo de 60-120°. ' +
      'Esto dificulta el giro de muñeca en el punto de impacto y reduce el control de la bola.',
      'La inclinación lateral del tronco es de 23.4°, por encima de los 20° recomendados. ' +
      'Puede indicar un desplazamiento del peso hacia adelante o falta de equilibrio en el swing.',
    ],
    tips: [
      'Durante el backswing, mantén el codo levemente flexionado y el hombro por debajo ' +
      'de la línea de la oreja. Practica el movimiento lento frente a un espejo para interiorizar la posición.',
      'Inicia el movimiento con una ligera flexión de rodillas para bajar el centro de gravedad. ' +
      'Un tronco más vertical mejora la estabilidad y la transferencia de energía desde las piernas.',
    ],
  },

  phases: [
    { name: 'preparación',    start_frame: 0,  end_frame: 13, start_sec: 0.0,  end_sec: 0.43, duration_sec: 0.43 },
    { name: 'backswing',      start_frame: 14, end_frame: 36, start_sec: 0.47, end_sec: 1.2,  duration_sec: 0.73 },
    { name: 'impacto',        start_frame: 37, end_frame: 51, start_sec: 1.23, end_sec: 1.7,  duration_sec: 0.47 },
    { name: 'follow-through', start_frame: 52, end_frame: 74, start_sec: 1.73, end_sec: 2.47, duration_sec: 0.74 },
  ],

  event_timing: {
    max_torso_rotation_frame: 38,
    max_arm_speed_frame: 41,
    impact_frame: 44,
  },

  metrics_series: metricsSeries,

  // Campos mínimos para AdvancedAnalysisPanel (colapsado por defecto)
  aggregated_metrics: {
    elbow_angle:    { mean: 126.2, std: 6.1, min: 110.4, max: 138.5, p25: 121.0, p50: 126.5, p75: 131.8, range: 28.1 },
    shoulder_angle: { mean: 124.8, std: 7.3, min: 110.1, max: 138.2, p25: 119.3, p50: 124.6, p75: 130.4, range: 28.1 },
    knee_angle:     { mean: 144.6, std: 4.2, min: 136.2, max: 152.8, p25: 141.5, p50: 144.4, p75: 147.9, range: 16.6 },
    trunk_tilt:     { mean: 23.4,  std: 3.8, min: 16.2,  max: 31.5,  p25: 20.2,  p50: 23.1,  p75: 26.4,  range: 15.3 },
    torso_rotation: { mean: 39.5,  std: 15.1, min: 22.0, max: 57.0,  p25: 26.8,  p50: 39.2,  p75: 52.1,  range: 35.0 },
  },

  landmark_names: [],
  landmarks_series: [],
  kinematics_series: [],
  feature_vector: [],
  feature_names: [],
};
