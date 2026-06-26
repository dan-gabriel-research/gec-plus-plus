"""
Command-line interface for the GEC++ agent.

Usage:
    python -m gec_agent.cli
    python -m gec_agent.cli --agent-id dan --verbose
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="GEC++ Agent — Grounded Emergent Consciousness prototype"
    )
    parser.add_argument(
        "--agent-id", default="default",
        help="Agent identity key (state persists under this ID)"
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Claude model string"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show GEC++ layer activity (CSMI scores, EI observations, AVI checks)"
    )
    parser.add_argument(
        "--db", default="gec_state.db",
        help="Path to SQLite state database"
    )
    args = parser.parse_args()

    # Import here so CLI startup is fast even if anthropic isn't installed
    try:
        from .agent import GECAgent
    except ImportError as e:
        print(f"Error: {e}")
        print("Run: pip install anthropic")
        sys.exit(1)

    print("\n=== GEC++ Agent ===")
    print(f"Agent ID : {args.agent_id}")
    print(f"Model    : {args.model}")
    print(f"Verbose  : {args.verbose}")
    print("Type 'exit' to end session and save state.\n")

    agent = GECAgent(args.agent_id, args.model, args.db)

    # Show loaded state
    state = agent.state
    n = state.get("session_count", 0)
    if n > 0:
        print(f"[TCI] Resuming from {n} prior session(s).")
        constraints = state.get("consistency_constraints", [])
        if constraints:
            print(f"[TCI] {len(constraints)} active commitments loaded.")
        print()
    else:
        print("[TCI] No prior state — starting fresh.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            agent.end_session()
            print("[TCI] State saved.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye", ":q"}:
            agent.end_session()
            summary = agent.session_summary
            print(f"\n[TCI] Session saved.")
            print(f"      Sessions total : {summary['session_count']}")
            print(f"      Constraints    : {summary['constraints']}")
            print(f"      Corrections    : {summary['corrections']}")
            break

        if args.verbose:
            print()

        response = agent.chat(user_input, verbose=args.verbose)

        if args.verbose:
            print()
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    main()
