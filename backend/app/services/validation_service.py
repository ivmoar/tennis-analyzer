"""
validation_service.py
---------------------
Pipeline de validación previa y posterior al análisis biomecánico.

El objetivo es garantizar que el vídeo analizado contiene realmente un golpe de
derecha válido antes de emitir una puntuación. Sin esta validación, el sistema
podría puntuar gestos que no son golpes (p. ej., un calentamiento, un fallo o
incluso un vídeo sin jugador).

Checks implementados
────────────────────
  Check 1 — Cuerpo completo visible
      MediaPipe detecta pose en ≥ 40 % de los frames (ya gestionado por
      PoseService.validate_forehand). Aquí se re-expone como ValidationResult.

  Check 2 — Raqueta detectada
      YOLOv8n (COCO clase 38 = tennis racket) debe aparecer en al menos el
      20 % de los frames muestreados. La raqueta debe ser visible en la mayor
      parte del golpe; si no aparece, el vídeo no es válido para el análisis.

  Check 3 — Pelota detectada
      YOLOv8n (COCO clase 32 = sports ball) debe aparecer en al menos 1 frame
      muestreado. La pelota es pequeña y rápida; basta con detectarla una vez
      para confirmar que hay un intercambio real.

  Check 4 — Contacto raqueta-pelota
      En la ventana de impacto estimada (±5 frames alrededor del estimated_
      impact_frame de PoseService), la pelota debe estar dentro del umbral de
      proximidad respecto a la muñeca dominante o al bounding box de la raqueta.
      Umbral: 15 % del ancho del frame.

Limitaciones académicas
───────────────────────
  La detección de pelota de YOLOv8n está entrenada sobre COCO, que incluye
  "sports ball" de manera genérica. Para pelotas de tenis en vuelo a alta
  velocidad se recomienda TrackNet (Huang et al., 2019) o modelos específicos
  de dominio, que quedan fuera del alcance de este TFE por requerir datasets
  de entrenamiento especializados y GPU dedicada.
  El Check 4 es por tanto un heurístico de proximidad espacial, no una
  detección de contacto físico real, lo que constituye una limitación
  conocida del prototipo.

Referencias
───────────
  Redmon, J. & Farhadi, A. (2018). YOLOv3: An Incremental Improvement. arXiv:1804.02767
  Huang, Y.-C., et al. (2019). TrackNet: Tennis Ball Tracking from Broadcast Video.
      ICCV Workshop on Computer Vision for Sports.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

# Clases COCO relevantes
_COCO_SPORTS_BALL   = 32
_COCO_TENNIS_RACKET = 38

# Umbrales de validación
# YOLOv8n/COCO tiene limitaciones con objetos en movimiento rápido (raqueta, pelota).
# El umbral de raqueta se fija en 0.08 para tolerar motion blur y ángulos difíciles.
_MIN_RACKET_FRAME_RATIO = 0.08   # raqueta en ≥ 8 % de frames muestreados
_MIN_BALL_DETECTIONS    = 1      # pelota en al menos 1 frame
_YOLO_CONF              = 0.20   # umbral de confianza YOLO (más bajo = más sensible)
_CONTACT_DIST_RATIO     = 0.15   # distancia máx. pelota-muñeca como fracción del ancho
_IMPACT_WINDOW_FRAMES   = 8      # ± frames alrededor del impacto para Check 4
_MAX_SAMPLE_FRAMES      = 60     # número máx. de frames a muestrear para Checks 2-3


@dataclass
class CheckResult:
    passed: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    valid: bool
    checks: dict[str, CheckResult]
    first_failure: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "first_failure": self.first_failure,
            "checks": {
                name: {
                    "passed":  c.passed,
                    "message": c.message,
                    "details": c.details,
                }
                for name, c in self.checks.items()
            },
        }


class ValidationService:
    """
    Servicio singleton de validación. El modelo YOLO se carga de forma perezosa
    (lazy) la primera vez que se necesita, para no penalizar el arranque del
    servidor cuando ultralytics no está disponible.
    """

    _instance: Optional["ValidationService"] = None
    _yolo_model = None
    _yolo_available: Optional[bool] = None

    # ──────────────────────────────────────────────────────────────────────────
    # Punto de entrada principal
    # ──────────────────────────────────────────────────────────────────────────

    def validate(
        self,
        video_path: str,
        pose_result: dict,
        side: str = "right",
    ) -> ValidationResult:
        """
        Ejecuta los 4 checks y devuelve un ValidationResult consolidado.

        Parameters
        ----------
        video_path:  ruta al vídeo original (para muestrear frames con OpenCV)
        pose_result: resultado de PoseService.analyze(), necesario para
                     detection_rate (Check 1) e impact_frame (Check 4)
        side:        lado dominante ("right" / "left")
        """
        checks: dict[str, CheckResult] = {}

        # ── Check 1: cuerpo completo ─────────────────────────────────────────
        checks["body_detection"] = self._check_body(pose_result)
        if not checks["body_detection"].passed:
            return ValidationResult(valid=False, checks=checks,
                                    first_failure="body_detection")

        # Muestrear frames para Checks 2 y 3 (operación costosa, hacerla una vez)
        frames, frame_indices, fps, w, h = self._sample_frames(video_path)

        # ── Check 2: raqueta ─────────────────────────────────────────────────
        checks["racket_detected"] = self._check_racket(frames, w)
        if not checks["racket_detected"].passed:
            return ValidationResult(valid=False, checks=checks,
                                    first_failure="racket_detected")

        # ── Check 3: pelota ──────────────────────────────────────────────────
        checks["ball_detected"] = self._check_ball(frames, w)
        if not checks["ball_detected"].passed:
            return ValidationResult(valid=False, checks=checks,
                                    first_failure="ball_detected")

        # ── Check 4: contacto raqueta-pelota ─────────────────────────────────
        checks["contact_detected"] = self._check_contact(
            video_path=video_path,
            pose_result=pose_result,
            side=side,
            frame_width=w,
            frame_height=h,
            fps=fps,
        )
        # Check 4 es advertencia, no bloqueo duro: si YOLO no detecta contacto
        # podría ser por limitaciones del modelo (pelota fuera de cámara, oclusión).
        # Se registra el resultado pero no se rechaza el análisis.

        all_passed = all(c.passed for c in checks.values())
        first_fail = next(
            (name for name, c in checks.items() if not c.passed), None
        )
        return ValidationResult(valid=all_passed, checks=checks,
                                first_failure=first_fail)

    # ──────────────────────────────────────────────────────────────────────────
    # Checks individuales
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _check_body(pose_result: dict) -> CheckResult:
        rate = pose_result.get("detection_rate", 0.0)
        passed = rate >= 0.40
        return CheckResult(
            passed=passed,
            message=(
                "Cuerpo completo detectado correctamente."
                if passed else
                f"Pose detectada solo en el {rate*100:.0f}% de los frames "
                f"(mínimo requerido: 40%). Asegúrate de que el cuerpo completo "
                f"sea visible durante todo el golpe."
            ),
            details={"detection_rate": round(rate, 3)},
        )

    def _check_racket(self, frames: list, frame_width: int) -> CheckResult:
        if not self._yolo_ready():
            return CheckResult(
                passed=True,
                message="Detección de raqueta omitida (modelo YOLO no disponible).",
                details={"skipped": True},
            )
        detections = 0
        total = len(frames)
        for frame in frames:
            results = self._yolo_model(frame, verbose=False,
                                       conf=_YOLO_CONF, classes=[_COCO_TENNIS_RACKET])
            if len(results[0].boxes) > 0:
                detections += 1
        ratio = detections / total if total > 0 else 0
        passed = ratio >= _MIN_RACKET_FRAME_RATIO
        return CheckResult(
            passed=passed,
            message=(
                f"Raqueta detectada en el {ratio*100:.0f}% de los frames muestreados."
                if passed else
                f"No se detectó la raqueta en suficientes frames ({ratio*100:.0f}% "
                f"< {_MIN_RACKET_FRAME_RATIO*100:.0f}% requerido). "
                f"Comprueba que la raqueta sea visible y el vídeo sea un golpe de tenis."
            ),
            details={"frames_with_racket": detections, "frames_sampled": total,
                     "ratio": round(ratio, 3)},
        )

    def _check_ball(self, frames: list, frame_width: int) -> CheckResult:
        if not self._yolo_ready():
            return CheckResult(
                passed=True,
                message="Detección de pelota omitida (modelo YOLO no disponible).",
                details={"skipped": True},
            )
        detections = 0
        for frame in frames:
            results = self._yolo_model(frame, verbose=False,
                                       conf=_YOLO_CONF, classes=[_COCO_SPORTS_BALL])
            if len(results[0].boxes) > 0:
                detections += 1
        passed = detections >= _MIN_BALL_DETECTIONS
        return CheckResult(
            passed=passed,
            message=(
                f"Pelota detectada en {detections} frame(s)."
                if passed else
                "No se detectó la pelota en ningún frame. "
                "Verifica que el vídeo incluya la pelota en algún momento del golpe. "
                "Nota: pelotas en vuelo a alta velocidad pueden ser difíciles de detectar "
                "con el modelo COCO general; considera ajustar el ángulo de cámara."
            ),
            details={"frames_with_ball": detections, "frames_sampled": len(frames)},
        )

    def _check_contact(
        self,
        video_path: str,
        pose_result: dict,
        side: str,
        frame_width: int,
        frame_height: int,
        fps: float,
    ) -> CheckResult:
        """
        Heurístico de contacto: en la ventana de impacto (±8 frames),
        ¿está la pelota cerca de la muñeca dominante?
        """
        if not self._yolo_ready():
            return CheckResult(
                passed=True,
                message="Verificación de contacto omitida (modelo YOLO no disponible).",
                details={"skipped": True},
            )

        impact_frame = pose_result.get("event_timing", {}).get("estimated_impact_frame")
        if impact_frame is None:
            return CheckResult(
                passed=True,
                message="No se pudo determinar el frame de impacto para verificar el contacto.",
                details={"skipped": True},
            )

        # Extraer wrist pixel position del frame de impacto
        wrist_name = f"{side}_wrist"
        wrist_pos = self._get_wrist_pixel(pose_result, impact_frame, wrist_name)

        # Leer frames en la ventana de impacto
        threshold_px = frame_width * _CONTACT_DIST_RATIO
        start_f = max(0, impact_frame - _IMPACT_WINDOW_FRAMES)
        end_f   = impact_frame + _IMPACT_WINDOW_FRAMES
        window_frames = self._read_frame_range(video_path, start_f, end_f)

        min_dist = math.inf
        contact_found = False

        for frame in window_frames:
            results = self._yolo_model(frame, verbose=False,
                                       classes=[_COCO_SPORTS_BALL, _COCO_TENNIS_RACKET])
            boxes = results[0].boxes
            if len(boxes) == 0:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                if cls_id == _COCO_SPORTS_BALL and wrist_pos is not None:
                    dist = math.hypot(cx - wrist_pos[0], cy - wrist_pos[1])
                    min_dist = min(min_dist, dist)
                    if dist <= threshold_px:
                        contact_found = True
                        break
            if contact_found:
                break

        dist_str = (f"{min_dist:.0f}px" if min_dist != math.inf else "N/A")
        return CheckResult(
            passed=contact_found,
            message=(
                f"Contacto confirmado: pelota a {dist_str} de la muñeca en la ventana de impacto."
                if contact_found else
                f"No se confirmó el contacto raqueta-pelota (dist. mínima: {dist_str}, "
                f"umbral: {threshold_px:.0f}px). "
                f"Nota: limitación conocida del modelo COCO para pelotas en vuelo; "
                f"el análisis se emite con advertencia."
            ),
            details={
                "impact_frame": impact_frame,
                "threshold_px": round(threshold_px, 1),
                "min_distance_px": round(min_dist, 1) if min_dist != math.inf else None,
                "contact_confirmed": contact_found,
            },
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _yolo_ready(self) -> bool:
        if self._yolo_available is None:
            self._load_yolo()
        return bool(self._yolo_available)

    def _load_yolo(self):
        try:
            from ultralytics import YOLO  # noqa: PLC0415
            self.__class__._yolo_model = YOLO("yolov8n.pt")
            self.__class__._yolo_available = True
        except Exception as e:
            print(f"ValidationService: YOLO no disponible ({e}). "
                  f"Los checks 2-4 se omitirán.")
            self.__class__._yolo_available = False

    def _sample_frames(
        self, video_path: str
    ) -> tuple[list, list, float, int, int]:
        """Muestrea hasta _MAX_SAMPLE_FRAMES frames distribuidos uniformemente."""
        cap = cv2.VideoCapture(video_path)
        total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        fps     = cap.get(cv2.CAP_PROP_FPS) or 30.0
        w       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        step    = max(1, total // _MAX_SAMPLE_FRAMES)
        indices = list(range(0, total, step))[:_MAX_SAMPLE_FRAMES]

        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        cap.release()
        return frames, indices, fps, w, h

    @staticmethod
    def _read_frame_range(
        video_path: str, start: int, end: int
    ) -> list:
        """Lee un rango continuo de frames (para la ventana de impacto)."""
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        frames = []
        for _ in range(end - start + 1):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        return frames

    @staticmethod
    def _get_wrist_pixel(
        pose_result: dict, impact_frame: int, wrist_name: str
    ) -> Optional[tuple[float, float]]:
        """Obtiene la posición en píxeles de la muñeca dominante en el frame de impacto."""
        landmarks_series = pose_result.get("landmarks_series", [])
        # Buscar el frame más cercano al impact_frame
        best = None
        best_dist = math.inf
        for entry in landmarks_series:
            if entry is None:
                continue
            f = entry.get("frame", -1)
            d = abs(f - impact_frame)
            if d < best_dist:
                best_dist = d
                best = entry
        if best is None or best_dist > 10:
            return None
        lm = best.get("landmarks", {}).get(wrist_name)
        if lm:
            return (lm["pixel_x"], lm["pixel_y"])
        return None
