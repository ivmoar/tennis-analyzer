# TennisAnalyzer

Sistema inteligente para la evaluación automática de la técnica de golpe de derecha en tenis mediante estimación de pose y análisis de vídeo monocular.

## Estructura del proyecto

```
tenis_app/
├── backend/                  # API FastAPI + lógica de análisis
│   ├── app/
│   │   ├── api/              # Endpoints REST
│   │   ├── core/             # Configuración
│   │   ├── models/           # Modelo Random Forest (generado al entrenar)
│   │   └── services/         # Lógica de negocio
│   │       ├── pose_service.py       # MediaPipe + cálculo de métricas
│   │       ├── scoring_service.py    # Puntuación 0-100
│   │       └── feedback_service.py   # Generación de feedback con LLM
│   ├── train_model.py        # Script de etiquetado y entrenamiento
│   └── requirements.txt
├── frontend/                 # Interfaz React
│   └── src/
│       ├── components/       # Componentes reutilizables
│       ├── pages/            # Páginas principales
│       └── services/         # Llamadas a la API
└── data/
    ├── videos/               # Vídeos de entrenamiento
    └── labels/               # Etiquetas y características extraídas
```

## Puesta en marcha

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Mac/Linux
pip install -r requirements.txt

cp .env.example .env
# Edita .env y añade tu ANTHROPIC_API_KEY

uvicorn app.main:app --reload
# API disponible en http://localhost:8000
# Documentación en http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local       # opcional; apunta al backend local
npm start
# App disponible en http://localhost:3000
```

## Entrenamiento del modelo

```bash
cd backend

# 1. Coloca los vídeos en data/videos/
# 2. Extrae características y genera archivo de etiquetas
python train_model.py --mode label --videos_dir data/videos

# 3. Abre data/labels/labels.csv y rellena la columna 'score' (0-100)
#    con tu valoración experta de cada golpe

# 4. Entrena el modelo
python train_model.py --mode train

# 5. Evalúa el modelo
python train_model.py --mode evaluate
```

## Tecnologías

| Componente | Tecnología |
|---|---|
| Estimación de pose | MediaPipe Pose 0.10.35 |
| Backend | FastAPI 0.111 |
| Frontend | React 18 |
| Modelo de puntuación | Random Forest (scikit-learn) |
| Feedback textual | Claude (Anthropic API) |
| Procesamiento de vídeo | OpenCV 4.9 |
