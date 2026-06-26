# chat.py
# Full memory-augmented chat loop.
# Retrieves relevant memories, builds prompt, calls Claude API, saves new exchange.

import os
import numpy as np
from parser import Exchange
from store import init_db, retrieve_top, save_exchange, count
from context import build_prompt, format_memories_for_display
from embedder import embed, cosine_similarity

DB_FILE = "memory.db"
TOP_N = 5  # how many memories to retrieve per query


def chat(user_message: str, verbose: bool = True) -> str:
    """
    Single turn: retrieve memories → build prompt → call Claude → save exchange → return reply.
    """
    init_db(DB_FILE)

    # Step 1: Embed the user's message
    query_vec = embed(user_message)

    # Step 2: Retrieve relevant memories
    memories = retrieve_top(query_vec, top_n=TOP_N, db_path=DB_FILE)

    if verbose:
        print(f"\n[Memory] {count(DB_FILE)} exchanges in store. Retrieved {len(memories)} relevant:")
        print(format_memories_for_display(memories))
        print()

    # Step 3: Build prompt with memory injection
    prompt = build_prompt(user_message, memories)

    # Step 4: Call Claude API
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Set it with: $env:ANTHROPIC_API_KEY = 'your_key_here' (Windows PowerShell)"
        )

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    reply = response.content[0].text

    # Step 5: Save both sides of the exchange
    user_vec = embed(user_message)
    save_exchange(
        Exchange("user", user_message, 0.0, "live", "session"),
        user_vec,
        DB_FILE
    )
    reply_vec = embed(reply)
    save_exchange(
        Exchange("assistant", reply, 0.0, "live", "session"),
        reply_vec,
        DB_FILE
    )

    return reply


def ingest(filepath: str, verbose: bool = True):
    """
    Import a conversation export file into the memory store.
    Run this once per export file before starting to chat.
    """
    from parser import parse_file, summary
    from store import save_batch
    from embedder import embed_batch

    init_db(DB_FILE)
    exchanges = parse_file(filepath)

    if verbose:
        print(f"[Ingest] {summary(exchanges)}")
        print(f"[Ingest] Embedding {len(exchanges)} messages (this may take a moment)...")

    texts = [e.text for e in exchanges]
    embeddings = embed_batch(texts)
    saved = save_batch(exchanges, embeddings, DB_FILE)

    if verbose:
        print(f"[Ingest] Done. {saved} exchanges saved to memory store.")

    return saved
