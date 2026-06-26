"""
empire.py  –  Empire logic for Space Empire Simulator
"""

import random
from planet import BUILDINGS

# ── TECH TREE ─────────────────────────────────────────────────────────────────
TECHNOLOGIES = {
    # Tier 1
    "Basic Propulsion":    {"cost": 50,  "tier": 1, "desc": "Fleets move 25% faster",           "requires": []},
    "Mining Techniques":   {"cost": 60,  "tier": 1, "desc": "+2 minerals from all planets",      "requires": []},
    "Trade Networks":      {"cost": 60,  "tier": 1, "desc": "+2 credits from all planets",       "requires": []},
    "Basic Shields":       {"cost": 70,  "tier": 1, "desc": "Fleets +10 HP in combat",           "requires": []},
    # Tier 2
    "Advanced Propulsion": {"cost": 150, "tier": 2, "desc": "Fleets move 50% faster total",     "requires": ["Basic Propulsion"]},
    "Deep Core Mining":    {"cost": 180, "tier": 2, "desc": "+5 minerals from all planets",      "requires": ["Mining Techniques"]},
    "Galactic Commerce":   {"cost": 180, "tier": 2, "desc": "+5 credits from all planets",       "requires": ["Trade Networks"]},
    "Plasma Weapons":      {"cost": 200, "tier": 2, "desc": "Fleets deal +20 combat damage",     "requires": ["Basic Shields"]},
    "Colonization Tech":   {"cost": 120, "tier": 2, "desc": "Colonize without fleet present",    "requires": ["Basic Propulsion"]},
    # Tier 3
    "Warp Drive":          {"cost": 400, "tier": 3, "desc": "Instant sector travel",             "requires": ["Advanced Propulsion"]},
    "Terraforming":        {"cost": 350, "tier": 3, "desc": "Convert any planet to Terran",      "requires": ["Deep Core Mining", "Colonization Tech"]},
    "Mega Structures":     {"cost": 500, "tier": 3, "desc": "Unlock Orbital Platform building",  "requires": ["Galactic Commerce", "Deep Core Mining"]},
    "Death Fleet":         {"cost": 450, "tier": 3, "desc": "Fleets deal x2 combat damage",     "requires": ["Plasma Weapons", "Advanced Propulsion"]},
    "AI Governance":       {"cost": 300, "tier": 3, "desc": "+20% all resource yields",          "requires": ["Galactic Commerce", "Deep Core Mining"]},
}

# ── DIPLOMACY STATES ──────────────────────────────────────────────────────────
DIPLO_NEUTRAL  = "Neutral"
DIPLO_ALLY     = "Allied"
DIPLO_WAR      = "War"
DIPLO_TRADE    = "Trade Pact"
DIPLO_PEACE    = "Peace Treaty"

# ── FLEET SPEEDS ─────────────────────────────────────────────────────────────
BASE_FLEET_SPEED   = 2.0
BASE_FLEET_HP      = 100
BASE_FLEET_DAMAGE  = 30
FLEET_COST_CREDITS = 100
FLEET_COST_MINERALS= 80


class Empire:
    def __init__(self, name, color, is_ai=False):
        self.name   = name
        self.color  = color
        self.is_ai  = is_ai

        self.systems  = []      # list of star dicts
        self.credits  = 1000
        self.minerals = 500
        self.science  = 0

        # Tech
        self.researched   = set()
        self.research_queue = None   # name of tech being researched
        self.research_progress = 0

        # Diplomacy: {empire_name: status_string}
        self.diplomacy = {}

        # War tracking
        self.at_war_with = set()   # set of empire names

        # AI personality
        self.ai_personality = random.choice(["expansionist", "militarist", "scientist"])
        self.ai_aggression  = random.uniform(0.2, 0.9)

        # Yield bonuses from tech
        self._mineral_bonus = 0
        self._credit_bonus  = 0
        self._yield_mult    = 1.0

    # ── RESOURCE UPDATES ──────────────────────────────────────────────────────
    def update_resources(self):
        for system in self.systems:
            for planet in system["planets"]:
                y = planet.total_yields()
                self.credits  += int((y["credits"]  + self._credit_bonus)  * self._yield_mult)
                self.minerals += int((y["minerals"] + self._mineral_bonus) * self._yield_mult)
                self.science  += int(y["science"] * self._yield_mult)
                planet.tick_population()

        # Research progress
        if self.research_queue:
            tech = TECHNOLOGIES.get(self.research_queue)
            if tech:
                self.research_progress += 1
                if self.research_progress >= tech["cost"]:
                    self._complete_research(self.research_queue)
                    self.research_queue    = None
                    self.research_progress = 0

    def _complete_research(self, tech_name):
        self.researched.add(tech_name)
        # Apply immediate effects
        if tech_name == "Mining Techniques":   self._mineral_bonus += 2
        if tech_name == "Deep Core Mining":    self._mineral_bonus += 5
        if tech_name == "Trade Networks":      self._credit_bonus  += 2
        if tech_name == "Galactic Commerce":   self._credit_bonus  += 5
        if tech_name == "AI Governance":       self._yield_mult    *= 1.2

    def can_research(self, tech_name):
        if tech_name in self.researched:
            return False, "Already researched"
        tech = TECHNOLOGIES.get(tech_name)
        if not tech:
            return False, "Unknown tech"
        for req in tech["requires"]:
            if req not in self.researched:
                return False, f"Requires: {req}"
        return True, "OK"

    def start_research(self, tech_name):
        ok, reason = self.can_research(tech_name)
        if ok:
            self.research_queue    = tech_name
            self.research_progress = 0
        return ok, reason

    # ── FLEET SPEED MULTIPLIER ────────────────────────────────────────────────
    def fleet_speed(self):
        spd = BASE_FLEET_SPEED
        if "Basic Propulsion"    in self.researched: spd *= 1.25
        if "Advanced Propulsion" in self.researched: spd *= 1.25   # stacks → 1.5x total
        if "Warp Drive"          in self.researched: spd *= 3.0
        return spd

    def fleet_hp(self):
        hp = BASE_FLEET_HP
        if "Basic Shields" in self.researched: hp += 10
        return hp

    def fleet_damage(self):
        dmg = BASE_FLEET_DAMAGE
        if "Plasma Weapons" in self.researched: dmg += 20
        if "Death Fleet"    in self.researched: dmg *= 2
        return dmg

    # ── DIPLOMACY ─────────────────────────────────────────────────────────────
    def get_relation(self, other_name):
        return self.diplomacy.get(other_name, DIPLO_NEUTRAL)

    def set_relation(self, other_name, status):
        self.diplomacy[other_name] = status
        if status == DIPLO_WAR:
            self.at_war_with.add(other_name)
        elif other_name in self.at_war_with:
            self.at_war_with.discard(other_name)

    def declare_war(self, other):
        self.set_relation(other.name, DIPLO_WAR)
        other.set_relation(self.name, DIPLO_WAR)

    def make_peace(self, other):
        self.set_relation(other.name, DIPLO_PEACE)
        other.set_relation(self.name, DIPLO_PEACE)

    def propose_trade(self, other):
        self.set_relation(other.name, DIPLO_TRADE)
        other.set_relation(self.name, DIPLO_TRADE)

    def propose_alliance(self, other):
        self.set_relation(other.name, DIPLO_ALLY)
        other.set_relation(self.name, DIPLO_ALLY)

    # ── COLONIZE / BUILD ──────────────────────────────────────────────────────
    def colonize_star(self, star):
        """Colonize an unclaimed star, colonizing its first planet."""
        star["owner"] = self
        self.systems.append(star)
        if star["planets"]:
            star["planets"][0].colonize()

    def build_on_planet(self, star, planet_idx, building_name):
        if star not in self.systems:
            return False, "Not your system"
        planets = star["planets"]
        if planet_idx < 0 or planet_idx >= len(planets):
            return False, "Invalid planet"
        planet = planets[planet_idx]
        return planet.build(building_name, self)

    def can_build_fleet(self):
        return (self.credits >= FLEET_COST_CREDITS and
                self.minerals >= FLEET_COST_MINERALS)

    def spend_fleet_cost(self):
        self.credits  -= FLEET_COST_CREDITS
        self.minerals -= FLEET_COST_MINERALS

    # ── COMBAT ────────────────────────────────────────────────────────────────
    def resolve_combat(self, attacker_fleet, defender_empire, defender_star):
        """
        Simple combat: fleet attacks a star.
        Returns (victory: bool, log: list[str])
        """
        log     = []
        atk_hp  = self.fleet_hp()
        atk_dmg = self.fleet_damage()

        def_hp  = sum(p.defense_value() for p in defender_star["planets"]) + 20
        def_dmg = 10 + len(defender_star["planets"]) * 2

        log.append(f"BATTLE: {attacker_fleet['owner'].name} attacks {defender_star['name']}")
        log.append(f"Attacker HP:{atk_hp} DMG:{atk_dmg} | Defender HP:{def_hp} DMG:{def_dmg}")

        round_n = 0
        while atk_hp > 0 and def_hp > 0 and round_n < 50:
            def_hp -= atk_dmg
            atk_hp -= def_dmg
            round_n += 1

        if atk_hp > 0:
            # attacker wins
            if defender_empire:
                defender_empire.systems = [s for s in defender_empire.systems
                                           if s is not defender_star]
            defender_star["owner"] = self
            self.systems.append(defender_star)
            log.append(f"VICTORY — {defender_star['name']} captured!")
            return True, log
        else:
            log.append(f"DEFEAT — {attacker_fleet['owner'].name} fleet destroyed!")
            return False, log

    # ── AI ────────────────────────────────────────────────────────────────────
    def ai_turn(self, loaded_sectors, all_empires, fleets):
        """Full AI decision for one tick (called every 2 seconds)."""
        if not self.systems:
            return

        # 1. Research something useful
        self._ai_research()

        # 2. Build buildings
        self._ai_build()

        # 3. Expand / fight
        if self.ai_personality == "expansionist":
            self._ai_expand(loaded_sectors)
        elif self.ai_personality == "militarist":
            self._ai_militarist(loaded_sectors, all_empires, fleets)
        else:
            self._ai_expand(loaded_sectors)   # scientist also expands but researches more

        # 4. Occasional diplomacy
        if random.random() < 0.05:
            self._ai_diplomacy(all_empires)

    def _ai_research(self):
        if self.research_queue:
            return
        candidates = []
        for name, tech in TECHNOLOGIES.items():
            ok, _ = self.can_research(name)
            if ok:
                candidates.append(name)
        if not candidates:
            return
        # Scientist prefers science techs, militarist prefers combat
        if self.ai_personality == "scientist":
            pref = [c for c in candidates if "Science" in c or "Commerce" in c or "AI" in c]
        elif self.ai_personality == "militarist":
            pref = [c for c in candidates if "Weapon" in c or "Shield" in c or "Fleet" in c or "Propulsion" in c]
        else:
            pref = []
        pool = pref if pref else candidates
        self.start_research(random.choice(pool))

    def _ai_build(self):
        for star in self.systems:
            for planet in star["planets"]:
                if not planet.colonized:
                    planet.colonize()
                    continue
                # Try to build something affordable
                for bname, bdata in BUILDINGS.items():
                    if bname in planet.buildings:
                        continue
                    ok, _ = planet.can_build(bname)
                    if not ok:
                        continue
                    if (self.credits  >= bdata["cost_credits"]  * 1.5 and
                        self.minerals >= bdata["cost_minerals"]  * 1.5):
                        planet.build(bname, self)
                        break   # one build per planet per tick

    def _ai_expand(self, loaded_sectors):
        if not self.systems:
            return
        nearby = []
        for owned in self.systems:
            for sector in loaded_sectors.values():
                for star in sector:
                    if star["owner"] is not None:
                        continue
                    dx = star["x"] - owned["x"]
                    dy = star["y"] - owned["y"]
                    if (dx*dx + dy*dy) ** 0.5 < 1000:
                        nearby.append(star)
        if nearby and self.minerals >= 50:
            target = random.choice(nearby)
            self.colonize_star(target)
            self.minerals -= 50

    def _ai_militarist(self, loaded_sectors, all_empires, fleets):
        # First expand, then potentially attack
        self._ai_expand(loaded_sectors)

        if random.random() > self.ai_aggression:
            return

        # Find enemy systems nearby
        enemies = [e for e in all_empires
                   if e is not self and self.get_relation(e.name) != DIPLO_ALLY]
        if not enemies:
            return
        target_empire = random.choice(enemies)
        if not target_empire.systems:
            return
        target_star = random.choice(target_empire.systems)
        # Declare war and create attack fleet
        if self.get_relation(target_empire.name) != DIPLO_WAR:
            self.declare_war(target_empire)
        if self.can_build_fleet():
            self.spend_fleet_cost()
            src = random.choice(self.systems)
            fleets.append({
                "x":        src["x"],
                "y":        src["y"],
                "target_x": target_star["x"],
                "target_y": target_star["y"],
                "target_star": target_star,
                "owner":    self,
                "hp":       self.fleet_hp(),
                "damage":   self.fleet_damage(),
                "speed":    self.fleet_speed(),
                "combat_target": target_empire,
            })

    def _ai_diplomacy(self, all_empires):
        others = [e for e in all_empires if e is not self]
        if not others:
            return
        other = random.choice(others)
        rel   = self.get_relation(other.name)
        # Small chance to propose trade or peace
        if rel == DIPLO_NEUTRAL and random.random() < 0.4:
            self.propose_trade(other)
        elif rel == DIPLO_WAR and random.random() < 0.15:
            self.make_peace(other)

    # ── LEGACY COMPAT ─────────────────────────────────────────────────────────
    def ai_expand(self, loaded_sectors):
        """Kept for backward-compat with old main.py call."""
        self._ai_expand(loaded_sectors)