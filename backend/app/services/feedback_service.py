"""
feedback_service.py
-------------------
Servicio de generación de feedback textual mediante LLM (Claude).
Recibe las métricas del golpe y la puntuación, y genera un texto
de retroalimentación técnica orientado a la mejora del jugador.
"""

import anthropic
from app.core.config import settings

# Contexto biomecánico de referencia que se incluye en el prompt
# Basado en: Elliott et al. (2003), Landlinger et al. (2012)
BIOMECHANICAL_CONTEXT = """
Criterios biomecánicos del golpe de derecha en tenis (forehand):

CODO (ángulo en el impacto):
- Rango óptimo: 100-160 grados
- Por debajo de 100: flexión excesiva, reduce el alcance y la transferencia de fuerza
- Por encima de 160: hiperextensión prematura, pérdida de control

HOMBRO (ángulo de elevación del brazo dominante):
- Rango óptimo: 60-120 grados
- Por debajo de 60: brazo demasiado bajo, reduce la zona de impacto
- Por encima de 120: brazo demasiado elevado, dificulta el giro de muñeca

RODILLAS (flexión durante la ejecución):
- Rango óptimo: 130-170 grados (ligera flexión)
- Por debajo de 130: flexión excesiva, limita la transferencia de energía desde las piernas
- Por encima de 170: piernas muy extendidas, reduce la estabilidad

TRONCO (inclinación lateral):
- Rango óptimo: 0-20 grados
- Por encima de 20: inclinación excesiva, puede indicar desequilibrio o compensación técnica
"""


class FeedbackService:

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(self, metrics: dict, score: float, breakdown: dict) -> str:
        """
        Genera feedback textual personalizado basado en las métricas del golpe.
        Si no hay API key configurada, devuelve feedback basado en reglas.
        """
        if self.client:
            return self._generate_with_llm(metrics, score, breakdown)
        return self._generate_with_rules(score, breakdown)

    def _generate_with_llm(self, metrics: dict, score: float, breakdown: dict) -> str:
        """Genera feedback usando Claude como LLM."""

        # Construir resumen de métricas para el prompt
        metrics_summary = []
        for key, info in breakdown.items():
            status_text = {
                "ok":   "dentro del rango óptimo",
                "low":  "por debajo del rango óptimo",
                "high": "por encima del rango óptimo",
            }.get(info["status"], "desconocido")

            metrics_summary.append(
                f"- {info['label']}: {info['value']}° "
                f"(rango óptimo {info['range'][0]}-{info['range'][1]}°) "
                f"— {status_text}, puntuación parcial: {info['score']}/100"
            )

        metrics_text = "\n".join(metrics_summary)

        prompt = f"""Eres un entrenador experto de tenis analizando el golpe de derecha de un jugador.
        
Basándote en el siguiente análisis biomecánico y en tu conocimiento técnico del tenis, 
genera un feedback claro, constructivo y orientado a la mejora. 
El feedback debe ser comprensible para un jugador no profesional.

{BIOMECHANICAL_CONTEXT}

RESULTADOS DEL ANÁLISIS:
Puntuación global: {score}/100

Métricas por dimensión:
{metrics_text}

INSTRUCCIONES PARA EL FEEDBACK:
- Empieza reconociendo los aspectos positivos del golpe
- Identifica los 1-2 aspectos más importantes a mejorar (no todos a la vez)
- Da indicaciones concretas y accionables para mejorar esos aspectos
- Usa un tono motivador y constructivo
- Extensión: 3-4 párrafos
- No uses tecnicismos excesivos, el jugador debe entenderlo"""

        try:
            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error en LLM: {e}. Usando feedback por reglas.")
            return self._generate_with_rules(score, breakdown)

    @staticmethod
    def _generate_with_rules(score: float, breakdown: dict) -> str:
        """Feedback basado en reglas cuando no hay LLM disponible."""
        positives = [
            info["label"] for info in breakdown.values()
            if info["status"] == "ok"
        ]
        improvements = [
            (info["label"], info["status"], info["value"], info["range"])
            for info in breakdown.values()
            if info["status"] != "ok"
        ]

        lines = []

        if positives:
            lines.append(
                f"Aspectos positivos del golpe: {', '.join(positives)}. "
                f"Estos elementos están dentro de los rangos técnicos óptimos."
            )

        if improvements:
            lines.append("Aspectos a mejorar:")
            for label, status, val, rng in improvements:
                if status == "low":
                    lines.append(
                        f"- {label}: el valor actual ({val}°) está por debajo "
                        f"del rango óptimo ({rng[0]}-{rng[1]}°). "
                        f"Trabaja en aumentar este ángulo durante la ejecución."
                    )
                else:
                    lines.append(
                        f"- {label}: el valor actual ({val}°) supera "
                        f"el rango óptimo ({rng[0]}-{rng[1]}°). "
                        f"Reduce este ángulo para mejorar el control del golpe."
                    )

        if score >= 80:
            lines.append("En general, el golpe muestra una técnica sólida. "
                         "Continúa trabajando los detalles para alcanzar la excelencia.")
        elif score >= 60:
            lines.append("El golpe tiene una base técnica correcta con margen de mejora "
                         "en los aspectos indicados.")
        else:
            lines.append("El golpe presenta varios aspectos técnicos a trabajar. "
                         "Céntrate primero en los más importantes antes de pasar al siguiente.")

        return "\n\n".join(lines)
