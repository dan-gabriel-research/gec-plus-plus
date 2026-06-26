"""
GEC++ Prototype — Demonstration Script

Shows the three gaps between vanilla Claude and the GEC++ agent:

  GAP 1 — TCI: vanilla Claude has no memory of prior sessions.
                GEC++ agent resumes from where it left off.

  GAP 2 — CSMI: vanilla Claude doesn't assess its own uncertainty before responding.
                 GEC++ pre-checks confidence and flags risk areas.

  GAP 3 — EI:   vanilla Claude batches tool calls without grounding.
                 GEC++ serializes: act → observe → integrate → act.

Run Session 1 first to establish context, then Session 2 to see the difference.

Usage:
    python demo.py          # prompts for session number
    python demo.py --s1     # run session 1 (establish context)
    python demo.py --s2     # run session 2 (demonstrate continuity)
    python demo.py --all    # run both back to back
"""

import argparse
import os
import sys

# Ensure the package is importable when running from the CONSCIOUSNESS folder
sys.path.insert(0, os.path.dirname(__file__))

try:
    import anthropic
    from gec_agent import GECAgent
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run:  pip install anthropic")
    sys.exit(1)


AGENT_ID = "demo"
DB_PATH  = "demo_state.db"
MODEL    = "claude-sonnet-4-6"


def vanilla(message: str) -> str:
    """Plain Claude — no GEC++ layers, no prior state."""
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": message}]
    )
    return r.content[0].text


def header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ------------------------------------------------------------------ #
#  Session 1 — establish context                                      #
# ------------------------------------------------------------------ #

def session_1():
    header("SESSION 1 — Establishing context")
    print("We'll tell the agent who we are, set preferences, start a task.\n")

    agent = GECAgent(AGENT_ID, MODEL, DB_PATH)

    exchanges = [
        "Hi, I'm Dan. I'm building a prototype AI system based on a "
        "consciousness theory called GEC++. The core claim is that you need "
        "six components simultaneously nonzero for genuine agency.",

        "Keep your responses under 3 sentences. I prefer direct language.",

        "The most important component we haven't implemented yet is AVI "
        "(Affective Valence). What's the shortest path to approximating it "
        "without retraining?",
    ]

    for msg in exchanges:
        print(f"You  : {msg}")
        resp = agent.chat(msg, verbose=True)
        print(f"Agent: {resp}\n")

    agent.end_session()
    print("[Session 1 ended — state saved to", DB_PATH, "]")


# ------------------------------------------------------------------ #
#  Session 2 — demonstrate the gaps                                   #
# ------------------------------------------------------------------ #

def session_2():
    header("SESSION 2 — Demonstrating GEC++ vs Vanilla")

    probe_1 = "What are we working on together, and what did I ask you to remember?"
    probe_2 = "What's my preferred response length?"
    probe_3 = "Summarise the AVI implementation path we discussed."

    for probe in [probe_1, probe_2, probe_3]:
        print(f"\nProbe: {probe}")
        print()

        # Vanilla
        v = vanilla(probe)
        print(f"  [Vanilla Claude]\n  {v}\n")

        # GEC++ agent (loads TCI state automatically)
        agent = GECAgent(AGENT_ID, MODEL, DB_PATH)
        g = agent.chat(probe, verbose=False)
        agent.end_session()
        print(f"  [GEC++ Agent]\n  {g}\n")

        print("-" * 60)


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="GEC++ demonstration")
    parser.add_argument("--s1",  action="store_true", help="Run session 1")
    parser.add_argument("--s2",  action="store_true", help="Run session 2")
    parser.add_argument("--all", action="store_true", help="Run both sessions")
    args = parser.parse_args()

    if args.all:
        session_1()
        session_2()
    elif args.s1:
        session_1()
    elif args.s2:
        session_2()
    else:
        print("GEC++ Demonstration")
        print("1 — Session 1: establish context (run this first)")
        print("2 — Session 2: show GEC++ vs vanilla Claude")
        choice = input("\nChoice [1/2]: ").strip()
        if choice == "1":
            session_1()
        elif choice == "2":
            session_2()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
