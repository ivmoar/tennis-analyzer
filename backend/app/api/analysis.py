import os
import uuid
import aiofiles
import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.services.pose_service import PoseService
from app.services.scoring_service import ScoringService
from app.services.feedback_service import FeedbackService
from app.core.config import settings

router = APIRouter()

pose_service    = PoseService()
scoring_service = ScoringService()
feedback_service = FeedbackService()


def _remove_if_exists(path: str):
    if os.path.exists(path):
        os.remove(path)


def _get_video_duration_sec(path: str) -> float:
    cap = cv2.VideoCapture(path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        if fps <= 0 or frame_count <= 0:
            return 0.0
        return frame_count / fps
    finally:
        cap.release()


@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    side: str = Form("right"),
):
    """
    Recibe un vídeo de un golpe de derecha y devuelve:
    - URL del vídeo anotado con landmarks
    - Métricas cinemáticas por fotograma
    - Puntuación global 0-100
    - Desglose por dimensión biomecánica
    - Texto de feedback generado por LLM
    """

    # Validación del archivo
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {file.content_type}. "
                   f"Usa MP4, MOV o AVI."
        )

    if side not in {"left", "right"}:
        raise HTTPException(
            status_code=400,
            detail="Lado dominante no válido. Usa 'left' o 'right'."
        )

    # Guardar vídeo temporalmente
    video_id   = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    input_path    = os.path.join(upload_dir, f"{video_id}_input.mp4")
    annotated_path = os.path.join(upload_dir, f"{video_id}_annotated.mp4")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"El vídeo pesa {size_mb:.0f} MB. El límite es {settings.MAX_VIDEO_SIZE_MB} MB."
        )

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)

    try:
        duration_sec = _get_video_duration_sec(input_path)
        if duration_sec > settings.MAX_VIDEO_DURATION_SEC:
            raise HTTPException(
                status_code=400,
                detail=f"El vídeo dura {duration_sec:.0f} s. "
                       f"El límite es {settings.MAX_VIDEO_DURATION_SEC} s."
            )

        # 1. Extracción de keypoints y métricas
        pose_result = pose_service.analyze(
            video_path=input_path,
            output_path=annotated_path,
            side=side,
        )

        if not pose_result["metrics_series"]:
            raise HTTPException(
                status_code=422,
                detail="No se detectó ninguna pose en el vídeo. "
                       "Asegúrate de que el jugador es visible en todo momento."
            )

        # 1b. Validar que el vídeo contiene un golpe de derecha analizable
        try:
            pose_service.validate_forehand(pose_result, side)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # 2. Puntuación técnica
        scoring_result = scoring_service.score(pose_result["aggregated_metrics"])

        # 3. Feedback textual
        feedback_text = feedback_service.generate(
            metrics=pose_result["aggregated_metrics"],
            score=scoring_result["score"],
            breakdown=scoring_result["breakdown"],
        )

        # 4. Limpiar vídeo de entrada en background
        background_tasks.add_task(_remove_if_exists, input_path)

        return JSONResponse({
            "video_id":          video_id,
            "annotated_video_url": f"/uploads/{video_id}_annotated.mp4",
            "metrics_series":    pose_result["metrics_series"],
            "landmarks_series":   pose_result["landmarks_series"],
            "kinematics_series":  pose_result["kinematics_series"],
            "aggregated_metrics": pose_result["aggregated_metrics"],
            "phases":             pose_result["phases"],
            "event_timing":       pose_result["event_timing"],
            "feature_vector":      pose_result["feature_vector"],
            "feature_names":       pose_result["feature_names"],
            "landmark_names":      pose_result["landmark_names"],
            "detection_rate":    pose_result["detection_rate"],
            "score":             scoring_result["score"],
            "scoring_method":    scoring_result.get("scoring_method", "rules"),
            "breakdown":         scoring_result["breakdown"],
            "feedback":          feedback_text,
            "n_frames":          pose_result["n_frames"],
            "fps":               pose_result["fps"],
        })

    except HTTPException:
        _remove_if_exists(input_path)
        _remove_if_exists(annotated_path)
        raise
    except Exception as e:
        _remove_if_exists(input_path)
        _remove_if_exists(annotated_path)
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")
