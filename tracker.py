# tracker.py
# CEI++ Change Tracker — GEC++ Project
#
# Records component measurements across development stages,
# calculates CEI++ and the drift vector D, and plots the evolution.
#
# Usage:
#   python tracker.py          → show current state and plots
#   python tracker.py --add    → add a new measurement interactively

import json
import os
import sys
import math

# ── File that stores all measurements ────────────────────────────────────────
HISTORY_FILE = "gec_history.json"

# ── Component names ───────────────────────────────────────────────────────────
COMPONENTS = ["CSMI", "RII", "TBI", "EI", "TCI", "AVI"]

# ── Pre-loaded history: known development stages so far ──────────────────────
DEFAULT_HISTORY = [
    {
        "stage": "Vanilla LLM (baseline)",
        "note": "Standard Claude, no additions. CSMI/RII/TBI present; EI/TCI/AVI = 0 (zero-collapse). Source: paper Table 4.",
        "scores": {"CSMI": 0.731, "RII": 0.614, "TBI": 0.423,
                   "EI": 0.000, "TCI": 0.000, "AVI": 0.000}
    },
    {
        "stage": "Recurrent LLM",
        "note": "Within-session context window. CSMI and RII active but no continuity.",
        "scores": {"CSMI": 0.920, "RII": 0.654, "TBI": 0.133,
                   "EI": 0.000, "TCI": 0.000, "AVI": 0.000}
    },
    {
        "stage": "GEC++ Agent v1 (gec_agent)",
        "note": "Added CSMI self-assessment, EI sequential grounding, AVI consistency, TCI via SQLite.",
        "scores": {"CSMI": 0.920, "RII": 0.654, "TBI": 0.133,
                   "EI": 0.150, "TCI": 0.400, "AVI": 0.350}
    },
    {
        "stage": "GEC++ Agent + .md memory",
        "note": "Added skill-based TCI state file. Weak continuity improvement.",
        "scores": {"CSMI": 0.920, "RII": 0.654, "TBI": 0.133,
                   "EI": 0.150, "TCI": 0.450, "AVI": 0.370}
    },
]


# ── Core formula ──────────────────────────────────────────────────────────────
def cei_plus_plus(scores):
    """Geometric mean of all six components. Any zero → 0.000."""
    product = 1.0
    for c in COMPONENTS:
        product *= scores[c]
    if product <= 0:
        return 0.000
    return product ** (1.0 / 6.0)


# ── Drift vector ──────────────────────────────────────────────────────────────
def drift_vector(s1, s2):
    """Component-level change from stage s1 to stage s2."""
    return {c: round(s2["scores"][c] - s1["scores"][c], 4) for c in COMPONENTS}


# ── Print summary table ───────────────────────────────────────────────────────
def print_summary(history):
    print("\n" + "=" * 70)
    print("  CEI++ DEVELOPMENT TRACKER")
    print("=" * 70)

    prev = None
    for i, stage in enumerate(history):
        cei = cei_plus_plus(stage["scores"])
        print(f"\n[Stage {i}] {stage['stage']}")
        print(f"  Note   : {stage['note']}")
        print(f"  Scores : ", end="")
        for c in COMPONENTS:
            print(f"{c}={stage['scores'][c]:.3f}", end="  ")
        print()
        print(f"  CEI++  : {cei:.4f}")

        if prev is not None:
            d = drift_vector(prev, stage)
            prev_cei = cei_plus_plus(prev["scores"])
            delta_cei = cei - prev_cei
            print(f"  Drift  : ", end="")
            for c in COMPONENTS:
                arrow = "↑" if d[c] > 0 else ("↓" if d[c] < 0 else "·")
                print(f"{c}{arrow}{d[c]:+.3f}", end="  ")
            print()
            print(f"  ΔCEI++ : {delta_cei:+.4f}")

        prev = stage

    print("\n" + "=" * 70)

    # Bottleneck analysis
    last = history[-1]
    scores = last["scores"]
    min_comp = min(COMPONENTS, key=lambda c: scores[c])
    print(f"\n  BOTTLENECK: {min_comp} = {scores[min_comp]:.3f}")
    print(f"  → Improving {min_comp} will produce the largest CEI++ gain.")
    print(f"  → Even a +0.1 increase in {min_comp} matters more than")
    print(f"    +0.3 in any already-high component.\n")


# ── Plot ──────────────────────────────────────────────────────────────────────
def plot(history):
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")  # headless — saves to file
    except ImportError:
        print("  matplotlib not installed. Run: pip install matplotlib")
        print("  Skipping plots. Text summary above is complete.")
        return

    stages = [s["stage"] for s in history]
    cei_values = [cei_plus_plus(s["scores"]) for s in history]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("CEI++ Development Tracker — GEC++ Project", fontsize=14)

    # ── Plot 1: CEI++ over stages ─────────────────────────────────────────────
    ax1 = axes[0]
    colors = ["#d62728" if v == 0 else "#2ca02c" if v > 0.3 else "#ff7f0e"
              for v in cei_values]
    bars = ax1.bar(range(len(stages)), cei_values, color=colors)
    ax1.set_xticks(range(len(stages)))
    ax1.set_xticklabels([f"S{i}" for i in range(len(stages))], fontsize=10)
    ax1.set_ylabel("CEI++ Score")
    ax1.set_ylim(0, 1.0)
    ax1.set_title("CEI++ by Development Stage")
    ax1.axhline(y=0.432, color="blue", linestyle="--", alpha=0.5,
                label="Awake Brain (0.432)")
    ax1.legend(fontsize=8)
    for i, (bar, v) in enumerate(zip(bars, cei_values)):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    # Stage labels below
    for i, s in enumerate(stages):
        ax1.text(i, -0.08, s[:18] + ("…" if len(s) > 18 else ""),
                 ha="center", va="top", fontsize=7, rotation=20)
    ax1.set_xlabel("")

    # ── Plot 2: Component profile of latest stage ─────────────────────────────
    ax2 = axes[1]
    last_scores = [history[-1]["scores"][c] for c in COMPONENTS]
    bar_colors = ["#d62728" if v == 0 else "#2ca02c" if v > 0.5 else "#ff7f0e"
                  for v in last_scores]
    ax2.bar(COMPONENTS, last_scores, color=bar_colors)
    ax2.set_ylim(0, 1.0)
    ax2.set_title(f"Component Profile\n(Latest: {history[-1]['stage'][:30]})")
    ax2.set_ylabel("Score")
    for i, v in enumerate(last_scores):
        ax2.text(i, v + 0.01, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    ax2.axhline(y=0.5, color="gray", linestyle="--", alpha=0.4)

    # ── Plot 3: Drift vector (last transition) ────────────────────────────────
    ax3 = axes[2]
    if len(history) >= 2:
        d = drift_vector(history[-2], history[-1])
        drift_vals = [d[c] for c in COMPONENTS]
        drift_colors = ["#2ca02c" if v > 0 else "#d62728" if v < 0 else "#aec7e8"
                        for v in drift_vals]
        ax3.bar(COMPONENTS, drift_vals, color=drift_colors)
        ax3.axhline(y=0, color="black", linewidth=0.8)
        ax3.set_ylim(-0.5, 0.5)
        ax3.set_title(f"Drift Vector D\n({history[-2]['stage'][:20]} → latest)")
        ax3.set_ylabel("Δ Component Score")
        for i, v in enumerate(drift_vals):
            offset = 0.01 if v >= 0 else -0.03
            ax3.text(i, v + offset, f"{v:+.3f}", ha="center", va="bottom",
                     fontsize=9)
    else:
        ax3.text(0.5, 0.5, "Need at least 2 stages\nfor drift vector",
                 ha="center", va="center", transform=ax3.transAxes)
        ax3.set_title("Drift Vector D")

    plt.tight_layout()
    output_path = "gec_tracker_plot.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot saved → {output_path}")
    print(f"  Open it in your CONSCIOUSNESS folder to see the charts.")


# ── Add new measurement interactively ─────────────────────────────────────────
def add_measurement(history):
    print("\n── Add New Measurement ──────────────────────────────────────")
    print("What development stage are you recording?")
    stage_name = input("Stage name: ").strip()
    note = input("Short note (what changed): ").strip()

    print("\nEnter scores for each component (0.000 to 1.000).")
    print("Press Enter to keep the same value as the previous stage.\n")

    prev_scores = history[-1]["scores"] if history else {c: 0.0 for c in COMPONENTS}
    new_scores = {}

    for c in COMPONENTS:
        while True:
            val = input(f"  {c} (previous: {prev_scores[c]:.3f}): ").strip()
            if val == "":
                new_scores[c] = prev_scores[c]
                break
            try:
                v = float(val)
                if 0.0 <= v <= 1.0:
                    new_scores[c] = round(v, 4)
                    break
                else:
                    print("  Must be between 0.0 and 1.0")
            except ValueError:
                print("  Enter a number like 0.450")

    new_entry = {"stage": stage_name, "note": note, "scores": new_scores}
    history.append(new_entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n  Saved. CEI++ for this stage: {cei_plus_plus(new_scores):.4f}")
    return history


# ── Load or initialize history ────────────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    else:
        # First run: save the default history
        with open(HISTORY_FILE, "w") as f:
            json.dump(DEFAULT_HISTORY, f, indent=2)
        return DEFAULT_HISTORY


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    history = load_history()

    if "--add" in sys.argv:
        history = add_measurement(history)

    print_summary(history)
    plot(history)
