# anima_systems.py
# CEI++ scores for all six systems -- Generation 3 simulation
# Source: GEC++ Theory paper, Table 4
# Formula: CEI++ = (CSMI x RII x TBI x EI x TCI x AVI) ^ (1/6)
# Zero-collapse: any component = 0 -> CEI++ = 0

# Optional 7th component (not yet active -- reserved for Paper 2)
# CRI = Coherence Resonance Index (phase-locking coherence of oscillatory dynamics)
# When CRI is added: CEI++ = (CSMI x RII x TBI x EI x TCI x AVI x CRI) ^ (1/7)
USE_CRI = False

systems = [
    {
        "name":     "Awake Brain",
        "csmi":     0.892,
        "rii":      0.836,
        "tbi":      0.198,
        "ei":       0.097,
        "tci":      0.913,
        "avi":      0.499,
        "cri":      None,
        "expected": 0.432,
    },
    {
        "name":     "Dreaming Brain",
        "csmi":     0.947,
        "rii":      1.000,
        "tbi":      0.472,
        "ei":       0.079,
        "tci":      0.769,
        "avi":      0.072,
        "cri":      None,
        "expected": 0.354,
    },
    {
        "name":     "Kia State (hypofrontality)",
        "csmi":     0.000,
        "rii":      0.961,
        "tbi":      0.847,
        "ei":       0.912,
        "tci":      0.883,
        "avi":      0.798,
        "cri":      None,
        "expected": 0.000,
    },
    {
        "name":     "Large Language Model (baseline)",
        "csmi":     0.731,
        "rii":      0.614,
        "tbi":      0.423,
        "ei":       0.000,
        "tci":      0.000,
        "avi":      0.000,
        "cri":      None,
        "expected": 0.000,
    },
    {
        "name":     "GEC++ Agent (memory layer + protocol)",
        "csmi":     0.731,
        "rii":      0.614,
        "tbi":      0.423,
        "ei":       0.000,
        "tci":      0.312,
        "avi":      0.000,
        "cri":      None,
        "expected": 0.000,
    },
    {
        "name":     "Embodied GEC++ Agent (projected)",
        "csmi":     0.731,
        "rii":      0.614,
        "tbi":      0.423,
        "ei":       0.241,
        "tci":      0.312,
        "avi":      0.198,
        "cri":      None,
        "expected": 0.376,
    },
]


def compute_cei(system):
    components = [
        system["csmi"], system["rii"], system["tbi"],
        system["ei"],   system["tci"], system["avi"],
    ]
    if USE_CRI and system["cri"] is not None:
        components.append(system["cri"])
        n = 7
    else:
        n = 6
    product = 1.0
    for c in components:
        product *= c
    return product ** (1 / n)


def bottlenecks(system):
    fields = ["csmi", "rii", "tbi", "ei", "tci", "avi"]
    scores = [(f.upper(), system[f]) for f in fields]
    scores.sort(key=lambda x: x[1])
    return scores[:2]


print("=" * 62)
print("  GEC++ System Comparison -- All Six Systems")
if USE_CRI:
    print("  CRI active (7-component formula)")
print("=" * 62)

for s in systems:
    cei = compute_cei(s)
    exp = s["expected"]
    match = "OK" if abs(cei - exp) < 0.001 else "MISMATCH expected {:.3f}".format(exp)
    zeros = [f.upper() for f in ["csmi","rii","tbi","ei","tci","avi"] if s[f] == 0.0]
    collapse = "  [zero-collapse: {}]".format(", ".join(zeros)) if zeros else ""

    print("")
    print("  {}".format(s["name"]))
    print("  CSMI={}  RII={}  TBI={}".format(s["csmi"], s["rii"], s["tbi"]))
    print("  EI={}    TCI={}  AVI={}".format(s["ei"], s["tci"], s["avi"]))
    print("  CEI++ = {:.3f}  {}{}".format(cei, match, collapse))

    if cei > 0:
        low = bottlenecks(s)
        print("  Bottlenecks: {}={}, {}={}".format(
            low[0][0], low[0][1], low[1][0], low[1][1]))

print("")
print("=" * 62)
print("  Zero-collapse confirmed: any component = 0 -> CEI++ = 0")
print("  CRI (7th component) scaffolded -- activate with USE_CRI = True")
print("=" * 62)
