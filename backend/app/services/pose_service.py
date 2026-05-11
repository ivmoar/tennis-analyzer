import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from typing import Optional
import urllib.request

MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_PATH = "pose_landmarker_lite.task"

LM = {
    "left_shoulder":  11, "right_shoulder": 12,
    "left_elbow":     13, "right_elbow":    14,
    "left_wrist":     15, "right_wrist":    16,
    "left_hip":       23, "right_hip":      24,
    "left_knee":      25, "right_knee":     26,
    "left_ankle":     27, "right_ankle":    28,
}

POSE_CONNECTIONS = [
    (11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),
]

REFERENCE_RANGES = {
    "elbow_angle":    (100, 160),
    "shoulder_angle": (60,  120),
    "knee_angle":     (130, 170),
    "trunk_tilt":     (0,   20),
}


class PoseService:

    def __init__(self):
        self._ensure_model()

    def _ensure_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"Descargando modelo MediaPipe...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("Modelo descargado.")

    @staticmethod
    def _coords(landmarks, name, w, h):
        lm = landmarks[LM[name]]
        return np.array([lm.x * w, lm.y * h])

    @staticmethod
    def _angle(a, b, c):
        ba = a - b
        bc = c - b
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

    def _compute_metrics(self, landmarks, w, h, side="right"):
        opp = "left" if side == "right" else "right"
        try:
            sh  = self._coords(landmarks, f"{side}_shoulder", w, h)
            el  = self._coords(landmarks, f"{side}_elbow",    w, h)
            wr  = self._coords(landmarks, f"{side}_wrist",    w, h)
            hd  = self._coords(landmarks, f"{side}_hip",      w, h)
            ho  = self._coords(landmarks, f"{opp}_hip",       w, h)
            kn  = self._coords(landmarks, f"{side}_knee",     w, h)
            an  = self._coords(landmarks, f"{side}_ankle",    w, h)
            sho = self._coords(landmarks, f"{opp}_shoulder",  w, h)
            sv  = sho - sh
            return {
                "elbow_angle":    round(self._angle(sh, el, wr), 1),
                "shoulder_angle": round(self._angle(hd, sh, el), 1),
                "knee_angle":     round(self._angle(hd, kn, an), 1),
                "trunk_tilt":     round(float(np.degrees(
                                      np.arctan2(abs(sv[1]), abs(sv[0]) + 1e-6))), 1),
                "hip_separation": round(float(abs(hd[0] - ho[0]) / (w + 1e-6)), 4),
            }
        except Exception:
            return None

    def _draw_landmarks(self, frame, landmarks, w, h):
        """Dibuja keypoints y conexiones manualmente sin usar mp.solutions."""
        for lm_idx in LM.values():
            lm = landmarks[lm_idx]
            if lm.visibility < 0.5:
                continue
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            cv2.circle(frame, (x, y), 5, (255, 255, 255), 1)

        for (a, b) in POSE_CONNECTIONS:
            la, lb = landmarks[a], landmarks[b]
            if la.visibility < 0.5 or lb.visibility < 0.5:
                continue
            x1, y1 = int(la.x * w), int(la.y * h)
            x2, y2 = int(lb.x * w), int(lb.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 200, 100), 2)

    def _annotate_frame(self, frame, landmarks, metrics, w, h, side):
        self._draw_landmarks(frame, landmarks, w, h)
        if not metrics:
            return frame

        def draw_angle(name, value, color):
            lm = landmarks[LM[name]]
            x, y = int(lm.x * w) + 8, int(lm.y * h) - 8
            cv2.putText(frame, f"{value:.0f}", (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

        draw_angle(f"{side}_elbow",    metrics["elbow_angle"],    (0, 255, 255))
        draw_angle(f"{side}_shoulder", metrics["shoulder_angle"], (255, 200, 0))
        draw_angle(f"{side}_knee",     metrics["knee_angle"],     (0, 200, 255))

        panel = [
            f"Codo:    {metrics['elbow_angle']:.0f}",
            f"Hombro:  {metrics['shoulder_angle']:.0f}",
            f"Rodilla: {metrics['knee_angle']:.0f}",
            f"Tronco:  {metrics['trunk_tilt']:.0f}",
        ]
        for i, line in enumerate(panel):
            cv2.putText(frame, line, (10, 25 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, line, (10, 25 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 1, cv2.LINE_AA)
        return frame

    def analyze(self, video_path: str, output_path: str, side: str = "right") -> dict:
        cap = cv2.VideoCapture(video_path)
        fps   = cap.get(cv2.CAP_PROP_FPS) or 30
        w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # No guardar vídeo si output es /dev/null (modo entrenamiento)
        writer = None
        if output_path != "/dev/null":
            writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps, (w, h)
            )

        base_opts = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        opts = mp_vision.PoseLandmarkerOptions(
            base_options=base_opts,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        metrics_series = []
        frame_idx = 0

        with mp_vision.PoseLandmarker.create_from_options(opts) as landmarker:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                ts_ms  = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect_for_video(mp_img, ts_ms)

                if result.pose_landmarks:
                    lms     = result.pose_landmarks[0]
                    metrics = self._compute_metrics(lms, w, h, side)
                    metrics_series.append(metrics)
                    frame   = self._annotate_frame(frame, lms, metrics, w, h, side)
                else:
                    metrics_series.append(None)

                if writer:
                    writer.write(frame)

        cap.release()
        if writer:
            writer.release()

        valid = [m for m in metrics_series if m]
        detection_rate = len(valid) / frame_idx if frame_idx > 0 else 0

        return {
            "metrics_series":     metrics_series,
            "aggregated_metrics": self._aggregate(valid),
            "detection_rate":     round(detection_rate, 3),
            "n_frames":           frame_idx,
        }

    @staticmethod
    def _aggregate(valid_metrics):
        if not valid_metrics:
            return {}
        keys = ["elbow_angle", "shoulder_angle", "knee_angle", "trunk_tilt", "hip_separation"]
        result = {}
        for key in keys:
            vals = [m[key] for m in valid_metrics if key in m]
            if vals:
                arr = np.array(vals)
                result[key] = {
                    "mean": round(float(arr.mean()), 2),
                    "std":  round(float(arr.std()),  2),
                    "min":  round(float(arr.min()),  2),
                    "max":  round(float(arr.max()),  2),
                    "p25":  round(float(np.percentile(arr, 25)), 2),
                    "p75":  round(float(np.percentile(arr, 75)), 2),
                }
        return result