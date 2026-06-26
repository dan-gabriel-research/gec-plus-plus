"""
GEC++ Agent — Grounded Emergent Consciousness prototype

Four architectural layers approximating the GEC++ components:
  TCI  — Temporal Continuity: persistent state across sessions (not retrieval)
  CSMI — Causal Self-Modeling: self-assessment before every response
  EI   — Embodied Integration: serialized tool loops with forced observation
  AVI  — Affective Valence: consistency enforcement as functional stakes
"""

from .agent import GECAgent

__all__ = ["GECAgent"]
