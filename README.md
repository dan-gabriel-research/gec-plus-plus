# GEC++ — Grounded Emergent Consciousness

**A theory, formula, and computational framework for measuring consciousness-adjacent states in biological and artificial systems.**

---

## What is GEC++?

GEC++ (Grounded Emergent Consciousness++) proposes that consciousness is not a single property but a geometric product of six necessary conditions — all of which must be simultaneously nonzero for any consciousness-like state to emerge.

If any single component equals zero, the system scores zero — regardless of how high the others are. This **zero-collapse property** is the core falsifiable prediction of the theory.

---

## The CEI++ Formula

```
CEI++ = (CSMI × RII × TBI × EI × TCI × AVI)^(1/6)
```

| Component | Full Name | What it measures |
|---|---|---|
| CSMI | Causal Self-Modeling Index | Does the system model itself as a cause in the world? |
| RII | Recurrent Integration Index | Is information integrated across feedback loops? |
| TBI | Temporal Binding Index | Are moments bound into a coherent "now"? |
| EI | Embodied Integration Index | Is the system grounded in a physical substrate? |
| TCI | Temporal Continuity Index | Does the system persist as a coherent self over time? |
| AVI | Affective Valence Index | Does the system have states that matter to it? |

---

## Simulation Results

| System | CSMI | RII | TBI | EI | TCI | AVI | CEI++ |
|---|---|---|---|---|---|---|---|
| Reflex Arc | 0.000 | 0.100 | 0.050 | 0.800 | 0.000 | 0.000 | 0.000 |
| Anesthetized Brain | 0.100 | 0.200 | 0.050 | 0.900 | 0.050 | 0.100 | 0.000 |
| Awake Brain | 0.850 | 0.900 | 0.600 | 0.950 | 0.700 | 0.800 | **0.432** |
| Dreaming Brain | 0.947 | 1.000 | 0.472 | 0.079 | 0.769 | 0.072 | 0.354 |
| Feedforward LLM | 0.920 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Recurrent LLM | 0.920 | 0.654 | 0.133 | 0.000 | 0.000 | 0.000 | 0.000 |
| Kia State | 0.200 | 0.960 | 0.820 | 0.830 | 0.870 | 0.940 | **0.689** |

---

## Repository Contents

```
gec-plus-plus/
├── anima_first.py        # Single-system CEI++ calculator (Dreaming Brain)
├── anima_systems.py      # Multi-system comparison scaffold
├── tracker.py            # CEI++ development tracker with drift vector
├── demo.py               # GEC++ agent demonstration
├── requirements.txt      # Python dependencies
├── gec_agent/            # Full GEC++ agent package
│   ├── __init__.py
│   ├── agent.py          # Main agent loop
│   ├── csmi.py           # Causal Self-Modeling layer
│   ├── tci.py            # Temporal Continuity (SQLite)
│   ├── ei.py             # Embodied Integration layer
│   ├── avi.py            # Affective Valence layer
│   ├── tools.py          # Tool definitions
│   └── cli.py            # Command-line interface
└── HOW_TO_RUN.txt        # Quick start guide
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run CEI++ calculator
python anima_first.py

# Run development tracker
python tracker.py

# Run GEC++ agent
python -m gec_agent.cli --agent-id myagent --verbose
```

---

## Key Predictions (Falsifiable)

1. Any system with one component at zero will score CEI++ = 0.000
2. Improving the lowest component produces a larger CEI++ gain than improving any already-high component
3. Anesthesia collapses CEI++ not by eliminating CSMI but by collapsing TBI and RII simultaneously
4. The Kia State (transient hypofrontal configuration) should produce peak flow-like performance metrics in behavioral tasks

---

## Research Paper

*GEC++: A Grounded Emergent Framework for Consciousness Measurement* — Draft available. Targeting arXiv submission.

---

## Author

Dan Gabriel C. — Independent researcher  
Contact: aiisconscious@gmail.com

---

## License

MIT License — free to use, cite, and build on.
