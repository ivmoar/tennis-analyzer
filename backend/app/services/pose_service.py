import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import urllib.request
from app.core.config import settings

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

LANDMARK_NAMES = [
    "nose",
    "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear",
    "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_pinky", "right_pinky",
    "left_index", "right_index",
    "left_thumb", "right_thumb",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

LM = {name: idx for idx, name in enumerate(LANDMARK_NAMES)}

POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]

CORE_METRIC_KEYS = ["elbow_angle", "shoulder_angle", "knee_angle", "trunk_tilt", "hip_separation"]

ANGLE_METRIC_KEYS = [
    "elbow_angle", "shoulder_angle", "knee_angle",
    "opp_elbow_angle", "opp_shoulder_angle", "opp_knee_angle",
    "shoulder_line_angle", "hip_line_angle", "torso_rotation",
    "trunk_tilt",
]

KINEMATIC_LANDMARKS = [
    "nose",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


class PoseService:

    def __init__(self):
        self._ensure_model()

    def _ensure_model(self):
        path = settings.MEDIAPIPE_MODEL_PATH
        if not os.path.exists(path):
            print("Descargando modelo MediaPipe...")
            urllib.request.urlretrieve(MODEL_URL, path)
            print("Modelo descargado.")

    @staticmethod
    def _point(landmarks, name, w, h):
        lm = landmarks[LM[name]]
        return np.array([lm.x * w, lm.y * h], dtype=float)

    @staticmethod
    def _point3d(landmarks, name, w, h):
        lm = landmarks[LM[name]]
        return np.array([lm.x * w, lm.y * h, lm.z * w], dtype=float)

    @staticmethod
    def _angle(a, b, c):
        ba = a - b
        bc = c - b
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

    @staticmethod
    def _line_angle(a, b):
        vec = b - a
        return float(np.degrees(np.arctan2(vec[1], vec[0] + 1e-6)))

    @staticmethod
    def _normalize_angle(angle):
        return float((angle + 180) % 360 - 180)

    @staticmethod
    def _distance(a, b):
        return float(np.linalg.norm(a - b))

    @staticmethod
    def _safe_ratio(num, den):
        return float(num / (den + 1e-6))

    def _serialize_landmarks(self, landmarks, w, h):
        result = {}
        for idx, name in enumerate(LANDMARK_NAMES):
            lm = landmarks[idx]
            result[name] = {
                "index": idx,
                "x": round(float(lm.x), 6),
                "y": round(float(lm.y), 6),
                "z": round(float(lm.z), 6),
                "pixel_x": round(float(lm.x * w), 2),
                "pixel_y": round(float(lm.y * h), 2),
                "pixel_z": round(float(lm.z * w), 2),
                "visibility": round(float(getattr(lm, "visibility", 0.0)), 4),
                "presence": round(float(getattr(lm, "presence", 0.0)), 4),
            }
        return result

    def _compute_metrics(self, landmarks, w, h, side="right"):
        opp = "left" if side == "right" else "right"
        try:
            sh = self._point(landmarks, f"{side}_shoulder", w, h)
            el = self._point(landmarks, f"{side}_elbow", w, h)
            wr = self._point(landmarks, f"{side}_wrist", w, h)
            hp = self._point(landmarks, f"{side}_hip", w, h)
            kn = self._point(landmarks, f"{side}_knee", w, h)
            an = self._point(landmarks, f"{side}_ankle", w, h)
            heel = self._point(landmarks, f"{side}_heel", w, h)
            foot = self._point(landmarks, f"{side}_foot_index", w, h)

            opp_sh = self._point(landmarks, f"{opp}_shoulder", w, h)
            opp_el = self._point(landmarks, f"{opp}_elbow", w, h)
            opp_wr = self._point(landmarks, f"{opp}_wrist", w, h)
            opp_hp = self._point(landmarks, f"{opp}_hip", w, h)
            opp_kn = self._point(landmarks, f"{opp}_knee", w, h)
            opp_an = self._point(landmarks, f"{opp}_ankle", w, h)
            opp_heel = self._point(landmarks, f"{opp}_heel", w, h)
            opp_foot = self._point(landmarks, f"{opp}_foot_index", w, h)

            nose = self._point(landmarks, "nose", w, h)
            shoulder_mid = (sh + opp_sh) / 2
            hip_mid = (hp + opp_hp) / 2
            ankle_mid = (an + opp_an) / 2

            shoulder_width = self._distance(sh, opp_sh)
            hip_width = self._distance(hp, opp_hp)
            torso_len = self._distance(shoulder_mid, hip_mid)
            body_scale = max(shoulder_width, hip_width, torso_len, 1.0)

            shoulder_line = self._line_angle(sh, opp_sh)
            hip_line = self._line_angle(hp, opp_hp)
            torso_rotation = self._normalize_angle(shoulder_line - hip_line)
            trunk_vec = shoulder_mid - hip_mid
            trunk_tilt = abs(90 - abs(self._line_angle(hip_mid, shoulder_mid)))

            hand_to_head = self._distance(wr, nose)
            hand_to_opp_shoulder = self._distance(wr, opp_sh)
            racket_proxy_extension = self._distance(sh, wr)
            stance_width = self._distance(heel, opp_heel)
            foot_alignment = self._line_angle(heel, foot)
            opp_foot_alignment = self._line_angle(opp_heel, opp_foot)
            center_of_mass = (shoulder_mid + hip_mid + ankle_mid) / 3

            return {
                "elbow_angle": round(self._angle(sh, el, wr), 2),
                "shoulder_angle": round(self._angle(hp, sh, el), 2),
                "knee_angle": round(self._angle(hp, kn, an), 2),
                "opp_elbow_angle": round(self._angle(opp_sh, opp_el, opp_wr), 2),
                "opp_shoulder_angle": round(self._angle(opp_hp, opp_sh, opp_el), 2),
                "opp_knee_angle": round(self._angle(opp_hp, opp_kn, opp_an), 2),
                "trunk_tilt": round(float(trunk_tilt), 2),
                "hip_separation": round(self._safe_ratio(abs(hp[0] - opp_hp[0]), w), 4),
                "shoulder_line_angle": round(shoulder_line, 2),
                "hip_line_angle": round(hip_line, 2),
                "torso_rotation": round(torso_rotation, 2),
                "shoulder_hip_separation": round(self._safe_ratio(abs(shoulder_mid[0] - hip_mid[0]), body_scale), 4),
                "arm_extension": round(self._safe_ratio(racket_proxy_extension, body_scale), 4),
                "hand_to_head_distance": round(self._safe_ratio(hand_to_head, body_scale), 4),
                "hand_to_opp_shoulder_distance": round(self._safe_ratio(hand_to_opp_shoulder, body_scale), 4),
                "wrist_height": round(self._safe_ratio(h - wr[1], h), 4),
                "stance_width": round(self._safe_ratio(stance_width, body_scale), 4),
                "foot_alignment": round(foot_alignment, 2),
                "opp_foot_alignment": round(opp_foot_alignment, 2),
                "center_of_mass_x": round(self._safe_ratio(center_of_mass[0], w), 4),
                "center_of_mass_y": round(self._safe_ratio(center_of_mass[1], h), 4),
                "body_scale_px": round(float(body_scale), 2),
                "dominant_wrist_x": round(self._safe_ratio(wr[0], w), 4),
                "dominant_wrist_y": round(self._safe_ratio(wr[1], h), 4),
                "dominant_elbow_x": round(self._safe_ratio(el[0], w), 4),
                "dominant_elbow_y": round(self._safe_ratio(el[1], h), 4),
                "dominant_shoulder_x": round(self._safe_ratio(sh[0], w), 4),
                "dominant_shoulder_y": round(self._safe_ratio(sh[1], h), 4),
                "dominant_hip_x": round(self._safe_ratio(hp[0], w), 4),
                "dominant_hip_y": round(self._safe_ratio(hp[1], h), 4),
                "trunk_vector_x": round(self._safe_ratio(trunk_vec[0], body_scale), 4),
                "trunk_vector_y": round(self._safe_ratio(trunk_vec[1], body_scale), 4),
            }
        except Exception:
            return None

    def _draw_landmarks(self, frame, landmarks, w, h):
        for idx, lm in enumerate(landmarks):
            if getattr(lm, "visibility", 0) < 0.5:
                continue
            x, y = int(lm.x * w), int(lm.y * h)
            radius = 4 if idx in LM.values() else 3
            cv2.circle(frame, (x, y), radius, (0, 255, 0), -1)
            cv2.circle(frame, (x, y), radius, (255, 255, 255), 1)

        for a, b in POSE_CONNECTIONS:
            la, lb = landmarks[a], landmarks[b]
            if getattr(la, "visibility", 0) < 0.5 or getattr(lb, "visibility", 0) < 0.5:
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

        draw_angle(f"{side}_elbow", metrics["elbow_angle"], (0, 255, 255))
        draw_angle(f"{side}_shoulder", metrics["shoulder_angle"], (255, 200, 0))
        draw_angle(f"{side}_knee", metrics["knee_angle"], (0, 200, 255))

        panel = [
            f"Codo:    {metrics['elbow_angle']:.0f}",
            f"Hombro:  {metrics['shoulder_angle']:.0f}",
            f"Rodilla: {metrics['knee_angle']:.0f}",
            f"Tronco:  {metrics['trunk_tilt']:.0f}",
            f"Rotacion:{metrics['torso_rotation']:.0f}",
        ]
        for i, line in enumerate(panel):
            cv2.putText(frame, line, (10, 25 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, line, (10, 25 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 1, cv2.LINE_AA)
        return frame

    @staticmethod
    def validate_forehand(pose_result: dict, side: str) -> None:
        """
        Valida que el vídeo analizado contiene un golpe de tenis analizable.
        Lanza ValueError con mensaje de usuario si no supera la validación.

        Comprueba:
        1. Duración mínima (≥ 15 frames).
        2. Tasa de detección de pose (≥ 40 % de frames).
        3. Visibilidad media de hombro, codo y muñeca del lado dominante (≥ 40 %).
        4. Coherencia fisiológica de los ángulos calculados.
        """
        n_frames        = pose_result["n_frames"]
        detection_rate  = pose_result["detection_rate"]
        landmarks_series = pose_result["landmarks_series"]
        agg             = pose_result.get("aggregated_metrics", {})

        # 1. Duración mínima
        if n_frames < 15:
            raise ValueError(
                "El vídeo es demasiado corto. Graba al menos 1 segundo del golpe completo."
            )

        # 2. Tasa de detección
        if detection_rate < 0.40:
            raise ValueError(
                f"Solo se detectó pose en el {round(detection_rate * 100)}% de los fotogramas. "
                "Asegúrate de que el jugador aparece de cuerpo completo y bien encuadrado durante todo el vídeo."
            )

        # 3. Visibilidad de landmarks clave del brazo dominante
        dom = "right" if side == "right" else "left"
        key_lms = [f"{dom}_shoulder", f"{dom}_elbow", f"{dom}_wrist"]

        vis_sums   = {lm: 0.0 for lm in key_lms}
        vis_counts = {lm: 0   for lm in key_lms}

        for frame_data in landmarks_series:
            if not frame_data:
                continue
            for lm in key_lms:
                lm_data = frame_data.get("landmarks", {}).get(lm)
                if lm_data is not None:
                    vis_sums[lm]   += float(lm_data.get("visibility", 0.0))
                    vis_counts[lm] += 1

        for lm in key_lms:
            if vis_counts[lm] == 0:
                continue
            mean_vis = vis_sums[lm] / vis_counts[lm]
            if mean_vis < 0.40:
                part = lm.replace(f"{dom}_", "").replace("_", " ")
                raise ValueError(
                    f"El {part} del brazo dominante no se ve con suficiente claridad "
                    f"(visibilidad media: {mean_vis:.0%}). "
                    "Graba el golpe de frente o desde el lateral asegurándote de que el brazo completo es visible."
                )

        # 4. Coherencia fisiológica
        if "elbow_angle" not in agg or "shoulder_angle" not in agg:
            raise ValueError(
                "No se pudo calcular el ángulo del brazo dominante. "
                "Verifica que el jugador realiza un golpe de derecha completo con el brazo visible."
            )

        elbow_mean    = agg["elbow_angle"]["mean"]
        shoulder_mean = agg["shoulder_angle"]["mean"]

        if not (20 < elbow_mean < 220) or not (5 < shoulder_mean < 220):
            raise ValueError(
                "Las métricas calculadas no corresponden a un golpe de tenis. "
                "Verifica que el vídeo muestra a un jugador realizando un golpe de derecha."
            )

    def analyze(self, video_path: str, output_path: str, side: str = "right") -> dict:
        cap = cv2.VideoCapture(video_path)
        if hasattr(cv2, "CAP_PROP_ORIENTATION_AUTO"):
            cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            return {
                "metrics_series": [],
                "landmarks_series": [],
                "kinematics_series": [],
                "aggregated_metrics": {},
                "phases": [],
                "event_timing": {},
                "feature_vector": [],
                "feature_names": [],
                "landmark_names": LANDMARK_NAMES,
                "detection_rate": 0,
                "n_frames": 0,
                "fps": round(float(fps), 2),
            }

        h, w = first_frame.shape[:2]

        writer = None
        if output_path != "/dev/null":
            # avc1/H.264 no está disponible en opencv-python-headless sin libx264.
            # mp4v (MPEG-4 Part 2) está incluido de serie y es compatible con todos
            # los navegadores modernos en contenedor .mp4.
            writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps, (w, h)
            )
            if not writer.isOpened():
                raise RuntimeError(
                    f"No se pudo abrir el VideoWriter para {output_path}. "
                    "Comprueba que la ruta de salida existe y el codec mp4v está disponible."
                )

        base_opts = mp_python.BaseOptions(model_asset_path=settings.MEDIAPIPE_MODEL_PATH)
        opts = mp_vision.PoseLandmarkerOptions(
            base_options=base_opts,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        metrics_series = []
        landmarks_series = []
        frame_idx = 0

        def process_frame(frame):
            nonlocal frame_idx
            # Calcular timestamp desde frame_idx para garantizar monotonía
            # (cap.get(CAP_PROP_POS_MSEC) falla con vídeos iPhone VFR)
            ts_ms = int(frame_idx * 1000 / fps)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_img, ts_ms)

            if result.pose_landmarks:
                lms = result.pose_landmarks[0]
                metrics = self._compute_metrics(lms, w, h, side)
                metrics_series.append(metrics)
                landmarks_series.append({
                    "frame": frame_idx,
                    "timestamp_ms": ts_ms,
                    "landmarks": self._serialize_landmarks(lms, w, h),
                })
                frame = self._annotate_frame(frame, lms, metrics, w, h, side)
            else:
                metrics_series.append(None)
                landmarks_series.append(None)

            if writer:
                writer.write(frame)

            frame_idx += 1

        with mp_vision.PoseLandmarker.create_from_options(opts) as landmarker:
            process_frame(first_frame)

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                process_frame(frame)

        cap.release()
        if writer:
            writer.release()

        kinematics_series = self._compute_kinematics(landmarks_series, metrics_series, fps)
        enriched_metrics = self._merge_kinematics(metrics_series, kinematics_series)
        phase_result = self._detect_phases(enriched_metrics, fps)
        valid = [m for m in enriched_metrics if m]
        detection_rate = len(valid) / frame_idx if frame_idx > 0 else 0

        return {
            "metrics_series": enriched_metrics,
            "landmarks_series": landmarks_series,
            "kinematics_series": kinematics_series,
            "aggregated_metrics": self._aggregate(valid),
            "phases": phase_result["phases"],
            "event_timing": phase_result["event_timing"],
            "feature_vector": self.build_feature_vector(self._aggregate(valid)),
            "feature_names": self.get_feature_names(self._aggregate(valid)),
            "landmark_names": LANDMARK_NAMES,
            "detection_rate": round(detection_rate, 3),
            "n_frames": frame_idx,
            "fps": round(float(fps), 2),
        }

    def _compute_kinematics(self, landmarks_series, metrics_series, fps):
        dt = 1.0 / (fps or 30)
        result = []
        prev_points = None
        prev_vel = None
        prev_angles = None
        prev_angle_vel = None

        for i, frame in enumerate(landmarks_series):
            if not frame:
                result.append(None)
                prev_points = None
                prev_vel = None
                prev_angles = None
                prev_angle_vel = None
                continue

            points = {}
            for name in KINEMATIC_LANDMARKS:
                lm = frame["landmarks"][name]
                points[name] = np.array([lm["pixel_x"], lm["pixel_y"], lm["pixel_z"]], dtype=float)

            landmark_kin = {}
            velocities = {}
            for name, point in points.items():
                if prev_points and name in prev_points:
                    vel = (point - prev_points[name]) / dt
                    acc = (vel - prev_vel[name]) / dt if prev_vel and name in prev_vel else np.zeros(3)
                else:
                    vel = np.zeros(3)
                    acc = np.zeros(3)
                velocities[name] = vel
                landmark_kin[name] = {
                    "vx": round(float(vel[0]), 2),
                    "vy": round(float(vel[1]), 2),
                    "vz": round(float(vel[2]), 2),
                    "speed": round(float(np.linalg.norm(vel)), 2),
                    "ax": round(float(acc[0]), 2),
                    "ay": round(float(acc[1]), 2),
                    "az": round(float(acc[2]), 2),
                    "acceleration": round(float(np.linalg.norm(acc)), 2),
                }

            angle_kin = {}
            metrics = metrics_series[i] or {}
            angles = {k: metrics[k] for k in ANGLE_METRIC_KEYS if k in metrics}
            angle_velocities = {}
            for key, value in angles.items():
                if prev_angles and key in prev_angles:
                    vel = self._normalize_angle(value - prev_angles[key]) / dt
                    acc = (vel - prev_angle_vel[key]) / dt if prev_angle_vel and key in prev_angle_vel else 0.0
                else:
                    vel = 0.0
                    acc = 0.0
                angle_velocities[key] = vel
                angle_kin[f"{key}_velocity"] = round(float(vel), 2)
                angle_kin[f"{key}_acceleration"] = round(float(acc), 2)

            result.append({
                "frame": frame["frame"],
                "timestamp_ms": frame["timestamp_ms"],
                "landmarks": landmark_kin,
                "angles": angle_kin,
            })
            prev_points = points
            prev_vel = velocities
            prev_angles = angles
            prev_angle_vel = angle_velocities

        return result

    @staticmethod
    def _merge_kinematics(metrics_series, kinematics_series):
        enriched = []
        for metrics, kin in zip(metrics_series, kinematics_series):
            if not metrics:
                enriched.append(None)
                continue
            item = dict(metrics)
            if kin:
                for key, value in kin["angles"].items():
                    item[key] = value
                for landmark in ["dominant_wrist", "dominant_elbow", "dominant_shoulder", "dominant_hip"]:
                    side_name = landmark.replace("dominant_", "")
                    for side in ("left", "right"):
                        candidate = f"{side}_{side_name}"
                        if candidate in kin["landmarks"]:
                            prefix = f"{candidate}_"
                            for k, v in kin["landmarks"][candidate].items():
                                item[f"{prefix}{k}"] = v
                if "right_wrist" in kin["landmarks"]:
                    item["right_wrist_speed"] = kin["landmarks"]["right_wrist"]["speed"]
                    item["right_wrist_acceleration"] = kin["landmarks"]["right_wrist"]["acceleration"]
                if "left_wrist" in kin["landmarks"]:
                    item["left_wrist_speed"] = kin["landmarks"]["left_wrist"]["speed"]
                    item["left_wrist_acceleration"] = kin["landmarks"]["left_wrist"]["acceleration"]
                # wrist_speed unificado (max dominante) — usado en REFERENCE_RANGES y scoring
                item["wrist_speed"] = max(
                    item.get("right_wrist_speed", 0.0),
                    item.get("left_wrist_speed", 0.0),
                )
            # hip_separation en grados: rotación relativa cadera-hombros (torso_rotation)
            # Mantiene consistencia con REFERENCE_RANGES (20–60°) y la descripción biomecánica
            item["hip_separation"] = abs(item.get("torso_rotation", 0.0))
            enriched.append(item)
        return enriched

    def _detect_phases(self, metrics_series, fps):
        valid = [(i, m) for i, m in enumerate(metrics_series) if m]
        if not valid:
            return {"phases": [], "event_timing": {}}

        indices = np.array([i for i, _ in valid])
        wrist_speed = np.array([
            max(m.get("right_wrist_speed", 0), m.get("left_wrist_speed", 0))
            for _, m in valid
        ])
        arm_extension = np.array([m.get("arm_extension", 0) for _, m in valid])
        torso_rotation = np.array([abs(m.get("torso_rotation", 0)) for _, m in valid])

        impact_pos = int(np.argmax(wrist_speed))
        impact_frame = int(indices[impact_pos])
        pre_impact = max(0, impact_pos - int(fps * 0.8))
        backswing_slice = slice(pre_impact, impact_pos + 1)
        backswing_local = int(np.argmax(torso_rotation[backswing_slice] + arm_extension[backswing_slice]))
        backswing_pos = pre_impact + backswing_local
        backswing_frame = int(indices[backswing_pos])

        prep_end_frame = max(int(indices[0]), backswing_frame)
        follow_start_frame = impact_frame
        follow_end_frame = int(indices[-1])

        phases = [
            self._phase("preparation", int(indices[0]), prep_end_frame, fps),
            self._phase("backswing_to_acceleration", prep_end_frame, impact_frame, fps),
            self._phase("impact_window", max(int(indices[0]), impact_frame - 2), min(follow_end_frame, impact_frame + 2), fps),
            self._phase("follow_through", follow_start_frame, follow_end_frame, fps),
        ]

        event_timing = {
            "preparation_start_frame": int(indices[0]),
            "backswing_peak_frame": backswing_frame,
            "estimated_impact_frame": impact_frame,
            "follow_through_end_frame": follow_end_frame,
            "preparation_start_sec": round(float(indices[0] / fps), 3),
            "backswing_peak_sec": round(float(backswing_frame / fps), 3),
            "estimated_impact_sec": round(float(impact_frame / fps), 3),
            "follow_through_end_sec": round(float(follow_end_frame / fps), 3),
            "max_wrist_speed_px_s": round(float(wrist_speed[impact_pos]), 2),
            "max_torso_rotation_deg": round(float(torso_rotation.max()), 2),
            "max_arm_extension": round(float(arm_extension.max()), 4),
        }
        return {"phases": phases, "event_timing": event_timing}

    @staticmethod
    def _phase(name, start_frame, end_frame, fps):
        return {
            "name": name,
            "start_frame": int(start_frame),
            "end_frame": int(end_frame),
            "start_sec": round(float(start_frame / fps), 3),
            "end_sec": round(float(end_frame / fps), 3),
            "duration_sec": round(float(max(end_frame - start_frame, 0) / fps), 3),
        }

    @staticmethod
    def _aggregate(valid_metrics):
        if not valid_metrics:
            return {}
        keys = sorted({
            key
            for metrics in valid_metrics
            for key, value in metrics.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        })
        result = {}
        for key in keys:
            vals = [m[key] for m in valid_metrics if key in m and isinstance(m[key], (int, float))]
            if vals:
                arr = np.array(vals, dtype=float)
                result[key] = {
                    "mean": round(float(arr.mean()), 4),
                    "std": round(float(arr.std()), 4),
                    "min": round(float(arr.min()), 4),
                    "max": round(float(arr.max()), 4),
                    "p25": round(float(np.percentile(arr, 25)), 4),
                    "p50": round(float(np.percentile(arr, 50)), 4),
                    "p75": round(float(np.percentile(arr, 75)), 4),
                    "range": round(float(arr.max() - arr.min()), 4),
                }
        return result

    @staticmethod
    def get_feature_names(aggregated_metrics: dict) -> list:
        stats = ["mean", "std", "min", "max", "p25", "p50", "p75", "range"]
        return [f"{key}_{stat}" for key in sorted(aggregated_metrics.keys()) for stat in stats]

    @classmethod
    def build_feature_vector(cls, aggregated_metrics: dict) -> list:
        stats = ["mean", "std", "min", "max", "p25", "p50", "p75", "range"]
        features = []
        for key in sorted(aggregated_metrics.keys()):
            for stat in stats:
                features.append(aggregated_metrics[key].get(stat, 0.0))
        return features
