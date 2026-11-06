# Roadmap

What the model does not do yet, ordered by how much it matters for the research question. The results these items come from are in [docs/results.md](docs/results.md).

## 1. Exclusion: alpha and beta males

The biggest gap. Any male can care for any nest he can reach, and his paternity follows his care, so nothing stops several males sharing one female. In rich habitats this makes males spread their care over several females, and polygynandry dominates, while Davies & Lundberg (1984) found that fed females end up with fewer males. In dunnocks, a dominant (alpha) male tries to keep others out, and whether he can depends on how large the female's range is.

Planned design, within the energy budget: part of a male's raising share for a nest becomes **guarding** that lowers rivals' delivered care (and paternity) there, with an effect that falls as the nest's foraging range grows. This uses the "negative contributions" idea in [docs/model.md](docs/model.md#2-core-abstraction-energy-as-the-single-currency). The test is whether rich habitats then shift toward monogamy and polygyny.

## 2. Information that matters

Changing λ over two orders of magnitude barely changes anything ([results §3](docs/results.md#3-cost-of-information)). A male already knows the nests he cares for, and the population average is a good enough guess for the rest. Ways to make information valuable, each a hypothesis to test:

- Let the population average stop being free (unobserved nests use a fixed, uninformed prior).
- Let females move or re-nest between rounds, so old observations go stale faster.
- Give the search share a second use for males: finding unguarded nests once exclusion (item 1) exists.

## 3. Female choices

- Females own one nest and have nothing to gain from search, yet their search share stays near its starting average. Social learning removes this small waste too slowly; a female's payoff depends far more on her habitat than on her search share.
- Females cannot yet accept or reject males, run two nests, or move. Each is a natural use of the allocation vector.
- An egg-laying cost for females is in the design but not in the code.

## 4. Paternity

Paternity equals the share of male care. This is the main simplifying assumption (see [docs/model.md §7](docs/model.md#7-payoffs-from-energy-to-fledglings)). A separate mating-access variable, as measured by Davies et al. (1992), would let care and paternity come apart.

## 5. Engineering

- Speed: one 60-round run takes about 5–8 s; the greedy allocator's look-ahead dominates. Vectorising it would allow larger populations.
- A small viewer that draws nests, ranges and care links on the map for one round.

## Possible extensions

- Individual differences in energy budget or fledgling curve.
- Risk aversion (variance penalty in the payoff).
- Kin-weighted payoffs.
- Other strategy types (learned or evolved rules) plugged in through `simulation/orchestrator.py`.
