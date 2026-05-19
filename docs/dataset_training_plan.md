# Plan de dataset y entrenamiento

## Objetivo

Construir un dataset de golpes de derecha que permita entrenar y evaluar un modelo capaz de estimar la calidad tecnica del gesto a partir de los datos extraidos con MediaPipe.

## Unidad de dato

Cada muestra del dataset debe representar un golpe analizado. Para cada golpe se conservaran:

- Video original.
- Metadatos del video y del jugador/grabacion.
- Features extraidas automaticamente por el backend.
- Etiquetas tecnicas asignadas por criterio experto o semi-experto.

## Etiquetas recomendadas

- `score`: puntuacion numerica de 0 a 100.
- `quality_class`: clase interpretativa derivada o asignada manualmente, por ejemplo `mala`, `aceptable`, `buena`, `excelente`.
- Etiquetas opcionales por dimension: codo, hombro, rodillas, tronco, rotacion, timing, estabilidad y follow-through.
- Notas libres del evaluador.

## Formato recomendado

Usar una estructura mixta:

- `videos/`: videos originales.
- `features/`: un JSON por video con landmarks, metricas, cinemática, fases y vector de entrenamiento.
- `labels.csv`: tabla maestra con identificador de muestra, ruta del video, etiquetas y metadatos.

## Entrenamiento

El modelo no debe entrenarse solo con el video crudo, sino con el vector de features extraido del video. El video se mantiene para trazabilidad, revision humana y reprocesado futuro si cambia el extractor.

Modelos iniciales recomendados:

- Random Forest Regressor para predecir `score`.
- Random Forest Classifier para predecir `quality_class`.
- XGBoost como comparativa posterior.

## Modelos propuestos

La estrategia recomendada es progresiva y explicable:

1. Baseline por reglas biomecanicas.
   - Usa rangos tecnicos de referencia para codo, hombro, rodilla, tronco y otras metricas.
   - Sirve como referencia inicial y como sistema de respaldo cuando no hay modelo entrenado.

2. Random Forest Regressor.
   - Modelo principal para predecir `score` en escala 0-100.
   - Adecuado para datasets pequenos o medianos.
   - Funciona bien con features biomecanicas tabulares.
   - No requiere normalizacion estricta.
   - Permite obtener importancia de variables para explicar la prediccion.

3. Random Forest Classifier.
   - Modelo principal para predecir `quality_class`.
   - Clases sugeridas: `mala`, `mejorable`, `buena`, `excelente`.
   - La clase puede etiquetarse manualmente o derivarse del `score`.

4. XGBoost Regressor y XGBoost Classifier.
   - Modelos comparativos para evaluar si el boosting mejora a Random Forest.
   - Utiles para la parte experimental del TFE.
   - Requieren mas ajuste de hiperparametros y control de sobreajuste.

No se recomienda comenzar con redes neuronales, LSTM, Transformers o CNN sobre video crudo porque requieren muchos mas datos, son menos explicables y aumentan mucho la complejidad del TFE.

Arquitectura de aprendizaje recomendada:

```text
MediaPipe 33 landmarks
        ↓
features biomecanicas y cinematicas
        ↓
baseline por reglas
        ↓
Random Forest Regressor + Classifier
        ↓
comparativa con XGBoost
        ↓
feedback explicable
```

## Evaluacion

- Para regresion: MAE, RMSE y R2.
- Para clasificacion: accuracy, precision, recall y F1.
- Usar importancia de variables para explicar que dimensiones biomecanicas influyen mas en la puntuacion.
