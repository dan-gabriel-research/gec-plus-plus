# anima_first.py
# First GEC++ calculation — Awake Brain

# The six component scores from our simulation
csmi = 0.947
rii  = 1.000
tbi  = 0.472
ei   = 0.079
tci  = 0.769
avi  = 0.072

# CEI++ formula: geometric mean of all six
cei_pp = (csmi * rii * tbi * ei * tci * avi) ** (1/6)

# Print the result
print("=== Anima: GEC++ Score Calculator ===")
print(f"CSMI : {csmi}")
print(f"RII  : {rii}")
print(f"TBI  : {tbi}")
print(f"EI   : {ei}")
print(f"TCI  : {tci}")
print(f"AVI  : {avi}")
print(f"CEI++: {cei_pp:.3f}")
