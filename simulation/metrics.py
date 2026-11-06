"""Reading mating systems off the allocation vectors.

Each female is classified by who cares for her nest(s), counting a male only
if his raising share there is at least `care_threshold`:

| Category      | Males caring for her | Do those males care for other females? |
|---------------|----------------------|----------------------------------------|
| unmated       | 0                    | –                                      |
| monogamy      | 1                    | no                                     |
| polygyny      | 1                    | yes                                    |
| polyandry     | 2+                   | none of them                           |
| polygynandry  | 2+                   | at least one                           |
"""
from collections import Counter
from typing import Dict

import numpy as np

from world.world_state import WorldState

CATEGORIES = ("unmated", "monogamy", "polygyny", "polyandry", "polygynandry")


def classify_females(world: WorldState) -> Dict[int, str]:
    thr = world.config.care_threshold
    # male -> set of females he cares for
    male_females: Dict[int, set] = {}
    for nest in world.nests.values():
        for m, s in nest.male_shares.items():
            if s >= thr:
                male_females.setdefault(m, set()).add(nest.female_id)

    result: Dict[int, str] = {}
    for agent in world.agents.values():
        if agent.sex != "female":
            continue
        males = {m for m, fs in male_females.items() if agent.id in fs}
        shared = any(len(male_females[m]) > 1 for m in males)
        if not males:
            result[agent.id] = "unmated"
        elif len(males) == 1:
            result[agent.id] = "polygyny" if shared else "monogamy"
        else:
            result[agent.id] = "polygynandry" if shared else "polyandry"
    return result


def summarize_round(world: WorldState) -> Dict[str, float]:
    classes = classify_females(world)
    counts = Counter(classes.values())
    n = max(len(classes), 1)
    females = [a for a in world.agents.values() if a.sex == "female"]
    males = [a for a in world.agents.values() if a.sex == "male"]
    thr = world.config.care_threshold
    row: Dict[str, float] = {c: counts.get(c, 0) / n for c in CATEGORIES}
    row.update({
        "female_search": float(np.mean([a.search_share for a in females])),
        "male_search": float(np.mean([a.search_share for a in males])),
        "fledglings_per_female": float(np.mean([a.fitness for a in females])),
        "females_per_male": float(np.mean([len(a.nests_cared_for(thr)) for a in males])),
        "males_per_female": float(np.mean(
            [sum(1 for s in world.nests[k].male_shares.values() if s >= thr)
             for a in females for k in a.nest_ids])),
    })
    return row
