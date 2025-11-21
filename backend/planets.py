# backend/planets.py

PLANET_FACTORS = {
    "Mercury": 0.38,
    "Venus":   0.91,
    "Earth":   1.00,
    "Mars":    0.38,
    "Jupiter": 2.53,
    "Saturn":  1.07,
}


def weights_on_planets(earth_weight_kg: float) -> dict:
    """
    Given Earth weight (kg), return dict of planet -> weight_kg.
    """
    return {
        planet: round(earth_weight_kg * factor, 2)
        for planet, factor in PLANET_FACTORS.items()
    }
