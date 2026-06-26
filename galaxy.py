"""
galaxy.py  –  Procedural galaxy generation for Space Empire Simulator
"""

import random
from planet import Planet, generate_planets

SECTOR_SIZE = 2000

# Star name syllables for procedural names
_PRE  = ["Al", "Vel", "Tor", "Zan", "Kep", "Mir", "Sol", "Aur", "Cyx", "Dra",
          "Eln", "Fax", "Gal", "Hyd", "Ixo", "Jor", "Kun", "Lyr", "Mab", "Nox"]
_MID  = ["an", "en", "or", "ix", "ar", "el", "on", "ax", "ur", "in"]
_SUF  = ["is", "ax", "on", "ar", "ix", "us", "ia", "el", "or", "ex"]

_STAR_COLORS = [
    (255, 255, 200),   # white-yellow  (common)
    (255, 220, 150),   # orange        (common)
    (255, 180, 100),   # deep orange   (uncommon)
    (150, 180, 255),   # blue-white    (uncommon)
    (255, 100,  80),   # red giant     (rare)
    (200, 255, 200),   # pale green    (rare)
    (255, 255, 255),   # pure white    (rare)
]
_STAR_COLOR_WEIGHTS = [35, 25, 15, 12, 7, 4, 2]

_NEBULA_CHANCE = 0.08    # probability a star is inside a "nebula zone"


def _star_name(rng):
    return rng.choice(_PRE) + rng.choice(_MID) + rng.choice(_SUF)


def generate_sector(sector_x, sector_y):
    """
    Return a list of star dicts for this sector.
    Uses a seeded RNG so the same sector always produces identical results.
    """
    rng = random.Random(f"{sector_x},{sector_y}")

    stars = []
    count = rng.randint(40, 60)

    for i in range(count):
        num_planets = rng.randint(1, 8)
        planets = []
        for _ in range(num_planets):
            p = Planet()
            # re-roll type with the sector rng for determinism
            ptype = rng.choices(
                list(__import__("planet").PLANET_TYPES.keys()),
                weights=[30, 20, 15, 12, 10, 8, 5, 5, 2],
                k=1
            )[0]
            p.type  = ptype
            p._base = __import__("planet").PLANET_TYPES[ptype]
            planets.append(p)

        star_color = rng.choices(_STAR_COLORS, weights=_STAR_COLOR_WEIGHTS, k=1)[0]
        # slight random tint
        star_color = tuple(min(255, max(60, c + rng.randint(-20, 20))) for c in star_color)

        in_nebula = rng.random() < _NEBULA_CHANCE

        stars.append({
            "x":         sector_x * SECTOR_SIZE + rng.randint(50, SECTOR_SIZE - 50),
            "y":         sector_y * SECTOR_SIZE + rng.randint(50, SECTOR_SIZE - 50),
            "size":      rng.randint(2, 6),
            "name":      _star_name(rng),
            "owner":     None,
            "planets":   planets,
            "color":     star_color,
            "in_nebula": in_nebula,
            # pre-computed total planet yields (updated when buildings change)
            "_yield_cache": None,
        })

    return stars


def star_total_yields(star):
    """Sum all planet yields for a star system."""
    totals = {"credits": 0, "minerals": 0, "science": 0}
    for p in star["planets"]:
        y = p.total_yields()
        for k in totals:
            totals[k] += y[k]
    return totals


def find_nearest_unclaimed(star, loaded_sectors, max_dist=1200):
    """Return the nearest unclaimed star within max_dist, or None."""
    best      = None
    best_dist = max_dist
    for sector in loaded_sectors.values():
        for s in sector:
            if s["owner"] is not None or s is star:
                continue
            dx = s["x"] - star["x"]
            dy = s["y"] - star["y"]
            d  = (dx*dx + dy*dy) ** 0.5
            if d < best_dist:
                best_dist = d
                best      = s
    return best


def stars_in_range(star, loaded_sectors, radius):
    """Yield all stars within radius of star."""
    for sector in loaded_sectors.values():
        for s in sector:
            if s is star:
                continue
            dx = s["x"] - star["x"]
            dy = s["y"] - star["y"]
            if (dx*dx + dy*dy) ** 0.5 <= radius:
                yield s