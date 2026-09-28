"""Fabricate test candidates (OPLA project files with scaled results) from a real OPLA CSV export.

Usage: python3 tests/compare/make_candidates.py <seed-folder>

<seed-folder> must contain the files produced by OPLA's "Export as CSV":
midpoint_impact_results.csv, endpoint_impact_results.csv, midpoint_chart_data.csv, endpoint_chart_data.csv

Writes tests/compare/candidates/ with one lca_study JSON per candidate (the format of OPLA's "Export project")
and, in rejected/, files the comparison must refuse.
"""
import csv, json, pathlib, random, shutil, sys

if len(sys.argv) != 2:
    sys.exit(__doc__)

SEED = pathlib.Path(sys.argv[1])
SRC = {name: SEED / name for name in [
    "midpoint_impact_results.csv", "endpoint_impact_results.csv", "midpoint_chart_data.csv", "endpoint_chart_data.csv",
]}
missing = [str(p) for p in SRC.values() if not p.is_file()]
if missing:
    sys.exit("Missing seed file(s): " + ", ".join(missing))

OUT = pathlib.Path(__file__).parent / "candidates"
shutil.rmtree(OUT, ignore_errors=True)
(OUT / "rejected").mkdir(parents=True)

def read(p):
    with open(p, newline="") as f:
        return list(csv.reader(f))

def totals(rows, factor=1.0, jitter=0.0):
    return [{"impact": r[0], "value": float(f"{float(r[1]) * factor * (1 + random.uniform(-jitter, jitter)):.3e}"), "unit": r[2]}
            for r in rows[1:] if r and r[0]]

def shares(rows):
    return {"categories": rows[0][1:], "contributors": [{"name": r[0], "data": [float(v or 0) for v in r[1:]]} for r in rows[1:] if r and r[0]]}

def reshuffled(rows, names):
    """Same categories, new contributor names and random shares summing to 100."""
    ncat = len(rows[0]) - 1
    cols = []
    for _ in range(ncat):
        w = [random.uniform(0.5, 3) for _ in names]
        s = sum(w)
        cols.append([round(x / s * 100, 2) for x in w])
    return {"categories": rows[0][1:], "contributors": [{"name": n, "data": [cols[c][i] for c in range(ncat)]} for i, n in enumerate(names)]}

EMPTY_SHARES = {"categories": [], "contributors": []}

def study(name, fu, flexible, materials, processes, eols, mid, end, mid_sh, end_sh):
    return {
        "goal_projectName": name, "goal_functionalUnit": fu,
        "summary": {
            "projectName": name, "functionalUnit": fu,
            "productionLocation": "Average regions of the World", "usageLocation": "Average regions of Canada",
            "isFlexible": flexible, "eolApproach": "Recycled content",
            "materials": materials, "processes": processes, "eols": eols,
        },
        "results": {
            "version": 1, "generatedAt": "2026-09-24T00:00:00.000Z",
            "midpoints": {"totals": mid, "contributions": mid_sh},
            "endpoints": {"totals": end, "contributions": end_sh, "midpointAttribution": EMPTY_SHARES},
        },
    }

def row(name, amount, unit):
    return {"name": name, "amount": amount, "unit": unit}

def write(path, data):
    path.write_text(json.dumps(data, indent=1))

random.seed(7)
MID, END = read(SRC["midpoint_impact_results.csv"]), read(SRC["endpoint_impact_results.csv"])
MID_SH, END_SH = read(SRC["midpoint_chart_data.csv"]), read(SRC["endpoint_chart_data.csv"])
FU = "Protecting one kg of meat"

# A: the real export, untouched
write(OUT / "A_LDPE_film.json", study(
    "LDPE/LLDPE film", FU, True,
    [row("LDPE granulate", 10, "kg"), row("LLDPE granulate", 3, "kg")], [row("extrusion, plastic film | RER", 13, "kg")],
    [row("treatment of waste plastic, sanitary landfill | CA", 100, "%")],
    totals(MID), totals(END), shares(MID_SH), shares(END_SH)))

# B: PP tray, lower in most categories, different contributors
names_b = ["PP", "thermoforming | RER", "treatment of waste plastic, mixture, sanitary landfill | CA"]
write(OUT / "B_PP_tray.json", study(
    "PP tray", FU, False, [row("PP granulate", 15, "kg")], [row("thermoforming | RER", 15, "kg")],
    [row("treatment of waste plastic, mixture, sanitary landfill | CA", 100, "%")],
    totals(MID, 0.78, 0.25), totals(END, 0.8, 0.1), reshuffled(MID_SH, names_b), reshuffled(END_SH, names_b)))

# C: PET tray, higher, no breakdown, different functional unit
write(OUT / "C_PET_tray.json", study(
    "PET tray", "Protecting 500 g of meat", False, [row("PET granulate", 20, "kg")], [row("thermoforming | RER", 20, "kg")],
    [row("recycling of PET | CA", 30, "%"), row("sanitary landfill | CA", 70, "%")],
    totals(MID, 1.35, 0.3), totals(END, 1.3, 0.1), EMPTY_SHARES, EMPTY_SHARES))

# D: paper laminate, lowest, 5 contributors with a negative end-of-life credit
names_d = ["kraft paper", "PE coating", "lamination | GLO", "printing | RER", "recycling credit | CA"]
mid_d = reshuffled(MID_SH, names_d)
for c in range(len(mid_d["categories"])):
    k = mid_d["contributors"]
    k[4]["data"][c] = -round(random.uniform(1, 8), 2)
    k[0]["data"][c] = round(100 - sum(k[i]["data"][c] for i in range(1, 5)), 2)
write(OUT / "D_Paper_laminate.json", study(
    "Paper laminate", FU, True, [row("kraft paper", 8, "kg"), row("PE coating", 1, "kg")],
    [row("lamination | GLO", 9, "kg"), row("printing | RER", 9, "kg")], [row("paper recycling | CA", 100, "%")],
    totals(MID, 0.55, 0.4), totals(END, 0.6, 0.1), mid_d, reshuffled(END_SH, names_d)))

# Files the comparison must refuse
(OUT / "rejected" / "midpoint_impact_results.csv").write_text(SRC["midpoint_impact_results.csv"].read_text())
old = json.loads((OUT / "A_LDPE_film.json").read_text())
old.pop("summary"); old.pop("results")
write(OUT / "rejected" / "old_lca_study.json", old)
write(OUT / "rejected" / "opla_comparison.json", {"app": "opla-compare", "version": "v0.1.0", "candidates": []})

print("candidates written to", OUT)
for p in sorted(OUT.rglob("*")):
    if p.is_file(): print("  ", p.relative_to(OUT))
