"""
train_model.py
--------------
Script para etiquetar vídeos y entrenar el modelo Random Forest
de puntuación técnica del golpe de derecha.

Uso:
  # Paso 0: pon los vídeos fuente en data/raw/ y rellena data/cuts/cuts.csv
  #   (columnas: video_file, start, end, score, notes)
  python train_model.py --mode cut

  # Paso 1: extraer características de los cortes
  python train_model.py --mode label

  # Paso 2: revisar data/labels/labels.csv y añadir scores si faltan

  # Paso 3: entrenar el modelo
  python train_model.py --mode train

  # Paso 4: evaluar el modelo entrenado
  python train_model.py --mode evaluate
"""

import argparse
import os
import sys
import json
import csv
import subprocess

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
CUTS_PATH         = "data/cuts/cuts.csv"
CUTS_OUTPUT_DIR   = "data/videos"
CUTS_SOURCE_DIR   = "data/raw_videos"


def cut_videos_from_csv(cuts_path: str = CUTS_PATH,
                        source_dir: str = CUTS_SOURCE_DIR,
                        output_dir: str = CUTS_OUTPUT_DIR):
    """
    Lee cuts.csv y recorta cada segmento con ffmpeg.

    Formato del CSV:
      video_file, start, end, score, notes
      IMG_2393.MOV, 0:10, 0:12, 57, poca extensión

    Los cortes se guardan en output_dir con nombre <video_base>_<start>_<end>.mp4
    y se añaden automáticamente a labels.csv con su score.
    """
    if not os.path.exists(cuts_path):
        print(f"ERROR: No se encuentra {cuts_path}")
        print(f"Crea el archivo con columnas: video_file,start,end,score,notes")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)

    # Cargar etiquetas existentes para no duplicar
    existing_labels = {}
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH) as f:
            for row in csv.DictReader(f):
                existing_labels[row["filename"]] = row

    new_entries = []

    with open(cuts_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\nProcesando {len(rows)} cortes de {cuts_path}...\n")

    for row in rows:
        video_file = row["video_file"].strip()
        start      = row["start"].strip()
        end        = row["end"].strip()
        score      = row.get("score", "").strip()
        notes      = row.get("notes", "").strip()

        # Nombre único del corte
        slug = start.replace(":", "-") + "_" + end.replace(":", "-")
        base = os.path.splitext(video_file)[0]
        out_name = f"{base}__{slug}.mp4"
        out_path = os.path.join(output_dir, out_name)

        if out_name in existing_labels:
            print(f"  [ya existe] {out_name}")
            continue

        src_path = os.path.join(source_dir, video_file)
        if not os.path.exists(src_path):
            print(f"  [AVISO] No se encuentra el vídeo fuente: {src_path}")
            continue

        print(f"  Cortando {video_file} [{start} → {end}] → {out_name}")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", start, "-to", end,
                    "-i", src_path,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    "-movflags", "+faststart",
                    "-an",
                    out_path,
                ],
                check=True,
                capture_output=True,
            )
            print(f"    OK")
            new_entries.append({"filename": out_name, "score": score, "notes": notes})
        except subprocess.CalledProcessError as e:
            print(f"    ERROR ffmpeg: {e.stderr.decode()[-200:]}")

    # Añadir nuevas entradas a labels.csv
    if new_entries:
        write_header = not os.path.exists(LABELS_PATH)
        with open(LABELS_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["filename", "score", "notes"])
            if write_header:
                writer.writeheader()
            writer.writerows(new_entries)
        print(f"\n{len(new_entries)} corte(s) añadidos a {LABELS_PATH}")
        no_score = [e["filename"] for e in new_entries if not e["score"]]
        if no_score:
            print(f"Recuerda añadir el score en {LABELS_PATH} para:")
            for n in no_score:
                print(f"  - {n}")
    else:
        print("\nNada nuevo que procesar.")

    print(f"\nSiguiente paso: python train_model.py --mode label")


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
    parser.add_argument("--mode", choices=["cut", "label", "train", "evaluate"], required=True)
    parser.add_argument("--videos_dir", default="data/videos",
                        help="Directorio con los vídeos de entrenamiento")
    parser.add_argument("--labels",     default=LABELS_PATH,
                        help="Ruta al archivo CSV de etiquetas")
    parser.add_argument("--cuts",       default=CUTS_PATH,
                        help="Ruta al CSV de cortes (modo cut)")
    parser.add_argument("--source_dir", default=CUTS_SOURCE_DIR,
                        help="Directorio con los vídeos fuente (modo cut)")
    args = parser.parse_args()

    if args.mode == "cut":
        cut_videos_from_csv(args.cuts, args.source_dir, args.videos_dir)
    elif args.mode == "label":
        cache = extract_features_from_videos(args.videos_dir)
        generate_labels_csv(cache)
    elif args.mode == "train":
        if not os.path.exists(FEATURES_PATH):
            print("Extrayendo características primero...")
            cache = extract_features_from_videos(args.videos_dir)
        train(args.labels)
    elif args.mode == "evaluate":
        evaluate(args.labels)
