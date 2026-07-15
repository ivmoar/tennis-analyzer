# Resultados del modelo de puntuación

> Material para la memoria del TFE. Modelo de regresión que predice una
> puntuación técnica (0–100) del golpe de derecha a partir de características
> biomecánicas extraídas con visión por computador.
>
> **Este documento recoge dos iteraciones.** Las secciones 1–8 describen la
> **iteración v1** (dataset piloto, 93 muestras, modelo *no* desplegado). La
> **sección 9** documenta la **iteración v2** (dataset ampliado a 135 muestras,
> modelo **desplegado en producción** el 15/07/2026) e introduce una corrección
> metodológica importante en la validación cruzada (GroupKFold).

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

## 8. Estado del sistema desplegado (durante la iteración v1)

> En la iteración v1 el modelo **no** estaba en producción (el scoring funcionaba
> por reglas). Esto cambió en la iteración v2 (sección 9.6). El resto de esta
> sección describe los componentes que ya estaban desplegados en v1.

El sistema desplegado en `https://ivanmorenoaranda.com/TFM` incorpora:

- **Feedback fundamentado (RAG).** El texto se genera con un LLM sobre contexto
  biomecánico recuperado de una base de conocimiento (ChromaDB), basada en
  literatura (Elliott et al., 2003; Landlinger et al., 2012).
- **Validación de contenido (YOLOv8).** Antes de puntuar se verifica que el
  vídeo contiene un golpe real: cuerpo visible, raqueta y pelota detectadas y
  proximidad raqueta-pelota en la ventana de impacto.

---

## 9. Iteración v2 — dataset ampliado y modelo desplegado

Segunda iteración (15/07/2026): se amplía el dataset, se conserva la selección
de 10 características (Set A) y se **despliega el modelo en producción**. Además
se corrige la metodología de validación cruzada, lo que revela una estimación
del error más honesta que la de v1.

### 9.1 Dataset ampliado

| Concepto | v1 (piloto) | **v2** |
|---|---|---|
| Cortes grabados | 95 | 136 |
| Cortes **usables** (pose detectada) | 93 | **135** |
| Descartados | 2 | 1 (`VIDEO-…-32-57__0-03_0-05`, sin pose fiable) |
| Vídeos fuente | 15 | **18** |
| Puntuación media / desv. típica | 68,5 / 16,8 | **74,2 / 19,6** |
| Rango observado | 20 – 98 | **15 – 100** |

Los cortes nuevos amplían deliberadamente los **extremos de la escala** (se
añaden golpes de jugadores profesionales, puntuados 93–100, y varios golpes
deficientes por debajo de 40), atendiendo a la recomendación de la sección 6.2.
El etiquetado sigue siendo de **un único anotador** (misma limitación de validez
que en v1, sección 1.2).

### 9.2 Corrección metodológica: validación cruzada por grupos

En v1 la validación cruzada 5-fold repartía los cortes **sin tener en cuenta su
vídeo de origen**. Como de un mismo vídeo fuente se extraen varios cortes
(golpes de la misma sesión, jugador, cámara e iluminación), esto permite que
clips muy parecidos caigan a la vez en entrenamiento y test → **fuga de
información** y una estimación del error **optimista**.

La validación correcta para esta estructura de datos es **GroupKFold agrupando
por vídeo fuente**: todos los cortes de un mismo vídeo permanecen juntos en la
misma partición. Así se mide lo que realmente importa: la capacidad de
generalizar a **una grabación nueva no vista**.

La Tabla 6 muestra el mismo modelo (Random Forest, 10 características, 135
muestras) bajo los tres esquemas, para dejar explícito el efecto:

#### Tabla 6 — Efecto del esquema de validación (Random Forest, Set A, n=135)

| Esquema de CV (5-fold) | MAE | RMSE | R² | Interpretación |
|---|---|---|---|---|
| KFold barajado | 9,53 | 13,77 | +0,505 | **Optimista** (fuga: cortes del mismo vídeo en train y test) |
| KFold sin barajar | 10,22 | — | — | Intermedio (el que reporta `train_model.py` por defecto) |
| **GroupKFold por vídeo fuente** | **11,73 ± 2,31** | **15,84** | **−0,017** | **Honesto** (generalizar a una grabación nueva) |

> **Lectura.** La estimación honesta del error (GroupKFold) es **MAE ≈ 11,7
> puntos**, notablemente peor que la de v1 (9,49). No es un empeoramiento del
> modelo, sino una **medición más rigurosa**: el 9,49 de v1 —calculado sin
> agrupar— estaba inflado por la misma fuga. El R² medio por fold es ≈ 0: al
> enfrentarse a un vídeo completamente nuevo, el modelo apenas supera a predecir
> la media dentro de ese vídeo. Con solo 18 vídeos fuente y un único anotador,
> es el resultado esperable de una **prueba de concepto**.

### 9.3 Comparativa de configuraciones (GroupKFold, n=135)

#### Tabla 7 — MAE por modelo y configuración (GroupKFold 5-fold, honesto)

| Configuración | Modelo | MAE | Baseline |
|---|---|---|---|
| 10 características (Set A) | **Random Forest** | **11,73** | 16,09 |
| 10 características (Set A) | XGBoost | 11,81 | 16,09 |

Aun con la validación honesta, el Random Forest **reduce el MAE ~27 % sobre el
baseline** (predecir la media, 16,09), lo que confirma que sigue habiendo señal
aprendible. Se conserva el Random Forest como modelo de producción.

### 9.4 Errores mayores (out-of-fold, GroupKFold)

El patrón de **regresión hacia la media** de v1 se mantiene: el modelo
sobreestima los golpes malos y subestima los excelentes. Los mayores errores se
concentran en los extremos recién añadidos:

| Vídeo (corte) | Real | Predicho | Error |
|---|---|---|---|
| Sinner (0:54) | 15 | 77,0 | +62,0 |
| IMG_2663 (0:14) | 29 | 78,1 | +49,1 |
| Sinner (1:54) | 45 | 86,1 | +41,1 |
| IMG_2675 (0:20) | 30 | 70,8 | +40,8 |
| IMG_2656 (0:11) | 30 | 68,1 | +38,1 |

Los golpes profesionales de puntuación deliberadamente baja (un *slice* defensivo
de Sinner puntuado 15) son los peor predichos: el modelo, entrenado
mayoritariamente con derechas de amateur de gama media, no reconoce la mecánica
atípica y regresa hacia la media.

### 9.5 Importancia de características (Random Forest, Set A, n=135)

| # | Característica | Importancia |
|---|---|---|
| 1 | wrist_speed_max | 0,397 |
| 2 | opp_elbow_angle_p50 | 0,149 |
| 3 | hand_to_opp_shoulder_distance_max | 0,149 |
| 4 | shoulder_line_angle_mean | 0,076 |
| 5 | knee_angle_mean | 0,059 |
| 6 | foot_alignment_p75 | 0,051 |
| 7 | torso_rotation_max | 0,037 |
| 8 | trunk_tilt_mean | 0,030 |
| 9 | shoulder_angle_mean | 0,028 |
| 10 | elbow_angle_mean | 0,024 |

Con más datos, la **velocidad máxima de muñeca** (`wrist_speed_max`, proxy de
potencia) pasa a dominar la decisión (importancia 0,40), coherente con la
intuición biomecánica de que la velocidad de la cabeza de la raqueta es un
determinante central de la calidad del golpe.

### 9.6 Despliegue en producción

El Random Forest v2 se despliega en `https://ivanmorenoaranda.com/TFM`,
sustituyendo al scoring por reglas. A partir de esta iteración la interfaz
muestra el distintivo «✦ Modelo IA» y la API devuelve `scoring_method="model"`.

Nota de arquitectura: el directorio del modelo se monta como **volumen** desde
el host (`./backend/app/models:/app/app/models`), de modo que el modelo queda
**desacoplado del build** de la imagen Docker. Esto permite actualizarlo sin
reconstruir la imagen y evita que una reconstrucción lo elimine (el `.dockerignore`
excluye los `*.joblib` por peso).

### 9.7 Reproducibilidad

- Definición de cortes: `backend/data/cuts/cuts.csv` (136 cortes: vídeo, inicio,
  fin, score, notas).
- Pipeline: `python train_model.py --mode cut` (recorta con ffmpeg) →
  `--mode label` (extrae características con MediaPipe, cachea en
  `features_cache.json`) → `--mode train` (reduce al Set A y entrena RF/XGB).
- Selección Set A codificada en `train_model.py` (`SET_A_FEATURES`); el modelo se
  guarda con esos 10 nombres y `scoring_service` reconstruye el vector en
  inferencia.

> **Recomendación pendiente.** `train_model.py --mode train` reporta el MAE con
> KFold sin agrupar (10,22). Convendría migrar su validación interna a
> **GroupKFold por vídeo fuente** para que la métrica impresa coincida con la
> estimación honesta (11,73) de este documento.
