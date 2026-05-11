import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.services.pose_service import PoseService
from app.services.scoring_service import ScoringService
from app.services.feedback_service import FeedbackService
from app.core.config import settings

router = APIRouter()

pose_service    = PoseService()
scoring_service = ScoringService()
feedback_service = FeedbackService()


@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    side: str = "right",
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

    # Guardar vídeo temporalmente
    video_id   = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    input_path    = os.path.join(upload_dir, f"{video_id}_input.mp4")
    annotated_path = os.path.join(upload_dir, f"{video_id}_annotated.mp4")

    async with aiofiles.open(input_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
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

        # 2. Puntuación técnica
        scoring_result = scoring_service.score(pose_result["aggregated_metrics"])

        # 3. Feedback textual
        feedback_text = feedback_service.generate(
            metrics=pose_result["aggregated_metrics"],
            score=scoring_result["score"],
            breakdown=scoring_result["breakdown"],
        )

        # 4. Limpiar vídeo de entrada en background
        background_tasks.add_task(os.remove, input_path)

        return JSONResponse({
            "video_id":          video_id,
            "annotated_video_url": f"/uploads/{video_id}_annotated.mp4",
            "metrics_series":    pose_result["metrics_series"],
            "aggregated_metrics": pose_result["aggregated_metrics"],
            "detection_rate":    pose_result["detection_rate"],
            "score":             scoring_result["score"],
            "breakdown":         scoring_result["breakdown"],
            "feedback":          feedback_text,
            "n_frames":          pose_result["n_frames"],
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")
