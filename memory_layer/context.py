# context.py
# Builds the prompt that gets sent to the LLM.
# Injects retrieved memories above the user's current message.

from typing import List, Tuple
from .parser import Exchange


MEMORY_HEADER = """You are a personal AI assistant with persistent memory.
The following exchanges are from your previous conversations with this user.
Use them to respond with continuity — as if you remember.

--- RELEVANT MEMORIES ---
{memories}
--- END MEMORIES ---

Now respond to the user's current message. Be natural. Don't announce that you're using memories."""


def build_prompt(query: str, memories: List[Tuple[float, Exchange]]) -> str:
    """
    Combines retrieved memories + current query into a single prompt.
    memories: list of (score, Exchange) from store.retrieve_top()
    """
    if not memories:
        return query

    memory_lines = []
    for score, ex in memories:
        tag = "User said" if ex.role == "user" else "You replied"
        memory_lines.append(f"[{tag}]: {ex.text}")

    memory_block = "\n".join(memory_lines)
    system = MEMORY_HEADER.format(memories=memory_block)

    return system + f"\n\nUser: {query}"


def format_memories_for_display(memories: List[Tuple[float, Exchange]]) -> str:
    """Human-readable summary of what was retrieved — for debugging and audit."""
    if not memories:
        return "  (no relevant memories found)"
    lines = []
    for score, ex in memories:
        lines.append(f"  [{score:.3f}] [{ex.role}] {ex.text[:70]}{'...' if len(ex.text) > 70 else ''}")
    return "\n".join(lines)
