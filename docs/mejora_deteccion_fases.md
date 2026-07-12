# Mejora de la detección de fases del golpe

## Problema

La detección del instante de impacto y la segmentación en fases
(*preparación → backswing → impacto → follow-through*) se apoyaba en el pico de
velocidad de la muñeca. La implementación original tenía tres debilidades:

1. **Muñeca incorrecta.** Se usaba `max(velocidad_izq, velocidad_der)` en cada
   fotograma, mezclando la muñeca de apoyo (ruidosa) con la que ejecuta el golpe.
2. **Sin suavizado.** El impacto se estimaba con `argmax` directo sobre la señal
   de velocidad. El *jitter* de MediaPipe genera picos espurios aislados que
   `argmax` confunde con el contacto, situando el impacto en un fotograma erróneo.
3. **Escalas mezcladas.** El backswing se buscaba sumando `torso_rotation`
   (grados, 0–60) y `arm_extension` (ratio, 0–1) sin normalizar, de modo que la
   rotación de tronco dominaba por completo.

## Solución

Reescritura de `PoseService._detect_phases` (`backend/app/services/pose_service.py`):

1. **Muñeca dominante.** Se usa únicamente la velocidad de la muñeca del lado
   dominante (`{side}_wrist_speed`), pasado desde `analyze`.
2. **Suavizado Gaussiano** (`_gaussian_smooth`, numpy puro sin scipy, para no
   añadir dependencias ni inflar la imagen del *backend*). `sigma = max(1, fps/15)`,
   proporcional a la tasa de fotogramas, con relleno *reflect* en los bordes.
3. **Impacto = velocidad + extensión.** Señal combinada normalizada
   `0.7·vel_muñeca + 0.3·extensión_brazo`: la velocidad es la señal primaria y la
   extensión del brazo (casi completa en el contacto) actúa como confirmación
   secundaria. `argmax` sobre esta señal robusta localiza el impacto.
4. **Backswing** buscado sobre señales normalizadas a [0,1] y en una ventana
   **estrictamente anterior** al impacto (evita una fase de duración cero).
5. **Ventana de impacto** definida en tiempo (~±50 ms) en lugar de en fotogramas
   fijos, para ser consistente entre vídeos de 30 y 60 fps.
6. `max_wrist_speed_px_s` reporta el pico de la señal **suavizada**, evitando
   publicar un artefacto de *jitter* como velocidad máxima.

## Validación

- **Prueba sintética:** ante una señal con un pico falso aislado (frame 20) más
  alto que el pico real (frame 50), la lógica antigua devolvía 20; la nueva
  devuelve 49 (impacto real) y sitúa el backswing en el máximo de rotación de
  tronco (frame 36). Casos límite (serie vacía, 1 fotograma) no fallan.
- **End-to-end** sobre vídeos reales (60 fps, tasa de detección 1.0): las cuatro
  fases se generan ordenadas y con duración no nula; el impacto se estima en
  ~1.4–1.6 s, coherente con la ejecución de una derecha.

## Línea futura

La estimación por biomecánica sigue siendo una aproximación. La detección exacta
del contacto mediante **TrackNet** (seguimiento de la pelota fotograma a
fotograma; el impacto es el cambio de dirección de la trayectoria) permitiría
extraer *features* alineadas al instante de golpeo en vez de estadísticos
globales — descrito en la sección de trabajo futuro.
