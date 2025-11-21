# planets.py
PLANET_GRAVITY = {
    "Mercury": 0.38,
    "Venus": 0.91,
    "Earth": 1.00,
    "Moon": 0.165,
    "Mars": 0.38,
    "Jupiter": 2.34,
    "Saturn": 1.06,
    "Uranus": 0.92,
    "Neptune": 1.19,
}

def weights_on_planets(earth_weight_kg: float):
    return {
        planet: round(earth_weight_kg * ratio, 1)
        for planet, ratio in PLANET_GRAVITY.items()
    }
