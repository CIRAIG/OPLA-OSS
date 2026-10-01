"""Fabricate test candidates (OPLA project files with scaled results) from a real OPLA project export.

Usage: python3 tests/compare/make_candidates.py <lca_study.json>

<lca_study.json> is the file downloaded with "Export project" in OPLA (the only input of the comparison).
run_test.py builds such a project in OPLA, exports it and calls make() itself, so running this script by hand
is only needed to inspect the candidates.

Writes tests/compare/candidates/ with one lca_study JSON per candidate (same format as "Export project")
and, in rejected/, files the comparison must refuse.
"""
import copy, json, pathlib, random, shutil, sys

OUT = pathlib.Path(__file__).parent / "candidates"
EMPTY_SHARES = {"categories": [], "contributors": []}
FU = "Protecting one kg of meat"


def totals(items, factor=1.0, jitter=0.0):
    return [{"impact": t["impact"], "value": float(f"{t['value'] * factor * (1 + random.uniform(-jitter, jitter)):.3e}"), "unit": t["unit"]}
            for t in items]


def reshuffled(shares, names):
    """Same categories, new contributor names and random shares summing to 100."""
    cats = shares["categories"]
    cols = []
    for _ in cats:
        w = [random.uniform(0.5, 3) for _ in names]
        s = sum(w)
        cols.append([round(x / s * 100, 2) for x in w])
    return {"categories": list(cats), "contributors": [{"name": n, "data": [cols[c][i] for c in range(len(cats))]} for i, n in enumerate(names)]}


def study(seed, name, fu, flexible, materials, processes, eols, mid, end, mid_sh, end_sh):
    """A copy of the exported project with a new name, summary and results."""
    data = copy.deepcopy(seed)
    data["goal_projectName"], data["goal_functionalUnit"] = name, fu
    data["summary"] = dict(seed["summary"], projectName=name, functionalUnit=fu, isFlexible=flexible,
                           materials=materials, processes=processes, eols=eols)
    data["results"] = dict(seed["results"],
                           midpoints={"totals": mid, "contributions": mid_sh},
                           endpoints=dict(seed["results"]["endpoints"], totals=end, contributions=end_sh))
    return data


def row(name, amount, unit):
    return {"name": name, "amount": amount, "unit": unit}


def write(path, data):
    path.write_text(json.dumps(data, indent=1))


def make(seed_path):
    seed = json.loads(pathlib.Path(seed_path).read_text())
    if "results" not in seed or "summary" not in seed:
        raise ValueError(f"{seed_path} has no results: export a completed project with \"Export project\"")
    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "rejected").mkdir(parents=True)
    random.seed(7)
    mid, end = seed["results"]["midpoints"]["totals"], seed["results"]["endpoints"]["totals"]
    mid_sh, end_sh = seed["results"]["midpoints"]["contributions"], seed["results"]["endpoints"]["contributions"]

    # A: the real export, results untouched
    write(OUT / "A_LDPE_film.json", study(
        seed, "LDPE/LLDPE film", FU, True,
        [row("LDPE granulate", 10, "kg"), row("LLDPE granulate", 3, "kg")], [row("extrusion, plastic film | RER", 13, "kg")],
        [row("treatment of waste plastic, sanitary landfill | CA", 100, "%")],
        totals(mid), totals(end), mid_sh, end_sh))

    # B: PP tray, lower in most categories, different contributors
    names_b = ["PP", "thermoforming | RER", "treatment of waste plastic, mixture, sanitary landfill | CA"]
    write(OUT / "B_PP_tray.json", study(
        seed, "PP tray", FU, False, [row("PP granulate", 15, "kg")], [row("thermoforming | RER", 15, "kg")],
        [row("treatment of waste plastic, mixture, sanitary landfill | CA", 100, "%")],
        totals(mid, 0.78, 0.25), totals(end, 0.8, 0.1), reshuffled(mid_sh, names_b), reshuffled(end_sh, names_b)))

    # C: PET tray, higher, no breakdown, different functional unit
    write(OUT / "C_PET_tray.json", study(
        seed, "PET tray", "Protecting 500 g of meat", False, [row("PET granulate", 20, "kg")], [row("thermoforming | RER", 20, "kg")],
        [row("recycling of PET | CA", 30, "%"), row("sanitary landfill | CA", 70, "%")],
        totals(mid, 1.35, 0.3), totals(end, 1.3, 0.1), EMPTY_SHARES, EMPTY_SHARES))

    # D: paper laminate, lowest, 5 contributors with a negative end-of-life credit
    names_d = ["kraft paper", "PE coating", "lamination | GLO", "printing | RER", "recycling credit | CA"]
    mid_d = reshuffled(mid_sh, names_d)
    for c in range(len(mid_d["categories"])):
        k = mid_d["contributors"]
        k[4]["data"][c] = -round(random.uniform(1, 8), 2)
        k[0]["data"][c] = round(100 - sum(k[i]["data"][c] for i in range(1, 5)), 2)
    write(OUT / "D_Paper_laminate.json", study(
        seed, "Paper laminate", FU, True, [row("kraft paper", 8, "kg"), row("PE coating", 1, "kg")],
        [row("lamination | GLO", 9, "kg"), row("printing | RER", 9, "kg")], [row("paper recycling | CA", 100, "%")],
        totals(mid, 0.55, 0.4), totals(end, 0.6, 0.1), mid_d, reshuffled(end_sh, names_d)))

    # Files the comparison must refuse: a non-JSON file, a project exported without results, a saved comparison
    (OUT / "rejected" / "results.csv").write_text("Impact,Value,Unit\n" + "".join(f"{t['impact']},{t['value']},{t['unit']}\n" for t in mid))
    old = copy.deepcopy(seed)
    old.pop("summary"); old.pop("results")
    write(OUT / "rejected" / "old_lca_study.json", old)
    write(OUT / "rejected" / "opla_comparison.json", {"app": "opla-compare", "version": "v0.1.0", "candidates": []})
    return OUT


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        out = make(sys.argv[1])
    except (OSError, ValueError) as e:
        sys.exit(str(e))
    print("candidates written to", out)
    for p in sorted(out.rglob("*")):
        if p.is_file(): print("  ", p.relative_to(out))
