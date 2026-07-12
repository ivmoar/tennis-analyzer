# TennisAnalyzer

Sistema inteligente para la evaluación automática de la técnica de golpe de derecha en tenis
mediante estimación de pose con MediaPipe y análisis de vídeo monocular.

Trabajo de Fin de Estudios (TFE) — Máster en Inteligencia Artificial — UNIR  
Autor: Iván Moreno Aranda

---

## Estructura del proyecto

```
tenis_app/
├── backend/                  # API FastAPI + lógica de análisis
│   ├── app/
│   │   ├── api/              # Endpoints REST
│   │   ├── core/             # Configuración y constantes
│   │   ├── models/           # Modelo entrenado (.joblib)
│   │   └── services/
│   │       ├── pose_service.py       # MediaPipe + cálculo de métricas cinemáticas
│   │       ├── scoring_service.py    # Puntuación 0-100 por métrica
│   │       ├── feedback_service.py   # Feedback textual con Claude (Anthropic) + RAG
│   │       └── rag_service.py        # Recuperación de contexto biomecánico (ChromaDB)
│   ├── train_model.py        # Script de etiquetado y entrenamiento (RF + XGBoost)
│   ├── cut_videos.py         # Utilidad para segmentar vídeos desde CSV de cortes
│   └── requirements.txt
├── frontend/                 # Interfaz React + TailwindCSS
│   └── src/
│       ├── components/       # Componentes reutilizables
│       ├── pages/            # Páginas principales
│       └── services/         # Llamadas a la API
└── data/
    ├── raw_videos/           # Vídeos originales (sin segmentar)
    ├── videos/               # Clips individuales de entrenamiento
    ├── cuts/                 # cuts.csv con timestamps y puntuaciones
    └── labels/               # Características extraídas + etiquetas
```

---

## Requisitos previos

- Python 3.10+
- Node.js 18+
- Clave API de Anthropic (para el módulo de feedback textual con Claude)

---

## Puesta en marcha

### 1. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
```

Editar `.env` y añadir la clave de Anthropic:

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-opus-4-5
```

```bash
# Arrancar la API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API REST disponible en: `http://localhost:8000`
- Documentación interactiva (Swagger): `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install

# Opcional: apuntar al backend
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local

npm start
# Interfaz disponible en http://localhost:3000
```

---

## Pipeline de entrenamiento del modelo

El sistema utiliza un modelo supervisado (Random Forest o XGBoost) entrenado con
puntuaciones expertas. El pipeline completo es:

### Opción A — Entrenamiento desde vídeos ya segmentados

```bash
cd backend

# Paso 1: extraer características de los vídeos
python train_model.py --mode label --videos_dir data/videos

# Paso 2: abrir data/labels/features.csv y completar la columna 'score' (0–100)

# Paso 3: entrenar y comparar RF vs XGBoost
python train_model.py --mode train --labels data/labels/features.csv

# Paso 4: métricas de evaluación (MAE, RMSE, R²)
python train_model.py --mode evaluate --labels data/labels/features.csv
```

### Opción B — Segmentación desde vídeos largos (método utilizado en el TFE)

```bash
# Paso 1: rellenar data/cuts/cuts.csv con formato:
#   video_file, start_time, end_time, score
#   rally_01.mp4, 0:05, 0:08, 75

# Paso 2: cortar los vídeos
python cut_videos.py --cut --videos_dir data/raw_videos

# Paso 3: extraer características y etiquetar desde los cortes
python train_model.py --mode label --videos_dir data/videos

# Paso 4: entrenar
python train_model.py --mode train --labels data/labels/labels_from_cuts.csv
```

El modelo entrenado se guarda en `app/models/scoring_model.joblib`.

---

## Endpoint principal

```
POST /analyze
Content-Type: multipart/form-data

Campo: file (vídeo MP4/MOV, mín. 720p)
```

Respuesta:

```json
{
  "score": 72.4,
  "metrics": {
    "elbow_angle": { "value": 148.2, "score": 85, "status": "ok" },
    "shoulder_angle": { "value": 95.1, "score": 80, "status": "ok" },
    "knee_angle": { "value": 142.3, "score": 70, "status": "warning" },
    "trunk_tilt": { "value": 8.7, "score": 90, "status": "ok" },
    "hip_separation": { "value": 34.5, "score": 75, "status": "ok" },
    "wrist_speed": { "value": 320.1, "score": 78, "status": "ok" }
  },
  "feedback": {
    "summary": "Golpe con buena técnica general...",
    "issues": ["Ligera falta de flexión de rodillas"],
    "tips": ["Trabaja el split-step antes del golpe"]
  }
}
```

---

## Métricas biomecánicas evaluadas

| Métrica | Descripción | Rango óptimo | Peso |
|---|---|---|---|
| `elbow_angle` | Ángulo de codo en el impacto | 100–160° | 0.25 |
| `shoulder_angle` | Elevación del brazo dominante | 60–120° | 0.20 |
| `knee_angle` | Flexión de rodillas | 130–170° | 0.20 |
| `trunk_tilt` | Inclinación lateral del tronco | 0–20° | 0.15 |
| `hip_separation` | Rotación relativa cadera-hombros | 20–60° | 0.10 |
| `wrist_speed` | Velocidad angular de muñeca | 200–600 °/s | 0.10 |

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Estimación de pose | MediaPipe Pose 0.10.35 (BlazePose, 33 landmarks) |
| Backend | FastAPI 0.111 |
| Frontend | React 18 + TailwindCSS |
| Modelo de puntuación | Random Forest / XGBoost (scikit-learn) |
| Feedback textual | Claude (Anthropic API) |
| Recuperación de contexto | ChromaDB (RAG en memoria) |
| Procesamiento de vídeo | OpenCV 4.9 |

---

## Licencia

Proyecto académico desarrollado para el TFE del Máster en IA de UNIR.  
MediaPipe: Apache License 2.0.
