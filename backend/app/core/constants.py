# Rangos óptimos de referencia (Elliott et al., 2003; Landlinger et al., 2012)
REFERENCE_RANGES = {
    "elbow_angle":    (100, 160),
    "shoulder_angle": (60,  120),
    "knee_angle":     (130, 170),
    "trunk_tilt":     (0,   20),
}

DIMENSION_WEIGHTS = {
    "elbow_angle":    0.30,
    "shoulder_angle": 0.25,
    "knee_angle":     0.25,
    "trunk_tilt":     0.20,
}

FEEDBACK_LABELS = {
    "elbow_angle":    "Extensión de codo",
    "shoulder_angle": "Posición de hombro",
    "knee_angle":     "Flexión de rodillas",
    "trunk_tilt":     "Inclinación de tronco",
}
