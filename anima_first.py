# anima_first.py
# First GEC++ calculation — Awake Brain (Generation 3, paper Table 4)

# The six component scores for the Awake Brain system
# Source: GEC++ Theory paper, Generation 3 simulation
csmi = 0.892
rii  = 0.836
tbi  = 0.198
ei   = 0.097
tci  = 0.913
avi  = 0.499

# CEI++ formula: geometric mean of all six
cei_pp = (csmi * rii * tbi * ei * tci * avi) ** (1/6)

# Print the result
print("=== Anima: GEC++ Score Calculator ===")
print(f"System : Awake Brain")
print(f"CSMI   : {csmi}")
print(f"RII    : {rii}")
print(f"TBI    : {tbi}  ← bottleneck")
print(f"EI     : {ei}   ← bottleneck")
print(f"TCI    : {tci}")
print(f"AVI    : {avi}")
print(f"CEI++  : {cei_pp:.3f}")
print(f"Expected: 0.432")
