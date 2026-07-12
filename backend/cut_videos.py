"""
cut_videos.py
-------------
Paso previo al entrenamiento: corta vídeos largos en clips individuales
de un golpe de derecha cada uno.

FLUJO DE USO:
─────────────
Paso 1 — Genera la plantilla CSV:
    python cut_videos.py --template

    Esto crea 'data/cuts/cuts.csv'. Ábrelo en Excel/Numbers/cualquier editor.

Paso 2 — Rellena el CSV con tus timestamps mientras ves los vídeos:
    Columnas: video_file | start | end | score | notes
    Ejemplo:
        partido1.mp4 | 0:15  | 0:21 | 75 | buena rotación de cadera
        partido1.mp4 | 1:03  | 1:09 | 45 | codo demasiado alto
        partido2.mp4 | 0:08  | 0:14 | 80 |
    • start/end pueden ser  MM:SS  o  HH:MM:SS  o directamente segundos (ej: 83.5)
    • score: tu valoración 0-100 del golpe (puedes dejarlo vacío y rellenarlo después)

Paso 3 — Corta todos los clips:
    python cut_videos.py --cut --videos_dir /ruta/a/tus/videos/largos

    Los clips se guardan en data/videos/ listos para el pipeline.
    También genera data/labels/labels_from_cuts.csv con las puntuaciones ya puestas.

Paso 4 — Entrena directamente (sin pasar por --mode label si ya tienes scores):
    python train_model.py --mode label --videos_dir data/videos   # extrae features
    python train_model.py --mode train --labels data/labels/labels_from_cuts.csv
"""

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

CUTS_CSV = "data/cuts/cuts.csv"
OUTPUT_VIDEOS_DIR = "data/videos"
OUTPUT_LABELS_CSV = "data/labels/labels_from_cuts.csv"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def parse_time(t: str) -> float:
    """Convierte '1:23', '0:01:23', '83.5' en segundos float."""
    t = str(t).strip()
    if not t:
        raise ValueError("Timestamp vacío")
    if ":" in t:
        parts = t.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(t)


def output_filename(video_file: str, index: int) -> str:
    stem = Path(video_file).stem
    return f"{stem}_{index:03d}.mp4"


# ─────────────────────────────────────────────
# Paso 1: crear plantilla CSV
# ─────────────────────────────────────────────

def create_template():
    os.makedirs(os.path.dirname(CUTS_CSV), exist_ok=True)

    if os.path.exists(CUTS_CSV):
        print(f"Ya existe {CUTS_CSV} — no se sobreescribe.")
        print("Bórralo manualmente si quieres regenerar la plantilla.")
        return

    with open(CUTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["video_file", "start", "end", "score", "notes"])
        # Filas de ejemplo
        writer.writerow(["partido1.mp4", "0:15", "0:21", "75", "ejemplo - borra estas filas"])
        writer.writerow(["partido1.mp4", "1:03", "1:09", "45", "ejemplo"])
        writer.writerow(["partido2.mp4", "0:08", "0:14", "", "sin puntuación todavía"])

    print(f"Plantilla creada: {CUTS_CSV}")
    print()
    print("Instrucciones:")
    print("  1. Abre el CSV en Excel, Numbers o un editor de texto")
    print("  2. Por cada derecha en tus vídeos, añade una fila:")
    print("       video_file  → nombre del archivo (incluyendo extensión)")
    print("       start       → tiempo de inicio  (ej: 1:23  o  83)")
    print("       end         → tiempo de fin     (ej: 1:29  o  89)")
    print("       score       → tu valoración 0-100 (puedes dejarlo vacío)")
    print("       notes       → comentario opcional")
    print()
    print("  3. Cuando hayas rellenado el CSV, ejecuta:")
    print(f"       python cut_videos.py --cut --videos_dir /ruta/a/tus/videos")


# ─────────────────────────────────────────────
# Paso 3: cortar clips
# ─────────────────────────────────────────────

def cut_videos(videos_dir: str):
    if not os.path.exists(CUTS_CSV):
        print(f"ERROR: No se encuentra {CUTS_CSV}")
        print("Primero ejecuta:  python cut_videos.py --template")
        sys.exit(1)

    os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
    os.makedirs("data/labels", exist_ok=True)

    rows = []
    with open(CUTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("El CSV está vacío. Rellénalo primero.")
        sys.exit(1)

    # Agrupar por video para asignar índices correlativos por vídeo
    from collections import defaultdict
    video_counter = defaultdict(int)

    labels_rows = []
    ok = 0
    errors = 0

    print(f"\nCortando {len(rows)} clips desde {videos_dir}...\n")

    for row in rows:
        video_file = row.get("video_file", "").strip()
        start_raw  = row.get("start", "").strip()
        end_raw    = row.get("end", "").strip()
        score      = row.get("score", "").strip()
        notes      = row.get("notes", "").strip()

        if not video_file or not start_raw or not end_raw:
            print(f"  SKIP — fila incompleta: {row}")
            continue

        # Validar timestamps
        try:
            start_sec = parse_time(start_raw)
            end_sec   = parse_time(end_raw)
        except ValueError as e:
            print(f"  ERROR timestamp en '{video_file}': {e}")
            errors += 1
            continue

        if end_sec <= start_sec:
            print(f"  ERROR: end ({end_raw}) <= start ({start_raw}) en '{video_file}'")
            errors += 1
            continue

        input_path = os.path.join(videos_dir, video_file)
        if not os.path.exists(input_path):
            print(f"  ERROR: no se encuentra '{input_path}'")
            errors += 1
            continue

        video_counter[video_file] += 1
        idx = video_counter[video_file]
        out_name = output_filename(video_file, idx)
        out_path = os.path.join(OUTPUT_VIDEOS_DIR, out_name)

        if os.path.exists(out_path):
            print(f"  [skip, ya existe] {out_name}")
            labels_rows.append({"filename": out_name, "score": score, "notes": notes})
            ok += 1
            continue

        duration = end_sec - start_sec

        cmd = [
            "ffmpeg",
            "-y",                          # sobreescribir sin preguntar
            "-ss", str(start_sec),         # seek rápido (antes del input)
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-crf", "23",                  # buena calidad, tamaño razonable
            "-preset", "fast",
            "-an",                         # sin audio (no hace falta)
            "-loglevel", "error",          # solo mostrar errores
            out_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR ffmpeg en '{video_file}' [{start_raw}-{end_raw}]:")
            print(f"    {result.stderr.strip()[:200]}")
            errors += 1
            continue

        duration_actual = end_sec - start_sec
        print(f"  OK  {out_name}  ({duration_actual:.1f}s)  score={score or '—'}")
        labels_rows.append({"filename": out_name, "score": score, "notes": notes})
        ok += 1

    # Guardar CSV de etiquetas
    if labels_rows:
        with open(OUTPUT_LABELS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["filename", "score", "notes"])
            writer.writeheader()
            writer.writerows(labels_rows)
        print(f"\nCSV de etiquetas guardado: {OUTPUT_LABELS_CSV}")

    print(f"\n{'─'*50}")
    print(f"Resultado: {ok} clips OK, {errors} errores")
    print(f"Clips guardados en: {OUTPUT_VIDEOS_DIR}/")
    print()

    scored = sum(1 for r in labels_rows if r["score"])
    unscored = len(labels_rows) - scored

    if unscored > 0:
        print(f"ATENCIÓN: {unscored} clips sin puntuación.")
        print(f"Abre {OUTPUT_LABELS_CSV} y rellena la columna 'score' (0-100).")
        print()

    print("Siguiente paso:")
    print("  python train_model.py --mode label --videos_dir data/videos")
    print(f"  python train_model.py --mode train --labels {OUTPUT_LABELS_CSV}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Corta vídeos largos en clips individuales de forehand"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--template", action="store_true",
        help="Genera la plantilla CSV para rellenar timestamps"
    )
    group.add_argument(
        "--cut", action="store_true",
        help="Corta los clips según el CSV relleno"
    )
    parser.add_argument(
        "--videos_dir", default=".",
        help="Carpeta donde están los vídeos largos originales (solo con --cut)"
    )
    args = parser.parse_args()

    # Trabajar desde el directorio del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if args.template:
        create_template()
    elif args.cut:
        cut_videos(args.videos_dir)
