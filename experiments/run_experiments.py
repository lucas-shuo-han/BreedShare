"""Reproduce every result in the README and docs/results.md.

    python experiments/run_experiments.py            # all experiments
    python experiments/run_experiments.py resource   # one experiment
    python experiments/run_experiments.py --replot   # redraw figures from results/*.csv

Raw numbers go to results/*.csv; figures to docs/figures/*.png.
Each point is the mean over seeds of the last 20 of 60 rounds.
"""
import csv
import os
import sys
from dataclasses import replace
from multiprocessing import Pool
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config.config import DEFAULT, Config
from simulation.metrics import CATEGORIES
from simulation.run import run, steady_state

SEEDS = list(range(1, 9))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "docs", "figures")

COLOURS = {"unmated": "#c9c9c9", "monogamy": "#4c78a8", "polygyny": "#f58518",
           "polyandry": "#54a24b", "polygynandry": "#b279a2"}


def _job(args: Tuple[Dict, int]) -> Dict[str, float]:
    overrides, seed = args
    row = steady_state(run(replace(DEFAULT, seed=seed, **overrides)))
    row.update(overrides)
    row["seed"] = seed
    return row


REPLOT = False


def _load(name: str) -> List[Dict[str, float]]:
    with open(os.path.join(RESULTS, f"{name}.csv"), newline="") as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def sweep(name: str, points: List[Dict]) -> List[Dict[str, float]]:
    if REPLOT:
        return _load(name)
    jobs = [(p, s) for p in points for s in SEEDS]
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        rows = pool.map(_job, jobs)
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, f"{name}.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def mean_by(rows: List[Dict], key: str, value: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    xs = sorted({r[key] for r in rows})
    means = np.array([np.mean([r[value] for r in rows if r[key] == x]) for x in xs])
    sems = np.array([np.std([r[value] for r in rows if r[key] == x], ddof=1) / np.sqrt(len(SEEDS))
                     for x in xs])
    return np.array(xs), means, sems


def stacked(ax, rows: List[Dict], key: str, log_x: bool = False) -> None:
    xs = None
    layers = []
    for c in CATEGORIES:
        xs, m, _ = mean_by(rows, key, c)
        layers.append(m)
    ax.stackplot(xs, layers, labels=CATEGORIES, colors=[COLOURS[c] for c in CATEGORIES], alpha=0.9)
    ax.set_ylim(0, 1)
    ax.set_xlim(xs[0], xs[-1])
    if log_x:
        ax.set_xscale("log")
    ax.set_ylabel("share of females")


def save(fig, name: str) -> None:
    os.makedirs(FIGURES, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, f"{name}.png"), dpi=150)
    plt.close(fig)


# --- experiments ------------------------------------------------------------------
def resource() -> None:
    rows = sweep("resource", [{"resource_level": x} for x in [0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0]])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    stacked(a, rows, "resource_level")
    a.set_xlabel("resource level (mean resource per cell)")
    a.set_title("Mating system vs. resource abundance")
    a.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    for value, label in [("males_per_female", "males per female"), ("females_per_male", "females per male")]:
        xs, m, se = mean_by(rows, "resource_level", value)
        b.errorbar(xs, m, yerr=se, marker="o", capsize=3, label=label)
    b.set_xlabel("resource level")
    b.set_title("Care partners (raising share ≥ 0.1)")
    b.legend()
    save(fig, "resource_sweep")


def search_efficiency() -> None:
    rows = sweep("search_efficiency", [{"search_efficiency": x} for x in [0.1, 0.3, 1.0, 3.0, 10.0, 30.0]])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    stacked(a, rows, "search_efficiency", log_x=True)
    a.set_xlabel("λ (search efficiency, log scale)")
    a.set_title("Mating system vs. cost of information")
    a.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    for value, label in [("male_search", "male search share"), ("female_search", "female search share")]:
        xs, m, se = mean_by(rows, "search_efficiency", value)
        b.errorbar(xs, m, yerr=se, marker="o", capsize=3, label=label)
    xs, m, se = mean_by(rows, "search_efficiency", "fledglings_per_female")
    b2 = b.twinx()
    b2.errorbar(xs, m, yerr=se, marker="s", color="grey", capsize=3, label="fledglings per female")
    b2.set_ylabel("fledglings per female")
    b.set_xscale("log")
    b.set_xlabel("λ")
    b.set_ylabel("search share")
    b.set_title("Search effort and output")
    b.set_ylim(0, 0.5)
    b2.set_ylim(0, 5)
    b.legend(loc="upper left", fontsize=8)
    b2.legend(loc="upper right", fontsize=8)
    save(fig, "search_efficiency_sweep")


def aggregation() -> None:
    aggs = [0.1, 0.3, 0.5, 0.7, 0.9]
    levels = [0.25, 0.5, 1.0]
    rows = sweep("aggregation", [{"aggregation_level": a, "resource_level": r} for a in aggs for r in levels])
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
    for ax, value in zip(axes, ["unmated", "polyandry", "polygynandry"]):
        grid = np.array([[np.mean([x[value] for x in rows
                                   if x["aggregation_level"] == a and x["resource_level"] == r])
                          for a in aggs] for r in levels])
        im = ax.imshow(grid, origin="lower", aspect="auto", vmin=0, vmax=max(0.3, grid.max()), cmap="viridis")
        ax.set_xticks(range(len(aggs)), [str(a) for a in aggs])
        ax.set_yticks(range(len(levels)), [str(r) for r in levels])
        ax.set_xlabel("aggregation level")
        ax.set_title(value)
        for i in range(len(levels)):
            for j in range(len(aggs)):
                bright = grid[i, j] > 0.6 * im.norm.vmax
                ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center",
                        color="black" if bright else "white", fontsize=8)
        fig.colorbar(im, ax=ax, fraction=0.046)
    axes[0].set_ylabel("resource level")
    save(fig, "aggregation_heatmap")


def _long_run(seed: int) -> List[Dict[str, float]]:
    return run(replace(DEFAULT, seed=seed, rounds=100))


def convergence() -> None:
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        runs = pool.map(_long_run, SEEDS)
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "convergence.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed"] + list(runs[0][0].keys()))
        writer.writeheader()
        for seed, rows in zip(SEEDS, runs):
            writer.writerows({"seed": seed, **r} for r in rows)

    fig, ax = plt.subplots(figsize=(8, 4))
    rounds = np.array([r["round"] for r in runs[0]])
    window = 5
    for c in CATEGORIES:
        series = np.array([[r[c] for r in rows] for rows in runs])          # seeds x rounds
        smooth = np.array([np.convolve(s, np.ones(window) / window, mode="valid") for s in series])
        x = rounds[window - 1:]
        m, sd = smooth.mean(axis=0), smooth.std(axis=0)
        ax.plot(x, m, color=COLOURS[c], label=c, lw=2)
        ax.fill_between(x, m - sd, m + sd, color=COLOURS[c], alpha=0.15)
    ax.axvspan(41, 60, color="black", alpha=0.06, label="window averaged in sweeps")
    ax.set_xlabel("round")
    ax.set_ylabel("share of females")
    ax.set_ylim(0, 0.6)
    ax.set_title(f"Default settings: mean of {len(SEEDS)} seeds (5-round moving average, ±1 sd across seeds)")
    ax.legend(fontsize=8, ncol=3, loc="upper right")
    save(fig, "convergence")


EXPERIMENTS = {"resource": resource, "search_efficiency": search_efficiency,
               "aggregation": aggregation, "convergence": convergence}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--replot"]
    REPLOT = "--replot" in sys.argv
    if REPLOT and not args:
        args = ["resource", "search_efficiency", "aggregation"]
    for name in args or EXPERIMENTS:
        print(f"running {name} ...", flush=True)
        EXPERIMENTS[name]()
    print("done")
