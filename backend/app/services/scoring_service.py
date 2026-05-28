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
from app.core.constants import REFERENCE_RANGES, DIMENSION_WEIGHTS, FEEDBACK_LABELS
from app.services.pose_service import PoseService


class ScoringService:

    def __init__(self):
        self.model = None
        self.feature_names = None
        self._load_model()

    def _load_model(self):
        path = settings.MODEL_PATH
        if os.path.exists(path):
            print(f"Cargando modelo Random Forest desde {path}")
            payload = joblib.load(path)
            if isinstance(payload, dict):
                self.model = payload.get("model")
                self.feature_names = payload.get("feature_names")
            else:
                self.model = payload
                self.feature_names = None
            return
        print("Modelo Random Forest no encontrado. Usando scoring por rangos.")

    def score(self, aggregated_metrics: dict) -> dict:
        """
        Calcula la puntuación global (0-100) y el desglose por dimensión.
        Usa el modelo Random Forest si está disponible, o la función
        de rangos en caso contrario.
        """
        if self.model is not None:
            result = self._score_with_model(aggregated_metrics)
            result["scoring_method"] = "model"
            return result
        result = self._score_with_ranges(aggregated_metrics)
        result["scoring_method"] = "rules"
        return result

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

    def _build_feature_vector(self, aggregated_metrics: dict) -> list:
        """Construye el vector de características para el modelo."""
        if not self.feature_names:
            return PoseService.build_feature_vector(aggregated_metrics)

        features = []
        for name in self.feature_names:
            metric, stat = name.rsplit("_", 1)
            features.append(aggregated_metrics.get(metric, {}).get(stat, 0.0))
        return features
