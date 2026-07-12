"""
train_model.py
--------------
Script para etiquetar vídeos y entrenar el modelo Random Forest
de puntuación técnica del golpe de derecha.

Uso:
  # Paso 1: procesar vídeos y generar archivo de etiquetas
  python train_model.py --mode label --videos_dir data/videos

  # Paso 2: revisar y editar data/labels/labels.csv con tus puntuaciones (0-100)

  # Paso 3: entrenar el modelo
  python train_model.py --mode train --labels data/labels/labels.csv

  # Paso 4: evaluar el modelo entrenado
  python train_model.py --mode evaluate --labels data/labels/labels.csv
"""

import argparse
import os
import sys
import json
import csv

import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# Añadir el backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.services.pose_service import PoseService

MODEL_OUTPUT_PATH = "app/models/random_forest_model.joblib"
LABELS_PATH       = "data/labels/labels.csv"
FEATURES_PATH     = "data/labels/features_cache.json"


def extract_features_from_videos(videos_dir: str) -> dict:
    """
    Procesa todos los vídeos del directorio y extrae sus vectores de características.
    Guarda un caché en JSON para no reprocesar.
    """
    pose_service = PoseService()

    # Cargar caché si existe
    cache = {}
    if os.path.exists(FEATURES_PATH):
        with open(FEATURES_PATH) as f:
            cache = json.load(f)
        print(f"Caché de características cargado: {len(cache)} vídeos")

    video_files = [
        f for f in os.listdir(videos_dir)
        if f.lower().endswith((".mp4", ".mov", ".avi"))
    ]

    print(f"\nProcesando {len(video_files)} vídeos en {videos_dir}...")

    for filename in video_files:
        if filename in cache:
            print(f"  [cache] {filename}")
            continue

        video_path = os.path.join(videos_dir, filename)
        print(f"  Analizando: {filename} ...")

        try:
            result = pose_service.analyze(
                video_path=video_path,
                output_path=os.devnull,   # No guardar vídeo anotado
                side="right",
            )
            if result["aggregated_metrics"]:
                cache[filename] = {
                    "features":       result["feature_vector"],
                    "feature_names":  result["feature_names"],
                    "detection_rate": result["detection_rate"],
                    "n_frames":       result["n_frames"],
                    "event_timing":   result.get("event_timing", {}),
                }
                print(f"    OK — {result['n_frames']} fotogramas, "
                      f"detección: {result['detection_rate']*100:.1f}%")
            else:
                print(f"    SKIP — no se detectó pose")
        except Exception as e:
            print(f"    ERROR: {e}")

    # Guardar caché actualizado
    os.makedirs(os.path.dirname(FEATURES_PATH), exist_ok=True)
    with open(FEATURES_PATH, "w") as f:
        json.dump(cache, f, indent=2)

    return cache


def generate_labels_csv(features_cache: dict):
    """Genera un CSV con los vídeos procesados para que el entrenador los etiquete."""
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)

    existing = {}
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH) as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["filename"]] = row.get("score", "")

    with open(LABELS_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "score", "notes"])
        for filename in features_cache:
            score = existing.get(filename, "")
            writer.writerow([filename, score, ""])

    print(f"\nArchivo de etiquetas generado: {LABELS_PATH}")
    print("Abre el archivo, rellena la columna 'score' (0-100) para cada vídeo")
    print("y vuelve a ejecutar con --mode train")


def load_dataset(labels_path: str, features_cache: dict):
    """Carga el dataset completo (características + etiquetas)."""
    X, y, names = [], [], []

    with open(labels_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["filename"]
            score    = row.get("score", "").strip()

            if not score:
                continue  # Sin etiquetar todavía
            try:
                score = float(score)
            except ValueError:
                continue

            if filename not in features_cache:
                print(f"  AVISO: {filename} no tiene características extraídas")
                continue

            X.append(features_cache[filename]["features"])
            y.append(score)
            names.append(filename)

    return np.array(X), np.array(y), names


def train(labels_path: str):
    """Entrena el modelo Random Forest con los vídeos etiquetados."""
    if not os.path.exists(FEATURES_PATH):
        print("ERROR: Primero ejecuta --mode label para extraer características")
        sys.exit(1)

    with open(FEATURES_PATH) as f:
        cache = json.load(f)

    X, y, names = load_dataset(labels_path, cache)

    if len(X) < 5:
        print(f"ERROR: Solo hay {len(X)} muestras etiquetadas. "
              f"Necesitas al menos 5 para entrenar (recomendado: 30+)")
        sys.exit(1)

    print(f"\nDataset: {len(X)} muestras etiquetadas")
    print(f"Puntuación media: {y.mean():.1f} | Desv. típica: {y.std():.1f}")
    print(f"Rango: {y.min():.0f} - {y.max():.0f}")

    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=2,
        random_state=42,
    )
    xgb_model = XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )

    feature_names = _get_feature_names(cache)

    # Validación cruzada comparativa (5-fold, MAE)
    results = {}
    for name, m in [("RandomForest", rf_model), ("XGBoost", xgb_model)]:
        if len(X) >= 10:
            cv = cross_val_score(m, X, y, cv=5, scoring="neg_mean_absolute_error")
            results[name] = {"mae": -cv.mean(), "std": cv.std(), "model": m}
        else:
            results[name] = {"mae": float("inf"), "std": 0.0, "model": m}

    print(f"\n{'Modelo':<15} {'MAE_cv':>8} {'Std':>8}")
    print("-" * 35)
    for name, r in results.items():
        print(f"{name:<15} {r['mae']:>8.2f} {r['std']:>8.2f}")

    # Elegir el modelo con menor MAE
    best_name = min(results, key=lambda k: results[k]["mae"])
    best_model = results[best_name]["model"]
    print(f"\nMejor modelo: {best_name} (MAE={results[best_name]['mae']:.2f})")

    # Entrenar ambos con todos los datos
    rf_model.fit(X, y)
    xgb_model.fit(X, y)

    # Importancia de características del mejor modelo
    importances = sorted(
        zip(feature_names, best_model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print("\nImportancia de características (top 10):")
    for feat, imp in importances[:10]:
        print(f"  {feat}: {imp:.3f}")

    # Guardar mejor modelo como producción
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump({"model": best_model, "feature_names": feature_names}, MODEL_OUTPUT_PATH)
    print(f"\nModelo de producción guardado en: {MODEL_OUTPUT_PATH}")

    # Guardar XGBoost siempre como referencia
    xgb_path = "app/models/xgboost_model.joblib"
    joblib.dump({"model": xgb_model, "feature_names": feature_names}, xgb_path)
    print(f"Modelo XGBoost guardado en: {xgb_path}")


def evaluate(labels_path: str):
    """Evalúa el modelo entrenado sobre el dataset completo."""
    if not os.path.exists(MODEL_OUTPUT_PATH):
        print("ERROR: No hay modelo entrenado. Ejecuta --mode train primero")
        sys.exit(1)

    if not os.path.exists(FEATURES_PATH):
        print("ERROR: No hay características extraídas")
        sys.exit(1)

    payload = joblib.load(MODEL_OUTPUT_PATH)
    model = payload["model"] if isinstance(payload, dict) else payload
    with open(FEATURES_PATH) as f:
        cache = json.load(f)

    X, y, names = load_dataset(labels_path, cache)

    if len(X) == 0:
        print("No hay muestras etiquetadas para evaluar")
        sys.exit(1)

    y_pred = model.predict(X)
    mae    = mean_absolute_error(y, y_pred)
    r2     = r2_score(y, y_pred)

    print(f"\nEvaluación del modelo:")
    print(f"  MAE (error absoluto medio): {mae:.2f} puntos")
    print(f"  R² (coeficiente de determinación): {r2:.3f}")
    print(f"\nPredicciones vs valores reales:")
    for name, real, pred in zip(names, y, y_pred):
        print(f"  {name:<40} real={real:.0f}  pred={pred:.1f}  "
              f"error={abs(real-pred):.1f}")


def _get_feature_names(features_cache: dict) -> list:
    for item in features_cache.values():
        if item.get("feature_names"):
            return item["feature_names"]
    if features_cache:
        n = len(next(iter(features_cache.values())).get("features", []))
        return [f"feature_{i}" for i in range(n)]
    return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Etiquetado y entrenamiento del modelo de puntuación"
    )
    parser.add_argument("--mode", choices=["label", "train", "evaluate"], required=True)
    parser.add_argument("--videos_dir", default="data/videos",
                        help="Directorio con los vídeos de entrenamiento")
    parser.add_argument("--labels",     default=LABELS_PATH,
                        help="Ruta al archivo CSV de etiquetas")
    args = parser.parse_args()

    if args.mode == "label":
        cache = extract_features_from_videos(args.videos_dir)
        generate_labels_csv(cache)
    elif args.mode == "train":
        if not os.path.exists(FEATURES_PATH):
            print("Extrayendo características primero...")
            cache = extract_features_from_videos(args.videos_dir)
        train(args.labels)
    elif args.mode == "evaluate":
        evaluate(args.labels)
