# Resultados del modelo de puntuación — iteración v1 (dataset piloto)

> Material para la memoria del TFE. Modelo de regresión que predice una
> puntuación técnica (0–100) del golpe de derecha a partir de características
> biomecánicas extraídas con visión por computador.

## 1. Descripción del dataset

### 1.1 Grabación

Los vídeos son grabaciones propias de sesiones de entrenamiento, segmentadas
posteriormente en cortes de un solo golpe.

| Característica | Valor real (medido de los ficheros) |
|---|---|
| Dispositivo | iPhone (91 % de los clips); una minoría procede de otra fuente de menor resolución |
| Orientación | Vertical (retrato) en el 100 % de los clips |
| Resolución | 2160×3840 (4K) en 87 clips (91 %); 480×848 y 464×832 en los 8 restantes |
| Frame rate | ~60 fps en la mayoría (53 a 60 fps, 31 a ~59,9 fps); 3 clips a 30 fps |
| Duración por corte | 1,0 – 9,0 s (media 2,2 s); un golpe por corte |
| Ángulo de cámara | `[COMPLETAR: p. ej. lateral / frontal respecto al jugador]` |
| Distancia al jugador | `[COMPLETAR: distancia aproximada en metros]` |
| Soporte | `[COMPLETAR: trípode / a mano]` |

*(Los tres últimos campos son condiciones físicas de grabación que deben
completarse manualmente; el resto se ha medido directamente de los archivos.)*

### 1.2 Composición y etiquetado

| Concepto | Valor |
|---|---|
| Cortes grabados | 95 |
| Cortes **usables** (pose detectada por MediaPipe) | **93** |
| Descartados | 2 |
| Motivo del descarte | MediaPipe no detectó pose fiable en `VIDEO-2025-10-14-19-32-56_004` y `VIDEO-2025-10-14-19-32-57_002` (transición sin jugador claramente visible) |
| Tasa de detección de pose (usables) | mayoría 100 %; mínimo 76,5 % |
| **Anotador** | **Único (el autor).** Puntuación 0–100 subjetiva por inspección visual |
| Puntuación media / desv. típica | 68,5 / 16,8 |
| Rango observado | 20 – 98 |

> **Limitación de validez (composición del dataset).** El conjunto es reducido
> (93 muestras), grabado por un solo jugador y **etiquetado por un único
> anotador**, por lo que la variable objetivo contiene ruido subjetivo (no hay
> acuerdo inter-anotador que acote el error irreducible). Estas condiciones
> limitan la capacidad de generalización y deben tenerse en cuenta al
> interpretar las métricas: se trata de un **dataset piloto / prueba de
> concepto**, no de un conjunto de validación definitivo.

## 2. Metodología

```
Vídeo → MediaPipe Pose → métricas biomecánicas por fotograma →
agregación estadística → vector de características → modelo de regresión →
puntuación técnica (0–100)
```

- **Características:** por cada métrica biomecánica se calculan 8 estadísticos de
  resumen del vídeo (media, desv. típica, mín, máx, percentiles 25/50/75, rango).
- **Modelos:** Random Forest y XGBoost (regresores).
- **Validación:** validación cruzada de 5 particiones (5-fold). Métricas: MAE y
  RMSE (en puntos sobre 100) y R².

## 3. Resultados

### Tabla 5 — MAE, RMSE y R² por modelo y configuración (CV 5-fold)

| Configuración | Modelo | MAE | RMSE | R² |
|---|---|---|---|---|
| 936 características | Random Forest | 11,09 | 13,69 | +0,078 |
| 936 características | XGBoost | 13,41 | 16,04 | −0,252 |
| **10 características (Set A)** | **Random Forest** | **9,49** | **12,69** | **+0,171** |
| 10 características (Set A) | XGBoost | 10,64 | 15,02 | −0,076 |
| *Baseline (predecir la media, 68,5)* | — | *13,03* | *16,75* | *0,000* |

**Lectura honesta de los resultados:**

- **El R² es bajo en todos los casos**, como cabía esperar con un MAE de ~9–11
  sobre una escala 0–100 y un dataset piloto. El mejor modelo (Random Forest con
  10 características) explica solo una fracción de la varianza (R² CV = +0,17).
  XGBoost obtiene **R² negativo**: rinde peor que predecir la media.
- Aun así, el Random Forest con 10 características **mejora claramente el
  baseline** en las tres métricas, lo que confirma que hay señal aprendible.
- La reducción de 936 a 10 características mejora MAE (11,09 → 9,49), RMSE
  (13,69 → 12,69) y R² (+0,078 → +0,171): el problema del modelo inicial era el
  **exceso de dimensionalidad** (sección 5), no el algoritmo.

### 3.1 Estabilidad — MAE por partición (Random Forest, 10 características)

| Fold | 1 | 2 | 3 | 4 | 5 | Media ± σ |
|---|---|---|---|---|---|---|
| MAE | 9,24 | 5,52 | 10,18 | 12,11 | 10,43 | **9,49 ± 2,19** |

El error es razonablemente estable entre particiones (rango 5,5–12,1). La
variabilidad restante es coherente con el pequeño tamaño de cada fold (~18-19
muestras).

### 3.2 Predicho vs real (out-of-fold) y análisis de errores

Predicciones out-of-fold del modelo elegido (Random Forest, 10 características),
es decir, cada vídeo predicho por el fold en que **no** participó en el
entrenamiento. Datos completos para el scatter en **`predicciones_oof.csv`**.

| Métrica (OOF agrupado, 93 vídeos) | Valor |
|---|---|
| MAE | 9,45 |
| RMSE | 13,15 |
| R² | +0,383 |

*(El R² agrupado sobre los 93 puntos, +0,38, es superior al R² medio por fold de
la Tabla 5, +0,17, porque este último promedia el R² de particiones pequeñas,
métricamente inestable. Ambos se reportan por transparencia.)*

**Los 10 mayores errores:**

| Vídeo | Real | Predicho | Error |
|---|---|---|---|
| IMG_2675_003 | 30 | 81,0 | +51,0 |
| IMG_2675_004 | 37 | 74,5 | +37,5 |
| IMG_2656_005 | 30 | 66,6 | +36,6 |
| IMG_2663_005 | 40 | 76,1 | +36,1 |
| IMG_2675_002 | 20 | 51,1 | +31,1 |
| IMG_2675_013 | 70 | 41,8 | −28,2 |
| IMG_2393_003 | 50 | 71,0 | +21,0 |
| VIDEO-…-32-57_001 | 92 | 71,1 | −20,9 |
| VIDEO-…-32-56_002 | 90 | 69,6 | −20,4 |
| IMG_2675_011 | 60 | 39,9 | −20,1 |

**Patrón de error: regresión hacia la media.** El modelo **sobreestima los
golpes malos** (notas reales 20–40 predichas como 50–81) y **subestima los
excelentes** (90–92 predichos como ~70). Es el comportamiento típico de un
regresor con poca señal y pocos datos: ante la incertidumbre, tiende a predecir
valores cercanos a la media (68,5). Los peores fallos se concentran en golpes de
puntuación baja, de los que el dataset tiene menos ejemplos, lo que refuerza la
necesidad de ampliar el conjunto (sección 6.2), especialmente en los extremos de
la escala.

## 4. Importancia de características (Random Forest, 936 características, top 15)

Para la gráfica de barras y como justificación de la selección a 10 (sección
6.1).

| # | Característica | Importancia |
|---|---|---|
| 1 | shoulder_line_angle_mean | 0,1340 |
| 2 | opp_elbow_angle_p50 | 0,1022 |
| 3 | hand_to_opp_shoulder_distance_max | 0,0786 |
| 4 | torso_rotation_mean | 0,0407 |
| 5 | hand_to_opp_shoulder_distance_range | 0,0260 |
| 6 | foot_alignment_p75 | 0,0245 |
| 7 | opp_knee_angle_p25 | 0,0225 |
| 8 | opp_knee_angle_p50 | 0,0188 |
| 9 | opp_elbow_angle_p25 | 0,0180 |
| 10 | body_scale_px_std | 0,0154 |
| 11 | opp_elbow_angle_mean | 0,0141 |
| 12 | hand_to_opp_shoulder_distance_min | 0,0134 |
| 13 | right_hip_vy_p75 | 0,0132 |
| 14 | hip_separation_p75 | 0,0127 |
| 15 | shoulder_angle_p75 | 0,0089 |

La importancia está muy repartida (la principal apenas 0,134 y decae rápido) y
aparecen varias características redundantes (mismo eje biomecánico en distintos
percentiles) y ruidosas (`body_scale_px_std`, `right_hip_vy_p75`), síntoma del
sobreajuste descrito en la sección 5.

## 5. Limitación principal: sobreparametrización

| | |
|---|---|
| Nº de características | **936** (117 métricas × 8 estadísticos) |
| Nº de muestras | 93 |
| Ratio muestras / característica | **≈ 0,1** |

La regla práctica recomienda **≥ 10 muestras por característica**; aquí ocurre lo
contrario (≈ 10 características por muestra). Con 936 dimensiones y 93 muestras el
modelo dispone de margen para sobreajustar. Además, buena parte de las 936 son
coordenadas de píxel crudas y velocidades por eje, dependientes de la cámara y de
escaso significado biomecánico.

## 6. Selección de características y trabajo futuro

### 6.1 Características seleccionadas (10)

Se seleccionaron 10 características que combinan **interpretabilidad
biomecánica** —coincidentes con la base de conocimiento del feedback (RAG)— y
**capacidad discriminativa empírica** (presencia entre las más importantes de la
sección 4):

| # | Característica | Dimensión biomecánica |
|---|---|---|
| 1 | elbow_angle_mean | Ángulo de codo (brazo dominante) |
| 2 | shoulder_angle_mean | Elevación de hombro (dominante) |
| 3 | knee_angle_mean | Flexión de rodilla |
| 4 | trunk_tilt_mean | Inclinación del tronco |
| 5 | torso_rotation_max | Rotación cadera-tronco (cadena cinética) |
| 6 | wrist_speed_max | Velocidad de muñeca (potencia) |
| 7 | shoulder_line_angle_mean | Orientación de la línea de hombros |
| 8 | hand_to_opp_shoulder_distance_max | Extensión/cruce del brazo |
| 9 | opp_elbow_angle_p50 | Ángulo de codo (brazo no dominante) |
| 10 | foot_alignment_p75 | Orientación del apoyo |

Esta reducción produce el modelo de la Tabla 5 (Random Forest, MAE 9,49).

### 6.2 Trabajo futuro (por orden de impacto esperado)

1. **Ampliación del dataset.** Palanca principal: incorporar más cortes
   (objetivo orientativo 150–200), con especial atención a los **extremos de la
   escala** (golpes muy buenos y muy malos), donde el modelo falla más.
2. **Características alineadas al instante de impacto.** Sustituir los
   estadísticos globales del vídeo por los valores en el fotograma de golpeo,
   detectado mediante seguimiento de la pelota (TrackNet), para aumentar la
   capacidad discriminativa respecto al momento de contacto.

## 7. Modelo de clasificación por niveles (Nivel 3, 4 categorías)

**No se ha entrenado.** En esta iteración solo existe el modelo de **regresión**
(puntuación 0–100) descrito arriba. No se ha entrenado ningún
`RandomForestClassifier` ni se han reportado accuracy ni matriz de confusión.

Aclaración: los términos `nivel_principiante / nivel_intermedio / nivel_avanzado`
que aparecen en el código pertenecen a la **base de conocimiento del feedback
(RAG)** —son documentos de contexto para el LLM, 3 niveles descriptivos— y **no
constituyen un clasificador entrenado**. Un clasificador de categorías es una
posible extensión futura (bastaría con discretizar la puntuación en categorías y
entrenar sobre las mismas características), pendiente de definir los umbrales de
las categorías.

## 8. Estado del sistema desplegado

Independientemente del modelo (que aún **no** está en producción; el scoring
funciona por reglas), el sistema desplegado en `https://ivanmorenoaranda.com/TFM`
incorpora en esta fase:

- **Feedback fundamentado (RAG).** El texto se genera con un LLM sobre contexto
  biomecánico recuperado de una base de conocimiento (ChromaDB), basada en
  literatura (Elliott et al., 2003; Landlinger et al., 2012).
- **Validación de contenido (YOLOv8).** Antes de puntuar se verifica que el
  vídeo contiene un golpe real: cuerpo visible, raqueta y pelota detectadas y
  proximidad raqueta-pelota en la ventana de impacto.
