"""
scoring_service.py
------------------
Servicio de puntuación técnica del golpe de derecha.

En la versión actual (sin modelo entrenado todavía) usa una función
de puntuación basada en rangos bibliográficos. Cuando el modelo
Random Forest esté entrenado, se carga automáticamente desde MODEL_PATH.
"""

import os
import numpy as np
import joblib
from app.core.config import settings

# Rangos óptimos de referencia (Elliott et al., 2003; Landlinger et al., 2012)
REFERENCE_RANGES = {
    "elbow_angle":    (100, 160),
    "shoulder_angle": (60,  120),
    "knee_angle":     (130, 170),
    "trunk_tilt":     (0,   20),
}

DIMENSION_WEIGHTS = {
    "elbow_angle":    0.30,   # Extensión del brazo: crítico en el impacto
    "shoulder_angle": 0.25,   # Posición del hombro
    "knee_angle":     0.25,   # Flexión de piernas
    "trunk_tilt":     0.20,   # Postura del tronco
}

FEEDBACK_LABELS = {
    "elbow_angle":    "Extensión de codo",
    "shoulder_angle": "Posición de hombro",
    "knee_angle":     "Flexión de rodillas",
    "trunk_tilt":     "Inclinación de tronco",
}


class ScoringService:

    def __init__(self):
        self.model = self._load_model()

    def _load_model(self):
        path = settings.MODEL_PATH
        if os.path.exists(path):
            print(f"Cargando modelo Random Forest desde {path}")
            return joblib.load(path)
        print("Modelo Random Forest no encontrado. Usando scoring por rangos.")
        return None

    def score(self, aggregated_metrics: dict) -> dict:
        """
        Calcula la puntuación global (0-100) y el desglose por dimensión.
        Usa el modelo Random Forest si está disponible, o la función
        de rangos en caso contrario.
        """
        if self.model is not None:
            return self._score_with_model(aggregated_metrics)
        return self._score_with_ranges(aggregated_metrics)

    def _score_with_ranges(self, aggregated_metrics: dict) -> dict:
        """Scoring basado en proximidad a rangos óptimos bibliográficos."""
        breakdown = {}
        weighted_score = 0.0

        for key, (lo, hi) in REFERENCE_RANGES.items():
            if key not in aggregated_metrics:
                continue
            mean_val = aggregated_metrics[key]["mean"]
            weight   = DIMENSION_WEIGHTS.get(key, 0.25)

            # Puntuación por dimensión: 100 si dentro del rango,
            # penalización proporcional a la desviación
            center = (lo + hi) / 2
            half   = (hi - lo) / 2

            if lo <= mean_val <= hi:
                dim_score = 100.0
            else:
                deviation = max(lo - mean_val, mean_val - hi, 0)
                dim_score = max(0.0, 100.0 - (deviation / half) * 50)

            breakdown[key] = {
                "label":     FEEDBACK_LABELS[key],
                "value":     mean_val,
                "score":     round(dim_score, 1),
                "range":     (lo, hi),
                "status":    "ok" if lo <= mean_val <= hi else
                             ("low" if mean_val < lo else "high"),
            }
            weighted_score += dim_score * weight

        global_score = round(min(weighted_score, 100.0), 1)
        return {"score": global_score, "breakdown": breakdown}

    def _score_with_model(self, aggregated_metrics: dict) -> dict:
        """Scoring usando el modelo Random Forest entrenado."""
        feature_vector = self._build_feature_vector(aggregated_metrics)
        score = float(self.model.predict([feature_vector])[0])
        score = round(min(max(score, 0), 100), 1)

        # El desglose sigue usando rangos para interpretabilidad
        breakdown_result = self._score_with_ranges(aggregated_metrics)
        breakdown_result["score"] = score
        return breakdown_result

    @staticmethod
    def _build_feature_vector(aggregated_metrics: dict) -> list:
        """Construye el vector de características para el modelo."""
        features = []
        keys = ["elbow_angle", "shoulder_angle", "knee_angle", "trunk_tilt", "hip_separation"]
        stats = ["mean", "std", "min", "max", "p25", "p75"]
        for key in keys:
            if key in aggregated_metrics:
                for stat in stats:
                    features.append(aggregated_metrics[key].get(stat, 0.0))
            else:
                features.extend([0.0] * len(stats))
        return features
