# Handoff para la redacción de la memoria del TFM

> **Para el asistente que redacte la memoria.** Este documento resume el proyecto,
> el encuadre recomendado y dónde está cada dato. Todo lo que necesitas está en
> esta carpeta `docs/`. **Regla de oro: usa siempre los números honestos (los de
> validación GroupKFold), nunca los optimistas.**

---

## 1. Qué es el proyecto en una frase

**Ivanalyze**: sistema que analiza la técnica del **golpe de derecha** en tenis a
partir de un vídeo, combinando visión por computador, machine learning y un LLM,
y devuelve una **puntuación técnica (0–100)** con feedback explicado. Desplegado
en producción: `https://ivanmorenoaranda.com/TFM`.

## 2. Arquitectura y técnicas (todas reales y desplegadas)

Pipeline end-to-end:

```
Vídeo → validación de contenido (YOLOv8) → estimación de pose (MediaPipe) →
métricas biomecánicas por fotograma → detección de fases del golpe →
agregación estadística → modelo de regresión (Random Forest) → puntuación →
feedback (LLM Claude) fundamentado en biomecánica (RAG) → resultados
```

| Componente | Técnica | Rol |
|---|---|---|
| Validación de entrada | **YOLOv8n** (COCO) | Rechaza vídeos sin golpe real (cuerpo, raqueta, pelota, contacto) |
| Estimación de pose | **MediaPipe Pose Landmarker** | 33 landmarks por fotograma |
| Detección de fases | Señal combinada velocidad muñeca + extensión de brazo, suavizado gaussiano | Preparación / backswing / impacto / follow-through |
| Puntuación | **Random Forest** (regresión), 10 features (Set A) | Nota 0–100 |
| Conocimiento | **RAG** (ChromaDB + embeddings all-MiniLM-L6-v2, literatura biomecánica) | Contexto para el feedback |
| Feedback | **LLM (Claude)** | Texto explicado {summary, issues, tips} |
| Frontend/Backend | React + FastAPI, Docker, HTTPS (Caddy) | App desplegada |

**Base bibliográfica del RAG:** Elliott et al. (2003); Landlinger et al. (2012).

## 3. Resultados del modelo — USA ESTOS NÚMEROS

Fuente completa: **`resultados_modelo_v1.md`** (secciones 1–8 = iteración piloto;
**sección 9 = iteración final v2, la que hay que contar como definitiva**).

**Dataset (v2):** 136 cortes grabados → **135 usables**, de **18 vídeos fuente**,
un golpe por corte. Puntuación media 74,2 (σ 19,6), rango 15–100. Etiquetado por
**un único anotador** (el autor).

**Modelo final: Random Forest, 10 características (Set A).**

| Métrica (validación **GroupKFold** por vídeo fuente — honesta) | Valor |
|---|---|
| MAE | **11,73** puntos |
| RMSE | 15,84 |
| R² | −0,017 (≈ 0) |
| Baseline (predecir la media) | MAE 16,09 |

→ El modelo **reduce el MAE ~27 % sobre el baseline**, pero con R² ≈ 0 al
generalizar a un vídeo nuevo.

**⚠️ Aviso crítico de honestidad.** Existen números más bajos (MAE 9,49 en el
piloto; 9,53 con KFold barajado). **NO los uses como resultado principal**: están
inflados por *fuga de información* (cortes del mismo vídeo caían a la vez en
entrenamiento y test). La validación correcta para datos con varios cortes por
vídeo es **GroupKFold agrupando por vídeo fuente**, y da 11,73. Reportar esto es
un punto fuerte de rigor, no una debilidad.

**Característica más discriminativa:** `wrist_speed_max` (velocidad máxima de
muñeca, proxy de potencia), importancia 0,40.

## 4. Encuadre recomendado (IMPORTANTE para la nota)

Este proyecto se defiende como **trabajo de ingeniería de ML + metodología con
evaluación crítica honesta**, NO como "logré un modelo de alta precisión".

**Tesis a defender:**

> Se construye y despliega un sistema completo de análisis técnico del golpe de
> derecha integrando visión por computador, ML y un LLM. La evaluación rigurosa
> (GroupKFold por vídeo fuente) revela que las características basadas en
> estadísticos globales del vídeo, sobre un dataset reducido etiquetado por un
> único anotador, tienen capacidad discriminativa limitada (MAE 11,7; R² ≈ 0).
> Se identifica y justifica la vía de mejora principal: **features alineadas al
> instante de impacto** mediante seguimiento de la pelota (TrackNet).

**Qué destacar sí o sí:**
1. **Sistema completo desplegado en producción** (no un notebook): Docker, HTTPS,
   reverse proxy, validación de entrada, app usable.
2. **Rigor metodológico:** reducción de 936→10 features contra el sobreajuste
   (ratio muestras/feature) y **corrección GroupKFold** (hallazgo metodológico).
3. **Evaluación honesta y análisis de errores** (regresión hacia la media,
   fallos en los extremos de la escala).

**Riesgo a evitar:** sobrevender el modelo. Mostrar el 11,7 y analizar el porqué
da credibilidad; esconderlo tras el 9,5 es lo que un tribunal afilado revienta.

## 5. Limitaciones (dedícales una sección explícita)

1. **Anotador único** → variable objetivo subjetiva y ruidosa; no hay acuerdo
   inter-anotador que acote el error irreducible.
2. **Dataset pequeño** (135 muestras, 18 vídeos fuente); pocos ejemplos en los
   extremos (golpes muy buenos / muy malos), donde el modelo más falla.
3. **Features de estadísticos globales** del vídeo (mezclan preparación,
   impacto y follow-through) en lugar de valores alineados al golpeo.
4. **Un solo tipo de golpe** (derecha) y condiciones de grabación homogéneas.

## 6. Trabajo futuro (por impacto esperado)

1. **Ampliar el dataset**, con varios anotadores (acuerdo inter-anotador) y más
   ejemplos en los extremos.
2. **TrackNet** — seguimiento de la pelota para detectar el frame de impacto
   exacto y extraer **features biomecánicas alineadas al contacto** (en vez de
   estadísticos globales). Es la mejora con mayor valor metodológico: permite el
   argumento "features alineadas al impacto vs estadísticos globales".
3. Análisis de múltiples golpes por vídeo; clasificador por niveles.

## 7. Mapa de ficheros de esta carpeta

| Fichero | Contenido |
|---|---|
| `resultados_modelo_v1.md` | **Doc principal.** Dataset, metodología, resultados v1 (secc. 1–8) y **v2 (secc. 9)**, tablas, errores, importancias, GroupKFold, despliegue |
| `mejora_deteccion_fases.md` | Reescritura de la detección de fases del golpe (suavizado, señal combinada) |
| `dataset_training_plan.md` | Plan original de dataset y etiquetado |
| `predicciones_oof.csv` | Predicciones out-of-fold del piloto (datos para el scatter real vs predicho) |
| `HANDOFF_memoria.md` | Este documento |

## 8. Datos de ficha del proyecto

- **Título/marca:** Ivanalyze (antes TennisAnalyzer)
- **Autor:** Iván Moreno Aranda — UNIR, TFM 2026 — Tutor: Alejandro
- **Repositorio:** https://github.com/ivmoar/tennis-analyzer (rama `main`)
- **Despliegue:** https://ivanmorenoaranda.com/TFM
- **Stack:** FastAPI · MediaPipe · YOLOv8 · scikit-learn (Random Forest) ·
  ChromaDB (RAG) · Claude (LLM) · React · Docker · Caddy
