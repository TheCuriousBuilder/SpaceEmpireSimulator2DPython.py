"""
planet.py  –  Planet & building system for Space Empire Simulator
"""

import random

# ── PLANET TYPE BASE YIELDS ───────────────────────────────────────────────────
PLANET_TYPES = {
    "Terran":    {"credits": 5, "minerals": 2, "science": 3, "color": (100, 180, 100), "desc": "Lush world, great for colonies"},
    "Desert":    {"credits": 2, "minerals": 5, "science": 1, "color": (210, 170,  80), "desc": "Rich mineral deposits"},
    "Ocean":     {"credits": 4, "minerals": 2, "science": 2, "color": ( 60, 120, 200), "desc": "Vast oceans, high trade value"},
    "Ice":       {"credits": 1, "minerals": 4, "science": 2, "color": (180, 220, 255), "desc": "Frozen but resource-rich"},
    "Volcanic":  {"credits": 1, "minerals": 6, "science": 0, "color": (200,  60,  20), "desc": "Extreme mining yields"},
    "Gas Giant": {"credits": 3, "minerals": 3, "science": 1, "color": (180, 140,  80), "desc": "Fuel and gas harvesting"},
    "Barren":    {"credits": 0, "minerals": 3, "science": 0, "color": ( 90,  90,  90), "desc": "Barely worth colonising"},
    "Jungle":    {"credits": 3, "minerals": 1, "science": 4, "color": ( 40, 140,  40), "desc": "Dense biosphere, science hub"},
    "Crystal":   {"credits": 6, "minerals": 1, "science": 5, "color": (180,  80, 255), "desc": "Exotic crystals, very rare"},
}

# ── BUILDINGS ─────────────────────────────────────────────────────────────────
BUILDINGS = {
    "Colony Hub":       {"cost_credits": 200, "cost_minerals": 100,
                         "yields": {"credits": 5, "minerals": 0,  "science": 0},
                         "desc": "Required to develop a planet",      "requires": None},
    "Mine":             {"cost_credits":  80, "cost_minerals":  50,
                         "yields": {"credits": 0, "minerals": 5,  "science": 0},
                         "desc": "+5 minerals per tick",              "requires": "Colony Hub"},
    "Trading Post":     {"cost_credits": 120, "cost_minerals":  40,
                         "yields": {"credits": 8, "minerals": 0,  "science": 0},
                         "desc": "+8 credits per tick",               "requires": "Colony Hub"},
    "Research Lab":     {"cost_credits": 150, "cost_minerals":  60,
                         "yields": {"credits": 0, "minerals": 0,  "science": 6},
                         "desc": "+6 science per tick",               "requires": "Colony Hub"},
    "Shipyard":         {"cost_credits": 300, "cost_minerals": 200,
                         "yields": {"credits": 0, "minerals": 0,  "science": 0},
                         "desc": "Allows fleet construction here",    "requires": "Colony Hub"},
    "Defense Grid":     {"cost_credits": 250, "cost_minerals": 150,
                         "yields": {"credits": 0, "minerals": 0,  "science": 0},
                         "desc": "+20 defense strength",              "requires": "Colony Hub"},
    "Advanced Mine":    {"cost_credits": 200, "cost_minerals": 120,
                         "yields": {"credits": 0, "minerals": 12, "science": 0},
                         "desc": "+12 minerals per tick",             "requires": "Mine"},
    "Stock Exchange":   {"cost_credits": 350, "cost_minerals":  80,
                         "yields": {"credits": 20, "minerals": 0, "science": 0},
                         "desc": "+20 credits per tick",              "requires": "Trading Post"},
    "University":       {"cost_credits": 300, "cost_minerals": 100,
                         "yields": {"credits": 0, "minerals": 0,  "science": 15},
                         "desc": "+15 science per tick",              "requires": "Research Lab"},
    "Orbital Platform": {"cost_credits": 500, "cost_minerals": 300,
                         "yields": {"credits": 10, "minerals": 5, "science": 5},
                         "desc": "Massive multi-yield station",       "requires": "Shipyard"},
}

# ── PLANET CLASS ──────────────────────────────────────────────────────────────
class Planet:
    def __init__(self, ptype=None, colonized=False):
        if ptype is None:
            weights = [30, 20, 15, 12, 10, 8, 5, 5, 2]   # rarity weights
            ptype = random.choices(list(PLANET_TYPES.keys()),
                                   weights=weights, k=1)[0]
        self.type        = ptype
        self.colonized   = colonized
        self.population  = 100 if colonized else 0
        self.buildings   = []           # list of building name strings
        self.defense     = 0
        self._base       = PLANET_TYPES[ptype]

    # ── YIELDS ────────────────────────────────────────────────────────────────
    @property
    def color(self):
        return self._base["color"]

    @property
    def desc(self):
        return self._base["desc"]

    def base_yields(self):
        """Raw yields from planet type (only if colonized)."""
        if not self.colonized:
            return {"credits": 0, "minerals": 0, "science": 0}
        return {
            "credits":  self._base["credits"],
            "minerals": self._base["minerals"],
            "science":  self._base["science"],
        }

    def building_yields(self):
        out = {"credits": 0, "minerals": 0, "science": 0}
        for bname in self.buildings:
            b = BUILDINGS.get(bname, {})
            for k, v in b.get("yields", {}).items():
                out[k] = out.get(k, 0) + v
        return out

    def total_yields(self):
        by = self.base_yields()
        bly = self.building_yields()
        return {k: by[k] + bly.get(k, 0) for k in by}

    def defense_value(self):
        base = 5 if self.colonized else 0
        if "Defense Grid" in self.buildings:
            base += 20
        if "Orbital Platform" in self.buildings:
            base += 10
        return base

    def has_shipyard(self):
        return "Shipyard" in self.buildings or "Orbital Platform" in self.buildings

    # ── ACTIONS ───────────────────────────────────────────────────────────────
    def colonize(self):
        self.colonized  = True
        self.population = 100
        if "Colony Hub" not in self.buildings:
            self.buildings.append("Colony Hub")

    def can_build(self, bname):
        if bname in self.buildings:
            return False, "Already built"
        b = BUILDINGS.get(bname)
        if b is None:
            return False, "Unknown building"
        req = b["requires"]
        if req and req not in self.buildings:
            return False, f"Requires {req}"
        if not self.colonized:
            return False, "Planet not colonized"
        return True, "OK"

    def build(self, bname, empire):
        ok, reason = self.can_build(bname)
        if not ok:
            return False, reason
        b = BUILDINGS[bname]
        if empire.credits < b["cost_credits"]:
            return False, "Not enough credits"
        if empire.minerals < b["cost_minerals"]:
            return False, "Not enough minerals"
        empire.credits  -= b["cost_credits"]
        empire.minerals -= b["cost_minerals"]
        self.buildings.append(bname)
        return True, f"{bname} built!"

    def tick_population(self):
        """Grow population slowly if colonized."""
        if self.colonized and self.population < 10_000:
            self.population = min(10_000, int(self.population * 1.002) + 1)

    # ── DICT COMPAT ───────────────────────────────────────────────────────────
    def to_dict(self):
        return {
            "type":       self.type,
            "colonized":  self.colonized,
            "population": self.population,
            "buildings":  list(self.buildings),
            "defense":    self.defense_value(),
            # legacy keys kept so main.py planet display still works
            "credits":    self._base["credits"],
            "minerals":   self._base["minerals"],
            "science":    self._base["science"],
        }

    def __repr__(self):
        return f"Planet({self.type}, col={self.colonized}, bldg={self.buildings})"


# ── HELPER: generate planets for a star ──────────────────────────────────────
def generate_planets(count=None):
    if count is None:
        count = random.randint(1, 8)
    return [Planet() for _ in range(count)]