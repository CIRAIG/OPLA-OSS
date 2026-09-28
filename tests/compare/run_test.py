"""Load the OPLA build (dist/opla.html) in headless Chromium, open the comparison mode, feed the fabricated
project files (lca_study JSON), screenshot every view and check the numbers. Also checks real OPLA projects
reaching the comparison through their "Export project" file (left menu and results-step badge).

Prerequisites:
  ./compile-release.sh test
  python3 tests/compare/make_candidates.py <seed-folder>
  pip install playwright && playwright install chromium   (or set CHROMIUM_PATH to an existing build)
"""
import json, math, os, pathlib, sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
HTML = ROOT / "dist" / "opla.html"
CAND = HERE / "candidates"
SHOTS = HERE / "shots"
SHOTS.mkdir(exist_ok=True)

# OPLA loads its font from Google Fonts; that is the only external request allowed (it is blocked in the test)
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
COMPARATOR = "Alpine.$data(document.querySelector('[x-data=\"comparator\"]'))"
GLOBAL = "Alpine.$data(document.querySelector('[x-data=\"global\"]'))"

if not HTML.is_file():
    sys.exit(f"{HTML} not found, run ./compile-release.sh test first")
if not CAND.is_dir():
    sys.exit(f"{CAND} not found, run tests/compare/make_candidates.py <seed-folder> first")

errors = []
console = []

def allowed(url):
    return url.startswith("file://") or any(h in url for h in ALLOWED_HOSTS)

with sync_playwright() as p:
    launch = {"args": ["--no-sandbox"]}
    if os.environ.get("CHROMIUM_PATH"):
        launch["executable_path"] = os.environ["CHROMIUM_PATH"]
    browser = p.chromium.launch(**launch)
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
    ctx.route("**/*", lambda route: route.continue_() if route.request.url.startswith("file://") else route.abort())
    page = ctx.new_page()
    page.on("console", lambda m: console.append((m.type, m.text)))
    # Alpine throws "reading 'after'" on duplicate x-for keys; the local EoL dataset has
    # duplicate activity names, which is a data issue unrelated to the comparison
    page.on("pageerror", lambda e: "reading 'after'" not in str(e) and errors.append(str(e)))
    page.on("requestfailed", lambda r: (not allowed(r.url)) and errors.append("network request: " + r.url))
    page.on("request", lambda r: (not allowed(r.url)) and errors.append("external request: " + r.url))

    def enter_compare():
        page.locator(".welcome-page__choice--compare").click()
        page.wait_for_selector('[x-data="comparator"]')
        page.wait_for_timeout(300)

    def comparator(js):
        return page.evaluate(f"() => {{ const d = {COMPARATOR}; {js} }}")

    page.goto(HTML.as_uri())
    page.wait_for_timeout(800)
    if page.locator(".init-system-error").count():
        errors.append("OPLA initialisation error: " + page.locator(".init-system-error__error-text").inner_text())
    enter_compare()
    page.screenshot(path=str(SHOTS / "00_empty.png"), full_page=True)

    # ---- load the four project files at once through the drop zone's file input
    drop_input = page.locator(".compare-dropzone .compare-dropzone__input")
    FOLDERS = ["A_LDPE_film", "B_PP_tray", "C_PET_tray", "D_Paper_laminate"]
    drop_input.set_input_files([str(CAND / (f + ".json")) for f in FOLDERS])
    page.wait_for_timeout(600)
    # files that must be refused: no card is created, one notice each
    drop_input.set_input_files(sorted(str(f) for f in (CAND / "rejected").iterdir()))
    page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / "01_candidates.png"), full_page=True)
    if page.locator(".compare-chip").count(): errors.append("file status chips are still shown")
    if page.locator(".compare-list .compare-dropzone").count(): errors.append("candidate rows still have their own drop zone")
    if page.locator(".compare-list__row").count() != 4: errors.append("expected 4 candidate rows")
    heights = page.eval_on_selector_all(".compare-list__row", "rows => rows.map(r => r.getBoundingClientRect().height)")
    if max(heights) > 48: errors.append(f"candidate rows too tall: {heights}")
    if page.evaluate("() => !(document.querySelector('.compare-dropzone').compareDocumentPosition(document.querySelector('.compare-list')) & Node.DOCUMENT_POSITION_FOLLOWING)"):
        errors.append("drop zone should be above the candidate list")
    # composition details are collapsed by default and open on click
    if page.locator(".compare-list__item:visible").count(): errors.append("composition details should start collapsed")
    page.locator(".compare-list__expand").first.click()
    page.wait_for_timeout(200)
    if page.locator(".compare-list__item:visible").count() == 0: errors.append("project summary details not shown when expanded")
    page.screenshot(path=str(SHOTS / "01b_candidates_expanded.png"), full_page=True)
    page.locator(".compare-list__expand").first.click()

    # ---- state checks (on the first midpoint category where candidate A has a non-zero total)
    STUDIES = {f: json.load(open(CAND / (f + ".json"))) for f in FOLDERS}
    def totals(folder):
        return {t["impact"]: (t["value"], t["unit"]) for t in STUDIES[folder]["results"]["midpoints"]["totals"]}
    CAT = next(k for k, (v, _) in totals("A_LDPE_film").items() if v != 0)
    cat_js = json.dumps(CAT)
    state = comparator(f"""
        const cat = {cat_js};
        return {{
            names: d.candidates.map(c => c.name), fu: d.candidates.map(c => c.fu),
            materials: d.candidates.map(c => c.summary.materials.map(m => m.name)),
            dropNotices: d.dropNotices,
            nMid: d.categories('midpoint').length, nEnd: d.categories('endpoint').length,
            fuWarn: d.fuWarning(), cov: d.coverageWarnings(),
            values: d.candidates.map(c => d.getValue(c, 'midpoint', cat)),
            rel: d.candidates.map(c => d.relative(c, 'midpoint', cat)),
            bA: d.breakdownFor(d.candidates[0], 'midpoint', cat),
            bC: d.breakdownFor(d.candidates[2], 'midpoint', cat),
            wins: d.summaryWins(),
        }};
    """)
    print("checked category:", CAT)
    print(json.dumps(state, indent=1)[:3000])

    # expected values from the files
    exp = [totals(f) for f in FOLDERS]
    cc = [e[CAT][0] for e in exp]
    for i, (got, want) in enumerate(zip(state["values"], cc)):
        if not math.isclose(got, want, rel_tol=1e-9): errors.append(f"value mismatch cand {i}: {got} vs {want}")
    positives = [v for v in cc if v > 0]
    ref = max(cc) if positives else max(abs(v) for v in cc)
    for i, r in enumerate(state["rel"]):
        if r is None or not math.isclose(r, cc[i] / ref * 100, rel_tol=1e-9): errors.append(f"relative mismatch cand {i}")
    # breakdown of A: first contributor's value = total x share / 100
    shares = STUDIES["A_LDPE_film"]["results"]["midpoints"]["contributions"]
    col = shares["categories"].index(CAT)
    first = shares["contributors"][0]
    got = next(b for b in state["bA"] if b["name"] == first["name"])
    if not math.isclose(got["value"], cc[0] * first["data"][col] / 100, rel_tol=1e-9): errors.append("breakdown value wrong")
    if state["bC"] is not None: errors.append("C should have no breakdown")
    if state["nMid"] != 18 or state["nEnd"] != 2: errors.append("category counts wrong")
    if not state["fuWarn"]: errors.append("FU warning expected (PET tray has a different FU)")
    if state["names"] != ["LDPE/LLDPE film", "PP tray", "PET tray", "Paper laminate"]: errors.append("names from the project files not applied: " + str(state["names"]))
    if state["fu"][0] != "Protecting one kg of meat": errors.append("functional unit from the project file not applied")
    if state["materials"][0] != ["LDPE granulate", "LLDPE granulate"]: errors.append("summary materials wrong: " + str(state["materials"][0]))
    notices = " | ".join(state["dropNotices"])
    if len(state["dropNotices"]) != 3: errors.append("expected 3 refused files: " + notices)
    for needle in ["midpoint_impact_results.csv is not an OPLA project file", "old_lca_study.json has no results", "opla_comparison.json is a saved comparison"]:
        if needle not in notices: errors.append("missing drop notice: " + needle)

    # ---- views
    def go(view, name, wait=900):
        comparator(f"d.setView('{view}');")
        page.wait_for_timeout(wait)
        page.screenshot(path=str(SHOTS / name), full_page=True)

    go("relative", "02_relative_columns.png")
    comparator("d.relLayout = 'rows'; d.afterChange();")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "03_relative_rows.png"), full_page=True)
    comparator("d.relLayout = 'columns'; d.relLevel = 'endpoint'; d.referenceId = String(d.candidates[0].id); d.afterChange();")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "04_relative_endpoint_refA.png"), full_page=True)
    comparator("d.relLevel = 'midpoint'; d.afterChange();")
    go("absolute", "05_absolute.png")
    go("radar", "06_radar.png")
    go("heatmap", "07_heatmap.png")
    page.locator(".compare-heat__head--cand").nth(3).click(); page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / "08_heatmap_sorted.png"), full_page=True)
    go("stacked", "09_stacked.png")
    comparator("d.stackMode = 'percent'; d.afterChange();")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "10_stacked_percent.png"), full_page=True)
    comparator("d.stackCategory = 'endpoint::Total human health'; d.stackMode = 'absolute'; d.afterChange();")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "11_stacked_endpoint.png"), full_page=True)

    # deactivate one candidate, check charts still render
    comparator("d.candidates[2].active = false; d.afterChange(); d.setView('relative');")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "12_relative_3active.png"), full_page=True)
    comparator("d.candidates[2].active = true; d.afterChange();")

    # ---- save session, reload page, load session (both buttons sit on the Candidates step)
    comparator("d.setView('candidates');")
    page.wait_for_timeout(300)
    if page.locator(".app__leftNav >> text=Save comparison").count(): errors.append("'Save comparison' still in the left menu")
    with page.expect_download() as dl:
        page.locator(".compare-candidates-header >> text=Save comparison").click()
    saved_path = HERE / "opla_comparison.json"; dl.value.save_as(str(saved_path))
    data = json.load(open(saved_path))
    if len(data["candidates"]) != 4: errors.append("session save wrong")
    with page.expect_download() as dl2:
        page.locator("text=Export table (CSV)").click()
    csv_path = HERE / "opla_comparison_table.csv"; dl2.value.save_as(str(csv_path))
    print(open(csv_path).read()[:1500])

    page.reload(); page.wait_for_timeout(800)
    enter_compare()
    if page.locator(".app__leftNav >> text=Load comparison").count(): errors.append("'Load comparison' still in the left menu")
    with page.expect_file_chooser() as fc:
        page.locator(".compare-candidates-header >> text=Load comparison").click()
    fc.value.set_files(str(saved_path))
    page.wait_for_timeout(1200)
    after = comparator("return {n: d.candidates.length, view: d.view, names: d.candidates.map(c => c.name), ref: d.referenceId};")
    print("after reload:", after)
    if after["n"] != 4: errors.append("session load failed")
    page.screenshot(path=str(SHOTS / "13_after_load.png"), full_page=True)
    if page.locator("text=Print report").count(): errors.append("print report button still shown")
    comparator("d.setView('candidates');")
    page.wait_for_timeout(300)
    page.locator(".card--compare:has(.compare-candidates-header)").screenshot(path=str(SHOTS / "13b_candidates_load_button.png"))

    # narrow viewport
    page.set_viewport_size({"width": 1024, "height": 800})
    comparator("d.setView('absolute');")
    page.wait_for_timeout(900); page.screenshot(path=str(SHOTS / "15_narrow_absolute.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})

    # ---- "remove all candidates" asks first: Cancel keeps them, Confirm clears them
    comparator("d.setView('candidates');")
    page.wait_for_timeout(300)
    n_before = comparator("return d.candidates.length;")
    page.locator("text=remove all candidates").click()
    page.wait_for_timeout(300)
    modal = page.locator(".compare-modal__content")
    if not modal.count() or "Remove all candidates?" not in modal.inner_text(): errors.append("remove-all modal missing or blank")
    if comparator("return d.candidates.length;") != n_before: errors.append("remove-all cleared candidates before confirmation")
    page.screenshot(path=str(SHOTS / "15e_remove_all_modal.png"), full_page=False)
    modal.locator("text=Cancel").click()
    page.wait_for_timeout(200)
    if page.locator(".compare-modal").count() or comparator("return d.candidates.length;") != n_before: errors.append("remove-all Cancel did not keep the candidates")
    page.locator("text=remove all candidates").click()
    page.wait_for_timeout(300)
    page.locator(".compare-modal__content >> text=Confirm").click()
    page.wait_for_timeout(300)
    if page.locator(".compare-modal").count() or comparator("return d.candidates.length;") != 0: errors.append("remove-all Confirm did not clear the candidates")

    # ---- leaving and re-entering the mode starts a fresh comparison
    page.locator(".app--compare .app__leftNav__logo").click()
    page.wait_for_selector(".welcome-page")
    if page.locator('[x-data="comparator"]').count(): errors.append("comparator still mounted on the welcome page")
    enter_compare()
    if comparator("return d.candidates.length;") != 0: errors.append("comparison not reset when re-entered")

    # ---- 50 projects stay readable: compact rows, drop zone still on top
    many = comparator(f"""
        const text = {json.dumps((CAND / 'A_LDPE_film.json').read_text())};
        for (let i = 0; i < 50; i++) d.ingestProject('p' + i + '.json', text);
        d.candidates.forEach((c, i) => c.name = 'Project ' + (i + 1));
        d.afterChange();
        return d.candidates.length;
    """)
    page.wait_for_timeout(600)
    list_h = page.evaluate("() => document.querySelector('.compare-list__table').getBoundingClientRect().height")
    if many != 50 or list_h > 50 * 40 + 60: errors.append(f"50 candidates: count {many}, list height {list_h}px")
    page.screenshot(path=str(SHOTS / "15b_fifty_candidates.png"), full_page=False)

    # ---- 50 projects: the relative chart keeps readable bars and scrolls inside its card
    rel_box = "() => { const b = document.querySelector('.compare-chart--scrollable'); const s = b.querySelector('svg'); return { sw: b.scrollWidth, cw: b.clientWidth, sh: b.scrollHeight, ch: b.clientHeight, vh: innerHeight, svg: s && s.getAttribute('width') }; }"
    comparator("d.relLayout = 'columns'; d.setView('relative');")
    page.wait_for_timeout(1200)
    box = page.evaluate(rel_box)
    if box["sw"] <= box["cw"]: errors.append(f"50 candidates, columns: relative chart does not scroll horizontally {box}")
    page.locator(".compare-chart--scrollable").screenshot(path=str(SHOTS / "15c_fifty_relative_columns.png"))
    comparator("d.relLayout = 'rows'; d.afterChange();")
    page.wait_for_timeout(1200)
    box = page.evaluate(rel_box)
    if box["sh"] <= box["ch"] or box["ch"] > box["vh"] * 0.76: errors.append(f"50 candidates, rows: relative chart does not scroll vertically {box}")
    page.locator(".compare-chart--scrollable").screenshot(path=str(SHOTS / "15d_fifty_relative_rows.png"))
    comparator("d.candidates = d.candidates.slice(0, 3); d.relLayout = 'columns'; d.afterChange();")
    page.wait_for_timeout(1200)
    box = page.evaluate(rel_box)
    if box["sw"] > box["cw"] or box["sh"] > box["ch"]: errors.append(f"3 candidates: relative chart should fit without scrollbar {box}")
    comparator("d.setView('candidates');")

    # ---- real OPLA projects -> comparison, through the exported JSON only
    # IDs come from the local overwrite/ datasets
    PROJECTS = [
        {"name": "JSON project 1", "fu": "Protecting one kg of meat", "mass": 2,
         "materials": ["material-Product 1 from Activity 1 | GLO", "material-Product 2 from Activity 2 | RoW"]},
        {"name": "JSON project 2", "fu": "Protecting one kg of meat", "mass": 5,
         "materials": ["material-Product 2 from Activity 2 | RoW"]},
    ]
    def build_project(proj):
        page.locator(".app__leftNav__logo:visible").first.click()
        page.wait_for_selector(".welcome-page")
        page.locator(".welcome-page__choice--new").click()
        page.wait_for_timeout(300)
        return page.evaluate(f"""async (p) => {{
            const g = {GLOBAL};
            g.goal_projectName = p.name; g.goal_functionalUnit = p.fu;
            g.goal_productionLocation = 'global'; g.goal_usageLocation = 'canada'; g.goal_isFlexible = 'yes';
            g.composition_materials = p.materials.map(type => ({{ type, mass: p.mass }}));
            g.processing_methods = [{{ type: 'processing-Activity 160 | RER', mass: 3 }}];
            g.eol_methods = [{{ type: 'Activity 835 | CA', mass: 100 }}];
            await g.$nextTick();
            return {{
                mid: g.midPointImpactResults().map(r => [r.impact, parseFloat(r.value)]),
                end: g.endPointImpactResults().map(r => [r.impact, parseFloat(r.value)]),
                nContrib: g.getMidPointChartData().series.length,
                materials: p.materials.map(type => g.getNameFromUUID(type)),
            }};
        }}""", proj)

    def check_candidate(label, cand, proj, expected):
        if cand["name"] != proj["name"]: errors.append(f"{label}: name {cand['name']!r}")
        if cand["fu"] != proj["fu"]: errors.append(f"{label}: functional unit {cand['fu']!r}")
        if cand["mid"] != expected["mid"]: errors.append(f"{label}: midpoint totals differ from OPLA")
        if cand["end"] != expected["end"]: errors.append(f"{label}: endpoint totals differ from OPLA")
        if cand["nContrib"] != expected["nContrib"]: errors.append(f"{label}: contributor count {cand['nContrib']} vs {expected['nContrib']}")
        if cand["materials"] != expected["materials"]: errors.append(f"{label}: summary materials {cand['materials']} vs {expected['materials']}")
        if cand["production"] != "Average regions of the World" or not cand["flexible"]: errors.append(f"{label}: summary goal fields {cand['production']!r}, {cand['flexible']}")

    CANDS_JS = """return d.candidates.map(c => ({
        name: c.name, fu: c.fu,
        mid: (c.midTotals || []).map(t => [t.impact, t.value]), end: (c.endTotals || []).map(t => [t.impact, t.value]),
        nContrib: c.midShares ? c.midShares.contributors.length : 0,
        materials: c.summary.materials.map(m => m.name), production: c.summary.productionLocation, flexible: c.summary.isFlexible,
    }));"""

    expected, exported = [], []
    for i, proj in enumerate(PROJECTS):
        expected.append(build_project(proj))
        # let OPLA's chart animations finish (resetting a project mid-animation makes ApexCharts throw)
        page.wait_for_timeout(1500)
        if not any(v for _, v in expected[-1]["mid"]): errors.append(f"project {i} has only zero results, test is not meaningful")
        if page.locator("text=Add to comparison").count(): errors.append("'Add to comparison' is still shown in the project view")
        if i == 0:
            # the left menu's "Export project"
            with page.expect_download() as dl:
                page.locator("text=Export project").first.click()
        else:
            # the invitation badge shown in the results step
            page.evaluate(f"() => {{ {GLOBAL}.currentStep = 'results'; }}")
            invite = page.locator(".compare-invite")
            invite.wait_for(state="visible")
            invite.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            invite.screenshot(path=str(SHOTS / "16a_compare_invite.png"))
            if "Export project to compare" not in invite.inner_text(): errors.append("invite badge text wrong")
            with page.expect_download() as dl:
                invite.click()
        path = HERE / f"lca_study_{i + 1}.json"; dl.value.save_as(str(path))
        exported.append(path)
        data = json.load(open(path))
        if "results" not in data or "summary" not in data: errors.append(f"exported {path.name} lacks results or summary")

    # the welcome page no longer carries a queue
    page.locator(".app__leftNav__logo:visible").first.click()
    page.wait_for_selector(".welcome-page")
    if page.locator(".welcome-page__choice__badge").count(): errors.append("queue badge still on the welcome page")
    page.screenshot(path=str(SHOTS / "16_welcome.png"), full_page=True)

    # file drop: both exported JSON files at once -> one candidate each
    enter_compare()
    page.locator(".compare-dropzone .compare-dropzone__input").set_input_files([str(p) for p in exported])
    page.wait_for_timeout(600)
    dropped = comparator(CANDS_JS)
    if len(dropped) != 2: errors.append(f"dropped JSON files should give 2 candidates, got {len(dropped)}")
    for i, (cand, proj, exp_) in enumerate(zip(dropped, PROJECTS, expected)):
        check_candidate(f"dropped {i}", cand, proj, exp_)

    # an exported study without results (older OPLA) is refused: no card, one notice
    old = json.load(open(exported[0])); old.pop("results"); old.pop("summary")
    old_path = HERE / "lca_study_old.json"; old_path.write_text(json.dumps(old))
    page.locator(".compare-dropzone .compare-dropzone__input").set_input_files([str(old_path)])
    page.wait_for_timeout(400)
    after_old = comparator("return { n: d.candidates.length, notices: d.dropNotices };")
    if after_old["n"] != 2: errors.append("a JSON without results created a candidate")
    if not any("lca_study_old.json has no results" in n for n in after_old["notices"]): errors.append("missing notice for a JSON without results")
    page.screenshot(path=str(SHOTS / "16b_json_dropped.png"), full_page=True)

    # ---- OPLA mode still works after the comparison
    page.locator(".app--compare .app__leftNav__logo").click()
    page.locator(".welcome-page__choice--new").click()
    page.wait_for_timeout(300)
    if not page.locator(".app__content__step-1").is_visible(): errors.append("OPLA project mode not shown")
    page.screenshot(path=str(SHOTS / "17_new_project.png"), full_page=True)

    browser.close()

print("\nCONSOLE:", [c for c in console if c[0] in ("error", "warning") and not any(h in c[1] for h in ALLOWED_HOSTS)][:20])
print("ERRORS:", errors)
sys.exit(1 if errors else 0)
