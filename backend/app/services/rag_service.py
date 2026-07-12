"""
rag_service.py
--------------
Recuperación de contexto biomecánico mediante ChromaDB en memoria.
Base de conocimiento expandida: 24 documentos sobre biomecánica del forehand,
errores comunes, correcciones y drills (Elliott et al., 2003; Landlinger et al., 2012).
"""

BIOMECHANICAL_DOCS = [
    # ── CODO ────────────────────────────────────────────────────────────────
    (
        "codo_rango",
        "Codo — ángulo en el impacto (elbow_angle): rango óptimo 100–160° (Elliott et al., 2003). "
        "Un ángulo en ese rango garantiza extensión controlada del brazo, maximiza la zona de impacto "
        "y facilita la transferencia de fuerza desde el hombro hacia la raqueta.",
    ),
    (
        "codo_bajo",
        "Codo demasiado flexionado (elbow_angle < 100°): el codo permanece doblado en el momento "
        "del impacto. Esto acorta la palanca del brazo, reduce el alcance y la potencia del golpe. "
        "Corrección: practicar el gesto con un tubo o palo para inducir la extensión completa. "
        "Drill: golpes lentos frente al espejo enfocando la extensión de codo en el impacto.",
    ),
    (
        "codo_alto",
        "Codo hiperextendido (elbow_angle > 160°): extensión excesiva antes del impacto, "
        "reduce el control y puede sobrecargar el ligamento lateral. "
        "Corrección: concentrarse en mantener un leve ángulo de codo al conectar. "
        "Drill: shadow swings con pausa en el punto de impacto revisando la posición.",
    ),

    # ── HOMBRO ──────────────────────────────────────────────────────────────
    (
        "hombro_rango",
        "Hombro — ángulo de elevación del brazo dominante (shoulder_angle): rango óptimo 60–120° (Elliott et al., 2003). "
        "Mantener el brazo en este rango asegura una trayectoria de raqueta ascendente óptima "
        "y facilita el windshield-wiper motion del giro de muñeca en el follow-through.",
    ),
    (
        "hombro_bajo",
        "Hombro demasiado bajo (shoulder_angle < 60°): brazo excesivamente caído, reduce la zona "
        "de impacto y obliga a doblar la muñeca para alcanzar la bola. "
        "Causa frecuente: postura encorvada o inicio del backswing demasiado bajo. "
        "Corrección: iniciar el backswing con la punta de la raqueta a la altura de la cadera. "
        "Drill: golpear con la mano libre señalando hacia arriba durante la preparación.",
    ),
    (
        "hombro_alto",
        "Hombro demasiado elevado (shoulder_angle > 120°): brazo muy alzado reduce la comodidad "
        "del golpe y limita la rotación de muñeca. "
        "Corrección: bajar el punto de contacto, trabajar el timing de la preparación. "
        "Drill: pratique con globos para encontrar la altura natural de contacto.",
    ),

    # ── RODILLAS ─────────────────────────────────────────────────────────────
    (
        "rodillas_rango",
        "Rodillas — flexión durante la ejecución (knee_angle): rango óptimo 130–170° (Elliott et al., 2003). "
        "La ligera flexión baja el centro de gravedad, mejora el equilibrio y permite "
        "cargar energía desde las piernas hacia la cadena cinética.",
    ),
    (
        "rodillas_exceso",
        "Rodillas demasiado flexionadas (knee_angle < 130°): flexión excesiva provoca tensión "
        "en cuádriceps y limita la extensión rápida de piernas necesaria para transferir potencia. "
        "Corrección: no agacharse más de lo necesario para alcanzar la bola. "
        "Drill: golpear desde posición media con marcas en el suelo para fijar la altura óptima.",
    ),
    (
        "rodillas_extendidas",
        "Rodillas demasiado extendidas (knee_angle > 170°): piernas casi rectas reducen base "
        "de apoyo y estabilidad. Golpe plano, sin carga desde las piernas. "
        "Corrección: flexionar ligeramente siempre antes del impacto (split-step → carga). "
        "Drill: practicar el 'coil': flexión de rodillas con rotación de cadera antes de golpear.",
    ),

    # ── TRONCO ───────────────────────────────────────────────────────────────
    (
        "tronco_rango",
        "Tronco — inclinación lateral (trunk_tilt): rango óptimo 0–20° (Elliott et al., 2003). "
        "El tronco debe mantenerse prácticamente vertical durante el impacto para preservar "
        "el equilibrio y facilitar la rotación de cadera-hombro.",
    ),
    (
        "tronco_inclinado",
        "Tronco excesivamente inclinado (trunk_tilt > 20°): indica desequilibrio lateral, "
        "posible compensación por bola corta o mal posicionamiento. "
        "Puede derivar en lesiones lumbares a largo plazo. "
        "Corrección: mejorar el footwork para llegar cómodo a la bola. "
        "Drill: golpear con los pies en posición abierta, controlando el alineamiento lateral.",
    ),

    # ── CADERA (hip_separation / torso_rotation) ─────────────────────────────
    (
        "cadera_rango",
        "Rotación de caderas respecto a hombros (hip_separation): rango óptimo 20–60°. "
        "Una rotación de cadera adelantada respecto a los hombros (kinetic chain) es fundamental "
        "para la transferencia de potencia de piernas y tronco hacia el brazo y la raqueta "
        "(Elliott et al., 2003). La secuencia óptima: caderas → hombros → codo → muñeca.",
    ),
    (
        "cadera_poca_rotacion",
        "Poca rotación de caderas (hip_separation < 20°): caderas y hombros rotan al mismo tiempo, "
        "sin separación. La energía cinética no se transfiere eficientemente. El golpe pierde potencia. "
        "Corrección: iniciar la rotación de caderas ANTES que los hombros en el forward swing. "
        "Drill: 'hip-shoulder separation drill': sostener la raqueta con ambas manos y practicar "
        "la rotación de cadera mientras los hombros se retrasan intencionadamente.",
    ),
    (
        "cadera_exceso_rotacion",
        "Exceso de rotación de cadera (hip_separation > 60°): apertura excesiva de caderas, "
        "normalmente demasiado pronto (antes del impacto). Reduce el control direccional. "
        "Corrección: retrasar ligeramente la apertura de caderas, enfocarse en 'guardar' la rotación "
        "hasta el último instante antes del impacto.",
    ),

    # ── MUÑECA / VELOCIDAD ────────────────────────────────────────────────────
    (
        "muneca_rango",
        "Velocidad de muñeca en el impacto (wrist_speed): rango óptimo 200–600 °/s. "
        "Una aceleración progresiva del segmento distal (muñeca) en la fase de impacto "
        "es el indicador más directo de una cadena cinética bien ejecutada "
        "(Landlinger et al., 2012). Velocidades superiores a 300°/s se asocian con topspin efectivo.",
    ),
    (
        "muneca_lenta",
        "Muñeca lenta (wrist_speed < 200°/s): el segmento distal no acelera adecuadamente. "
        "Puede indicar: rigidez de muñeca, falta de relajación del antebrazo, o desconexión "
        "del giro de hombro. "
        "Corrección: trabajar el 'snap' de muñeca en el impacto soltando levemente el grip. "
        "Drill: golpear con una pelota de espuma para reducir el miedo al error y liberar la muñeca.",
    ),
    (
        "muneca_rapida",
        "Muñeca muy rápida (wrist_speed > 600°/s): aceleración excesiva puede indicar golpe "
        "armado exclusivamente con el antebrazo, sin apoyo de la cadena cinética completa. "
        "Riesgo de lesión por sobrecarga del codo. "
        "Corrección: distribuir la potencia desde las piernas y el tronco, no solo el brazo.",
    ),

    # ── CADENA CINÉTICA Y FASES ───────────────────────────────────────────────
    (
        "cadena_cinetica",
        "Cadena cinética del forehand: la secuencia óptima de activación es pies → rodillas → "
        "caderas → tronco → hombro → codo → muñeca → raqueta. "
        "Cada segmento proximal desacelera y transfiere energía al segmento distal siguiente. "
        "Un fallo en cualquier eslabón reduce la eficiencia global (Elliott et al., 2003).",
    ),
    (
        "fases_golpe",
        "Fases del golpe de derecha: (1) Preparación — giro de hombros, backswing, posicionamiento. "
        "(2) Carga — flexión de rodillas, coil de cadera, raqueta atrás. "
        "(3) Forward swing e impacto — extensión de piernas, rotación cadera→hombro, extensión de codo. "
        "(4) Follow-through — continuación del arco de raqueta por encima del hombro contrario.",
    ),
    (
        "tecnica_topspin",
        "Golpe de derecha con topspin: el brushing (rozamiento) de la pelota requiere que la "
        "raqueta suba de abajo-arriba en el impacto. Indicadores biomecánicos: ángulo de hombro "
        "ascendente (>90°), velocidad de muñeca elevada (>300°/s) y extensión de codo progresiva. "
        "El topspin aumenta el margen de red y permite una trayectoria de bola más profunda.",
    ),
    (
        "footwork",
        "Footwork y posicionamiento: llegar a la bola con los pies bien posicionados es "
        "condición necesaria para una buena biomecánica. Los defectos de ángulo de tronco o "
        "rodillas frecuentemente tienen origen en un posicionamiento tardío o impreciso.",
    ),

    # ── ERRORES MÁS COMUNES ───────────────────────────────────────────────────
    (
        "errores_comunes",
        "Errores más frecuentes en el forehand amateur: (1) muñeca bloqueada (wrist_speed bajo), "
        "(2) falta de rotación de caderas (hip_separation bajo), "
        "(3) hombro demasiado bajo por mal posicionamiento, "
        "(4) piernas rectas sin carga (knee_angle alto), "
        "(5) apertura prematura de caderas antes del impacto.",
    ),
    (
        "nivel_principiante",
        "Jugador principiante: los errores más habituales son piernas rectas, tronco inclinado "
        "y muñeca bloqueada. Priorizar el footwork y la postura básica antes de trabajar la cadena cinética.",
    ),
    (
        "nivel_intermedio",
        "Jugador de nivel intermedio: suele tener buena postura pero le falta separación cadera-hombro "
        "y velocidad de muñeca. Trabajar el coil (carga) y el release progresivo de la cadena cinética.",
    ),
    (
        "nivel_avanzado",
        "Jugador avanzado: optimizar la sincronización de la cadena cinética completa. "
        "Pequeñas mejoras en el timing de apertura de cadera y aceleración de muñeca generan "
        "incrementos notables en la potencia y el topspin del golpe.",
    ),
]


class RAGService:

    def __init__(self):
        try:
            import chromadb
            # EphemeralClient es la API actual (chromadb >= 0.4); Client() está deprecado
            try:
                self._client = chromadb.EphemeralClient()
            except AttributeError:
                self._client = chromadb.Client()  # fallback para versiones antiguas

            self._collection = self._client.create_collection("biomechanics")
            self._collection.add(
                ids=[doc_id for doc_id, _ in BIOMECHANICAL_DOCS],
                documents=[text for _, text in BIOMECHANICAL_DOCS],
            )
            self._available = True
        except Exception as e:
            print(f"RAGService: ChromaDB no disponible ({e}). Usando fallback.")
            self._available = False

    def retrieve(self, query: str, n_results: int = 4) -> str:
        if not self._available:
            return ""
        try:
            n = min(n_results, len(BIOMECHANICAL_DOCS))
            results = self._collection.query(query_texts=[query], n_results=n)
            docs = results.get("documents", [[]])[0]
            return "\n".join(docs)
        except Exception:
            return ""
