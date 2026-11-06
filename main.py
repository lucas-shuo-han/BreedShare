"""Run one BreedShare simulation and print how the mating system develops.

    python main.py
    python main.py --resource-level 0.9 --rounds 80
    python main.py --log          # also write every decision to breed_share_debug.log
"""
import argparse
import logging
from dataclasses import replace

from config.config import DEFAULT
from simulation.metrics import CATEGORIES
from simulation.run import run, steady_state


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rounds", type=int, default=DEFAULT.rounds)
    p.add_argument("--seed", type=int, default=DEFAULT.seed)
    p.add_argument("--resource-level", type=float, default=DEFAULT.resource_level)
    p.add_argument("--aggregation-level", type=float, default=DEFAULT.aggregation_level)
    p.add_argument("--search-efficiency", type=float, default=DEFAULT.search_efficiency, help="lambda")
    p.add_argument("--females", type=int, default=DEFAULT.n_females)
    p.add_argument("--males", type=int, default=DEFAULT.n_males)
    p.add_argument("--log", action="store_true", help="write decisions to breed_share_debug.log")
    args = p.parse_args()

    if args.log:
        logging.basicConfig(filename="breed_share_debug.log", filemode="w", level=logging.INFO,
                            format="%(message)s")

    config = replace(DEFAULT, rounds=args.rounds, seed=args.seed,
                     resource_level=args.resource_level, aggregation_level=args.aggregation_level,
                     search_efficiency=args.search_efficiency,
                     n_females=args.females, n_males=args.males)

    rows = run(config)

    short = {"unmated": "unmat", "monogamy": "mono", "polygyny": "pgyny",
             "polyandry": "pandry", "polygynandry": "pgnd"}
    header = "round  " + "  ".join(f"{short[c]:>6}" for c in CATEGORIES) + "  fledg/F  srch_M  srch_F"
    print(header)
    for r in rows:
        if r["round"] == 1 or r["round"] % 10 == 0:
            print(f"{int(r['round']):>5}  " + "  ".join(f"{r[c]:>6.2f}" for c in CATEGORIES)
                  + f"  {r['fledglings_per_female']:>7.2f}  {r['male_search']:>6.2f}  {r['female_search']:>6.2f}")

    s = steady_state(rows)
    print("\nMating system over the last 20 rounds (share of females):")
    for c in CATEGORIES:
        print(f"  {c:<13} {s[c]:6.1%}")


if __name__ == "__main__":
    main()
