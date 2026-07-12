"""
feedback_service.py
-------------------
Servicio de generación de feedback textual mediante LLM (Claude) + RAG (ChromaDB).
Devuelve un dict estructurado: {summary, issues, tips}
"""

import json
import re
import anthropic
from app.core.config import settings

# Contexto de fallback cuando ChromaDB no está disponible — cubre las 6 métricas
BIOMECHANICAL_CONTEXT = """
Criterios biomecánicos del golpe de derecha en tenis (forehand).
Rangos basados en Elliott et al. (2003) y Landlinger et al. (2012).

CODO (elbow_angle) — rango óptimo 100–160°:
- Por debajo de 100°: flexión excesiva, acorta la palanca y reduce potencia y alcance.
- Por encima de 160°: hiperextensión prematura, pérdida de control del golpe.

HOMBRO (shoulder_angle) — rango óptimo 60–120°:
- Por debajo de 60°: brazo demasiado bajo, reduce la zona de impacto.
- Por encima de 120°: brazo muy elevado, dificulta la pronación de muñeca.

RODILLAS (knee_angle) — rango óptimo 130–170°:
- Por debajo de 130°: flexión excesiva, limita la transferencia de energía desde las piernas.
- Por encima de 170°: piernas casi rectas, reduce estabilidad y base de apoyo.

TRONCO (trunk_tilt) — rango óptimo 0–20°:
- Por encima de 20°: inclinación lateral excesiva, indica desequilibrio postural o compensación técnica.

ROTACIÓN DE CADERAS (hip_separation) — rango óptimo 20–60°:
- Por debajo de 20°: caderas y hombros rotan juntos, sin separación. Pérdida de potencia por cadena cinética incompleta.
- Por encima de 60°: apertura prematura de caderas antes del impacto, reduce control direccional.
- La secuencia óptima de la cadena cinética es: caderas → hombros → codo → muñeca.

VELOCIDAD DE MUÑECA (wrist_speed) — rango óptimo 200–600 °/s:
- Por debajo de 200°/s: muñeca bloqueada, sin aceleración distal. Golpe sin potencia ni topspin efectivo.
- Por encima de 600°/s: exceso de fuerza en el segmento distal sin apoyo de la cadena cinética proximal.
"""


def _parse_feedback_json(text: str) -> dict:
    """Extrae el JSON del response del LLM. Fallback si el modelo no cumple el formato."""
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return {"summary": text, "issues": [], "tips": []}


class FeedbackService:

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        try:
            from app.services.rag_service import RAGService
            self.rag = RAGService()
        except ImportError:
            self.rag = None

    def generate(self, metrics: dict, score: float, breakdown: dict) -> dict:
        """
        Devuelve un dict con estructura:
          { "summary": str, "issues": [str, ...], "tips": [str, ...] }
        """
        if self.client:
            return self._generate_with_llm(metrics, score, breakdown)
        return self._generate_with_rules(score, breakdown)

    def _generate_with_llm(self, metrics: dict, score: float, breakdown: dict) -> dict:
        # Construir query RAG a partir de las métricas fuera de rango
        failing = [info["label"] for info in breakdown.values() if info["status"] != "ok"]
        rag_query = " ".join(failing) if failing else "técnica golpe derecha tenis"
        if self.rag is not None:
            biomechanical_context = self.rag.retrieve(rag_query)
        else:
            biomechanical_context = BIOMECHANICAL_CONTEXT

        metrics_summary = []
        for key, info in breakdown.items():
            status_text = {
                "ok":   "dentro del rango óptimo",
                "low":  "por debajo del rango óptimo",
                "high": "por encima del rango óptimo",
            }.get(info["status"], "desconocido")
            metrics_summary.append(
                f"- {info['label']}: {round(info['value'], 1)}° "
                f"(rango óptimo {info['range'][0]}-{info['range'][1]}°) "
                f"— {status_text}, puntuación parcial: {info['score']}/100"
            )

        metrics_text = "\n".join(metrics_summary)

        prompt = f"""Eres un entrenador experto de tenis analizando el golpe de derecha de un jugador.

{biomechanical_context}

RESULTADOS DEL ANÁLISIS:
Puntuación global: {score}/100

Métricas por dimensión:
{metrics_text}

INSTRUCCIONES:
Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta, sin texto adicional antes ni después:
{{
  "summary": "Evaluación general del golpe en 2-3 frases. Menciona puntos positivos y nivel general. Tono motivador.",
  "issues": ["Descripción del fallo más importante (incluye valor medido y rango óptimo)", "Segundo fallo si existe"],
  "tips": ["Consejo concreto y accionable para corregir el fallo 1", "Consejo para el fallo 2"]
}}

Reglas estrictas:
- summary: exactamente 2-3 frases, sin listas
- issues: solo los 1-2 fallos más importantes. Array vacío [] si todo está dentro del rango óptimo.
- tips: un tip por cada issue (misma longitud que issues). Tips prácticos, sin tecnicismos.
- El JSON debe ser válido. No añadas comentarios ni texto fuera del JSON."""

        try:
            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return _parse_feedback_json(message.content[0].text)
        except Exception as e:
            print(f"Error en LLM: {e}. Usando feedback por reglas.")
            return self._generate_with_rules(score, breakdown)

    @staticmethod
    def _generate_with_rules(score: float, breakdown: dict) -> dict:
        positives = [info["label"] for info in breakdown.values() if info["status"] == "ok"]
        improvements = [
            (info["label"], info["status"], round(info["value"], 1), info["range"])
            for info in breakdown.values()
            if info["status"] != "ok"
        ][:2]

        if score >= 80:
            base = "El golpe muestra una técnica sólida con buen control general."
        elif score >= 60:
            base = "El golpe tiene una base técnica correcta con margen de mejora."
        else:
            base = "El golpe presenta varios aspectos técnicos a trabajar."

        summary = base
        if positives:
            summary += f" Los ángulos de {', '.join(p.lower() for p in positives)} están dentro de los rangos óptimos."

        issues, tips = [], []
        for label, status, val, rng in improvements:
            if status == "low":
                issues.append(f"{label}: {val}° está por debajo del rango óptimo ({rng[0]}-{rng[1]}°).")
                tips.append(f"Trabaja en aumentar el ángulo de {label.lower()} durante la ejecución del golpe.")
            else:
                issues.append(f"{label}: {val}° supera el rango óptimo ({rng[0]}-{rng[1]}°).")
                tips.append(f"Reduce el ángulo de {label.lower()} para mejorar el control del golpe.")

        return {"summary": summary, "issues": issues, "tips": tips}
