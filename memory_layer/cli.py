# cli.py
# Command-line interface for the memory layer.
#
# Usage:
#   python cli.py --ingest conversations.json   → import a conversation export
#   python cli.py --chat                         → start chatting with memory
#   python cli.py --stats                        → show memory store stats

import argparse
import sys
from store import init_db, count


def main():
    parser = argparse.ArgumentParser(
        description="AI Memory Layer — powered by GEC++ TCI engine"
    )
    parser.add_argument("--ingest", metavar="FILE",
                        help="Import a conversation export file (ChatGPT, Claude, or .txt)")
    parser.add_argument("--chat", action="store_true",
                        help="Start interactive chat with memory")
    parser.add_argument("--stats", action="store_true",
                        help="Show memory store statistics")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress memory retrieval details")

    args = parser.parse_args()

    if args.ingest:
        from chat import ingest
        ingest(args.ingest, verbose=not args.quiet)

    elif args.stats:
        init_db()
        n = count()
        print(f"Memory store: {n} exchanges stored.")

    elif args.chat:
        from chat import chat
        print("=== AI Memory Layer ===")
        print("Your AI remembers your past conversations.")
        print("Type 'quit' to exit.\n")
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                break
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            if not user_input:
                continue
            try:
                reply = chat(user_input, verbose=not args.quiet)
                print(f"\nAssistant: {reply}\n")
            except EnvironmentError as e:
                print(f"\nError: {e}\n")
                sys.exit(1)
            except Exception as e:
                print(f"\nUnexpected error: {e}\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
