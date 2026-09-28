/*
 * OPLA Results Comparator
 * Comparison mode of OPLA: loads the project files (lca_study.json) exported by several OPLA runs
 * (one run = one packaging candidate) and compares them side by side.
 * Wrapped in an IIFE so its helpers do not leak into (or collide with) the global scope used by main.js.
 */
(() => {

const APP_VERSION = 'v0.1.0';

// Categorical palette for candidates (validated for colour-vision deficiency, fixed order)
const CANDIDATE_PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948',
                           '#7fb3e6', '#f4a685', '#8cd6b9', '#f3cd73', '#f2b9cf', '#7fc17f', '#a59ad8', '#f0a3a2'];
// Palette for contributors (materials / processes / end-of-life) in stacked charts
const CONTRIBUTOR_PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948',
                             '#7fb3e6', '#f4a685', '#8cd6b9', '#f3cd73', '#f2b9cf', '#7fc17f', '#a59ad8', '#f0a3a2',
                             '#6b6b6b', '#b0b0b0'];
const NO_BREAKDOWN_COLOR = '#9e9e9e';
const CHART_FONT = '"Source Sans 3", "Segoe UI", Helvetica, Arial, sans-serif';

// Chart instances live outside Alpine's reactive proxy (ApexCharts objects must not be proxied)
const CHARTS = {};
// Renders are serialised: a render never starts before the previous one has finished,
// and if several are requested in a burst only the latest one actually runs.
let RENDER_CHAIN = Promise.resolve(), RENDER_SEQ = 0, MOUNT_SEQ = 0;
function queueRender(fn) {
    const seq = ++RENDER_SEQ;
    RENDER_CHAIN = RENDER_CHAIN.then(async () => { if (seq !== RENDER_SEQ) return; await fn(); }).catch(e => console.error('render failed', e));
    return RENDER_CHAIN;
}

/* ------------------------------------------------------------------ */
/* OPLA project files (lca_study.json from "Export project")            */
/* ------------------------------------------------------------------ */
function csvEscape(v) {
    const s = String(v ?? '');
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

const norm = s => String(s ?? '').trim().toLowerCase();

function parseTotals(list) {
    const items = (Array.isArray(list) ? list : [])
        .filter(r => r && r.impact)
        .map(r => ({ impact: String(r.impact), value: Number(r.value), unit: String(r.unit || '') }))
        .filter(r => Number.isFinite(r.value));
    return items.length ? items : null;
}

function parseShares(s) {
    if (!s || !Array.isArray(s.categories) || !Array.isArray(s.contributors)) return null;
    const categories = s.categories.map(String);
    const contributors = s.contributors.filter(k => k && k.name).map(k => ({
        name: String(k.name),
        data: categories.map((_, i) => { const v = Number(Array.isArray(k.data) ? k.data[i] : NaN); return Number.isFinite(v) ? v : 0; }),
    }));
    return categories.length && contributors.length ? { categories, contributors } : null;
}

function parseSummaryRows(list) {
    return (Array.isArray(list) ? list : []).filter(r => r && r.name).map(r => ({
        name: String(r.name),
        amount: typeof r.amount === 'number' && Number.isFinite(r.amount) ? r.amount : null,
        unit: String(r.unit || ''),
    }));
}

/**
 * Read an OPLA project file. Returns { project } with everything a candidate needs, or { error } explaining why it was rejected.
 */
function parseProjectFile(filename, text) {
    if (!/\.json$/i.test(filename) && !String(text).trim().startsWith('{')) {
        return { error: filename + ' is not an OPLA project file. Use the lca_study.json from "Export project" in OPLA.' };
    }
    let j;
    try { j = JSON.parse(text); } catch (e) { return { error: filename + ' is not a valid JSON file.' }; }
    if (!j || typeof j !== 'object') return { error: filename + ' is not an OPLA project file.' };
    if (j.app === 'opla-compare') return { error: filename + ' is a saved comparison, use "Load comparison" at the top of the Candidates step instead.' };

    const r = j.results || {}, s = j.summary;
    const midTotals = parseTotals(r.midpoints && r.midpoints.totals);
    const endTotals = parseTotals(r.endpoints && r.endpoints.totals);
    const hasResults = [...(midTotals || []), ...(endTotals || [])].some(t => t.value !== 0);
    if (!s || typeof s !== 'object' || !hasResults) {
        return { error: filename + ' has no results (older OPLA export or unfinished project). Open it in OPLA, complete it and export it again.' };
    }
    return {
        project: {
            name: String(s.projectName || '').trim() || filename.replace(/\.json$/i, ''),
            fu: String(s.functionalUnit || ''),
            summary: {
                productionLocation: String(s.productionLocation || ''),
                usageLocation: String(s.usageLocation || ''),
                isFlexible: s.isFlexible === true,
                eolApproach: String(s.eolApproach || ''),
                materials: parseSummaryRows(s.materials),
                processes: parseSummaryRows(s.processes),
                eols: parseSummaryRows(s.eols),
            },
            midTotals, endTotals,
            midShares: parseShares(r.midpoints && r.midpoints.contributions),
            endShares: parseShares(r.endpoints && r.endpoints.contributions),
        },
    };
}

/* ------------------------------------------------------------------ */
/* Formatting helpers                                                   */
/* ------------------------------------------------------------------ */
function fmtSci(v) {
    if (v === null || v === undefined || !Number.isFinite(v)) return '–';
    return Number(v).toExponential(3);
}
function fmtSmart(v) {
    if (v === null || v === undefined || !Number.isFinite(v)) return '–';
    const a = Math.abs(v);
    if (a === 0) return '0';
    if (a >= 1e4 || a < 1e-2) return Number(v).toExponential(2);
    return String(parseFloat(Number(v).toPrecision(3)));
}
function fmtPct(v, d = 1) {
    if (v === null || v === undefined || !Number.isFinite(v)) return '–';
    return Number(v).toFixed(d) + '%';
}
function shorten(s, n = 26) {
    s = String(s);
    return s.length > n ? s.slice(0, n - 1) + '…' : s;
}
function download(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
}
function hexToRgb(hex) {
    const h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function mix(c1, c2, t) {
    const a = hexToRgb(c1), b = hexToRgb(c2);
    return 'rgb(' + a.map((x, i) => Math.round(x + (b[i] - x) * t)).join(',') + ')';
}
// 0 = best (green) … 1 = worst (red), through a neutral grey midpoint
function heatColor(t) {
    if (t === null || !Number.isFinite(t)) return 'transparent';
    return t < 0.5 ? mix('#a9d69c', '#eeeeee', t * 2) : mix('#eeeeee', '#f5a3a3', (t - 0.5) * 2);
}

function destroyChart(id) {
    if (CHARTS[id]) { try { CHARTS[id].destroy(); } catch (e) { console.warn('chart destroy failed', id, e); } delete CHARTS[id]; }
}
async function mountChart(id, options, minWidth = 0) {
    const old = document.getElementById(id);
    if (!old) return;
    destroyChart(id);
    // Always draw into a fresh container: a destroyed chart can still have a debounced
    // resize/update pending, which would otherwise redraw its stale content into the same element.
    const el = document.createElement('div');
    el.id = id;
    // the chart fills its card but never gets narrower than minWidth (the card then scrolls)
    if (minWidth) el.style.minWidth = minWidth + 'px';
    old.replaceWith(el);
    options.chart = Object.assign({}, options.chart, { id: id + '-' + (++MOUNT_SEQ) });
    const chart = new ApexCharts(el, options);
    CHARTS[id] = chart;
    await chart.render();
}
function baseChart(type, height, filename, extra = {}) {
    return Object.assign({
        type, height, width: '100%', fontFamily: CHART_FONT, background: 'transparent',
        animations: { enabled: false },
        toolbar: {
            show: true,
            tools: { download: true, selection: false, zoom: false, zoomin: false, zoomout: false, pan: false, reset: false },
            export: { png: { filename }, svg: { filename }, csv: { filename } }
        }
    }, extra);
}

/* ------------------------------------------------------------------ */
/* Alpine component                                                     */
/* ------------------------------------------------------------------ */
document.addEventListener('alpine:init', () => {
    Alpine.data('comparator', () => ({
        version: APP_VERSION,
        candidates: [],
        nextId: 1,
        view: 'candidates',
        views: [
            { id: 'candidates', title: 'Candidates', index: 'Step 1' },
            { id: 'relative', title: 'Relative comparison', index: 'View A' },
            { id: 'absolute', title: 'Absolute per category', index: 'View B' },
            { id: 'radar', title: 'Radar profile', index: 'View C' },
            { id: 'heatmap', title: 'Heatmap table', index: 'View D' },
            { id: 'stacked', title: 'Stacked contributions', index: 'View E' },
        ],
        // settings
        referenceId: 'worst',
        relLevel: 'midpoint',
        relLayout: 'columns',
        absCategory: '',
        stackCategory: '',
        stackMode: 'absolute',
        radarHidden: [],
        heatSort: null,
        // ui
        dragOver: false,
        expandedIds: [],
        modal: null,
        dropNotices: [],
        _listeners: null,

        /* ---------------- lifecycle ---------------- */
        init() {
            this._listeners = {
                // Drop anywhere on the page (outside a zone) is ignored by the browser instead of navigating away
                dragover: e => e.preventDefault(),
                drop: e => e.preventDefault(),
            };
            for (const [type, fn] of Object.entries(this._listeners)) window.addEventListener(type, fn);
        },
        // Called by Alpine when the comparison mode is left (x-if removes the component)
        destroy() {
            for (const [type, fn] of Object.entries(this._listeners || {})) window.removeEventListener(type, fn);
            Object.keys(CHARTS).forEach(destroyChart);
        },

        /* ---------------- template helpers ---------------- */
        fmtSci, fmtPct, heatColor,

        /* ---------------- candidates ---------------- */
        // One candidate = one OPLA project file (lca_study.json from "Export project")
        newCandidate(project) {
            const id = this.nextId++;
            const c = {
                id, name: project.name, fu: project.fu, color: CANDIDATE_PALETTE[(id - 1) % CANDIDATE_PALETTE.length],
                active: true, summary: project.summary,
                midTotals: project.midTotals, endTotals: project.endTotals, midShares: project.midShares, endShares: project.endShares,
            };
            this.candidates.push(c);
            // return the reactive proxy, not the raw object, so later mutations are tracked
            return this.candidates[this.candidates.length - 1];
        },
        removeCandidate(c) {
            this.candidates = this.candidates.filter(x => x.id !== c.id);
            if (String(this.referenceId) === String(c.id)) this.referenceId = 'worst';
            if (this.heatSort === c.id) this.heatSort = null;
            this.afterChange();
        },
        move(c, dir) {
            const i = this.candidates.indexOf(c), j = i + dir;
            if (j < 0 || j >= this.candidates.length) return;
            const arr = this.candidates.slice();
            [arr[i], arr[j]] = [arr[j], arr[i]];
            this.candidates = arr;
            this.afterChange();
        },
        duplicateName(c) { return this.candidates.some(o => o.id !== c.id && norm(o.name) === norm(c.name)); },

        // Every dropped file becomes its own candidate; files that cannot be used are listed in dropNotices
        async onFiles(fileList) {
            const files = Array.from(fileList || []);
            if (!files.length) return;
            for (const f of files) {
                let text = '';
                try { text = await f.text(); } catch (e) { this.dropNotices.push('Could not read ' + f.name + '.'); continue; }
                this.ingestProject(f.name, text);
            }
            this.afterChange();
        },
        ingestProject(filename, text) {
            const res = parseProjectFile(filename, text);
            if (res.error) { this.dropNotices.push(res.error); return null; }
            return this.newCandidate(res.project);
        },
        clearDropNotices() { this.dropNotices = []; },
        summaryGroups(c) {
            const s = c.summary;
            if (!s) return [];
            return [
                { title: 'Materials', rows: s.materials || [] },
                { title: 'Processes', rows: s.processes || [] },
                { title: 'End-of-life routes', rows: s.eols || [] },
            ].filter(g => g.rows.length);
        },
        summaryAmount(r) { return r.amount === null ? '' : fmtSmart(r.amount) + (r.unit ? ' ' + r.unit : ''); },
        summaryLocations(c) {
            const s = c.summary;
            if (!s || (!s.productionLocation && !s.usageLocation)) return '–';
            return (s.productionLocation || '?') + ' → ' + (s.usageLocation || '?');
        },
        summaryCounts(c) {
            const s = c.summary;
            if (!s) return '';
            const n = (k, one, many) => (s[k] || []).length + ' ' + ((s[k] || []).length === 1 ? one : many);
            return [n('materials', 'material', 'materials'), n('processes', 'process', 'processes'), n('eols', 'EoL', 'EoL')].join(' · ');
        },
        isExpanded(c) { return this.expandedIds.includes(c.id); },
        toggleDetails(c) {
            this.expandedIds = this.isExpanded(c) ? this.expandedIds.filter(id => id !== c.id) : [...this.expandedIds, c.id];
        },
        hasData(c) { return !!(c.midTotals || c.endTotals); },

        /* ---------------- derived data ---------------- */
        active() { return this.candidates.filter(c => c.active && this.hasData(c)); },
        loaded() { return this.candidates.filter(c => this.hasData(c)); },
        totalsKey(level) { return level === 'midpoint' ? 'midTotals' : 'endTotals'; },
        sharesKey(level) { return level === 'midpoint' ? 'midShares' : 'endShares'; },
        categories(level) {
            const key = this.totalsKey(level), out = [];
            for (const c of this.candidates) for (const it of (c[key] || [])) if (!out.includes(it.impact)) out.push(it.impact);
            return out;
        },
        unitOf(level, cat) {
            const key = this.totalsKey(level);
            for (const c of this.candidates) { const it = (c[key] || []).find(i => i.impact === cat); if (it) return it.unit; }
            return '';
        },
        getValue(c, level, cat) {
            const it = (c[this.totalsKey(level)] || []).find(i => i.impact === cat);
            return it ? it.value : null;
        },
        referenceCandidate() { return this.candidates.find(c => String(c.id) === String(this.referenceId)) || null; },
        referenceLabel() { const r = this.referenceCandidate(); return r ? r.name : 'worst candidate per category'; },
        refValue(level, cat) {
            const ref = this.referenceCandidate();
            if (ref && ref.active && this.hasData(ref)) return this.getValue(ref, level, cat);
            const vals = this.active().map(c => this.getValue(c, level, cat)).filter(v => v !== null);
            if (!vals.length) return null;
            const mx = Math.max(...vals);
            return mx > 0 ? mx : Math.max(...vals.map(Math.abs));
        },
        relative(c, level, cat) {
            const v = this.getValue(c, level, cat), r = this.refValue(level, cat);
            if (v === null || r === null || r === 0) return null;
            return v / r * 100;
        },
        categoryOptions() {
            return [
                { group: 'Midpoint indicators', items: this.categories('midpoint').map(c => ({ key: 'midpoint::' + c, label: c })) },
                { group: 'Endpoint indicators', items: this.categories('endpoint').map(c => ({ key: 'endpoint::' + c, label: c })) },
            ];
        },
        splitKey(key) { const i = key.indexOf('::'); return i < 0 ? null : { level: key.slice(0, i), cat: key.slice(i + 2) }; },
        ensureSelections() {
            const opts = this.categoryOptions().flatMap(g => g.items).map(o => o.key);
            if (!opts.includes(this.absCategory)) this.absCategory = opts.find(k => /Climate change, short/i.test(k)) || opts[0] || '';
            if (!opts.includes(this.stackCategory)) this.stackCategory = opts.find(k => /Climate change, short/i.test(k)) || opts[0] || '';
            if (this.referenceId !== 'worst' && !this.candidates.some(c => String(c.id) === String(this.referenceId))) this.referenceId = 'worst';
        },
        breakdownFor(c, level, cat) {
            const sh = c[this.sharesKey(level)];
            const total = this.getValue(c, level, cat);
            if (!sh || total === null) return null;
            const idx = sh.categories.indexOf(cat);
            if (idx < 0) return null;
            return sh.contributors.map(k => ({ name: k.name, share: k.data[idx], value: total * k.data[idx] / 100 }));
        },
        contributorNames(level, cat) {
            const out = [];
            for (const c of this.active()) for (const b of (this.breakdownFor(c, level, cat) || [])) if (!out.includes(b.name)) out.push(b.name);
            return out;
        },

        /* ---------------- checks ---------------- */
        fuWarning() {
            const act = this.active();
            if (act.length < 2) return null;
            const fus = act.map(c => norm(c.fu));
            const distinct = [...new Set(fus.filter(f => f))];
            const missing = act.filter(c => !norm(c.fu)).map(c => c.name);
            if (distinct.length <= 1 && !missing.length) return null;
            const parts = [];
            if (distinct.length > 1) parts.push('The active candidates declare different functional units (' + act.filter(c => norm(c.fu)).map(c => c.name + ': "' + c.fu + '"').join('; ') + '). An LCA comparison is only meaningful when every candidate fulfils the same function; check that these are equivalent before drawing conclusions.');
            if (missing.length) parts.push('No functional unit recorded for: ' + missing.join(', ') + '. Set it in OPLA and export the project again, or type it on the candidate card, so the check can be made.');
            return parts;
        },
        coverageWarnings() {
            const out = [];
            const act = this.active();
            const midCats = this.categories('midpoint');
            for (const c of act) {
                const have = (c.midTotals || []).map(i => i.impact);
                const miss = midCats.filter(k => !have.includes(k));
                if (c.midTotals && miss.length) out.push(c.name + ' lacks ' + miss.length + ' midpoint categor' + (miss.length > 1 ? 'ies' : 'y') + ' present in other candidates (' + miss.slice(0, 3).join(', ') + (miss.length > 3 ? ', …' : '') + ').');
                if (!c.midTotals) out.push(c.name + ' has no midpoint results.');
                if (!c.endTotals) out.push(c.name + ' has no endpoint results.');
            }
            // Unit mismatch between candidates for the same category
            for (const level of ['midpoint', 'endpoint']) for (const cat of this.categories(level)) {
                const units = [...new Set(act.map(c => { const it = (c[this.totalsKey(level)] || []).find(i => i.impact === cat); return it ? norm(it.unit) : null; }).filter(u => u))];
                if (units.length > 1) out.push('Unit mismatch for "' + cat + '": ' + units.join(' vs ') + '.');
            }
            return out;
        },
        viewStatus(id) {
            const n = this.active().length;
            if (id === 'candidates') return this.candidates.length ? (this.loaded().length + ' loaded, ' + n + ' active') : 'nothing loaded yet';
            if (id === 'stacked') { const withB = this.active().filter(c => c.midShares || c.endShares).length; return n < 1 ? 'needs candidates' : (withB ? withB + ' with breakdown' : 'no breakdown'); }
            return n >= 2 ? 'ready' : (n === 1 ? 'needs 2+ candidates' : 'needs candidates');
        },
        viewStatusClass(id) { const s = this.viewStatus(id); return (s === 'ready' || /loaded|with breakdown/.test(s)) ? 'app__leftNav__steps__step__status--completed' : ''; },
        summaryWins() {
            // number of midpoint categories in which each candidate has the lowest value
            const act = this.active(), wins = {};
            act.forEach(c => wins[c.id] = 0);
            let counted = 0;
            for (const cat of this.categories('midpoint')) {
                const vals = act.map(c => ({ id: c.id, v: this.getValue(c, 'midpoint', cat) })).filter(x => x.v !== null);
                if (vals.length < 2) continue;
                counted++;
                const mn = Math.min(...vals.map(x => x.v));
                vals.filter(x => x.v === mn).forEach(x => wins[x.id]++);
            }
            return { wins, counted };
        },

        /* ---------------- navigation / rendering ---------------- */
        setView(id) { this.view = id; this.$nextTick(() => this.render()); },
        afterChange() { this.ensureSelections(); this.$nextTick(() => this.render()); },
        render() {
            this.ensureSelections();
            // selects whose options are rendered by x-for can lag behind the model value: re-sync them
            document.querySelectorAll('select[data-sync]').forEach(s => { s.value = String(this[s.dataset.sync]); });
            return queueRender(async () => {
                if (this.view === 'relative') await this.renderRelative();
                if (this.view === 'absolute') await this.renderAbsolute();
                if (this.view === 'radar') await this.renderRadar();
                if (this.view === 'stacked') await this.renderStacked();
            });
        },
        candidateSeriesMeta() { return this.active().map(c => ({ name: c.name, color: c.color })); },

        /* ----- View A: relative ----- */
        async renderRelative() {
            const act = this.active(), level = this.relLevel;
            const cats = this.categories(level);
            const el = document.getElementById('chart-relative');
            if (!el) return;
            if (act.length < 1 || !cats.length) { destroyChart('chart-relative'); el.innerHTML = ''; return; }
            const series = act.map(c => ({ name: c.name, data: cats.map(cat => { const r = this.relative(c, level, cat); return r === null ? null : +r.toFixed(2); }) }));
            const horizontal = this.relLayout === 'rows';
            const dense = act.length * cats.length > 30;
            const height = horizontal ? Math.max(360, 90 + cats.length * (act.length * 14 + 16)) : 520;
            // columns: keep bars readable (min ~7px each); a chart wider than the card scrolls horizontally inside it
            const minWidth = horizontal ? 0 : cats.length * Math.ceil(act.length * 7 / 0.7) + 140;
            const options = {
                chart: baseChart('bar', height, 'opla_relative_' + level),
                series, colors: act.map(c => c.color),
                plotOptions: { bar: { horizontal, columnWidth: '70%', barHeight: '75%', borderRadius: 2, borderRadiusApplication: 'end', dataLabels: { position: 'top' } } },
                dataLabels: { enabled: !dense, formatter: v => v === null ? '' : Number(v).toFixed(0), offsetY: horizontal ? 0 : -16, style: { fontSize: '11px', colors: ['#444'] }, background: { enabled: false } },
                stroke: { show: true, width: 1, colors: ['#fff'] },
                xaxis: horizontal
                    ? { title: { text: 'Impact relative to ' + this.referenceLabel() + ' (%)' }, labels: { formatter: v => Number(v).toFixed(0) + '%' }, categories: cats }
                    : { categories: cats, labels: { rotate: -45, rotateAlways: cats.length > 6, trim: true, hideOverlappingLabels: false, maxHeight: 160, style: { fontSize: '11px' }, formatter: v => shorten(v, 30) } },
                yaxis: horizontal
                    ? { labels: { style: { fontSize: '11px' }, maxWidth: 260, formatter: v => shorten(v, 34) } }
                    : { title: { text: 'Impact relative to ' + this.referenceLabel() + ' (%)' }, labels: { formatter: v => Number(v).toFixed(0) + '%' }, forceNiceScale: true },
                annotations: horizontal
                    ? { xaxis: [{ x: 100, borderColor: '#333', strokeDashArray: 4, label: { text: 'reference = 100%', orientation: 'horizontal', style: { background: '#333', color: '#fff', fontSize: '10px' } } }] }
                    : { yaxis: [{ y: 100, borderColor: '#333', strokeDashArray: 4, label: { text: 'reference = 100%', position: 'left', textAnchor: 'start', style: { background: '#333', color: '#fff', fontSize: '10px' } } }] },
                legend: { position: 'bottom', fontSize: '13px' },
                grid: { borderColor: '#eee' },
                tooltip: {
                    shared: true, intersect: false,
                    y: { formatter: (v, o) => {
                        const cat = cats[o.dataPointIndex], c = act[o.seriesIndex];
                        const abs = this.getValue(c, level, cat);
                        return v === null ? 'n/a' : Number(v).toFixed(1) + '%  (' + fmtSci(abs) + ' ' + this.unitOf(level, cat) + ')';
                    } },
                    x: { formatter: (v, o) => cats[o.dataPointIndex] || v }
                }
            };
            await mountChart('chart-relative', options, minWidth);
        },

        /* ----- View B: absolute ----- */
        async renderAbsolute() {
            const act = this.active();
            const main = document.getElementById('chart-absolute');
            if (!main) return;
            const sel = this.splitKey(this.absCategory);
            if (!act.length || !sel) { ['chart-absolute', 'chart-abs-end-0', 'chart-abs-end-1'].forEach(id => { destroyChart(id); const e = document.getElementById(id); if (e) e.innerHTML = ''; }); return; }
            const build = (level, cat, height, filename, showTitle) => {
                const unit = this.unitOf(level, cat);
                const values = act.map(c => this.getValue(c, level, cat));
                const opts = {
                    chart: baseChart('bar', height, filename),
                    series: [{ name: cat, data: values.map(v => v === null ? null : v) }],
                    colors: act.map(c => c.color),
                    plotOptions: { bar: { distributed: true, columnWidth: act.length > 6 ? '70%' : '45%', borderRadius: 3, borderRadiusApplication: 'end', dataLabels: { position: 'top' } } },
                    dataLabels: { enabled: true, formatter: v => v === null ? 'n/a' : fmtSci(v), offsetY: -18, style: { fontSize: '11px', colors: ['#333'] }, background: { enabled: false } },
                    legend: { show: false },
                    xaxis: { categories: act.map(c => c.name), labels: { trim: true, rotate: -30, rotateAlways: false, style: { fontSize: '12px' } } },
                    yaxis: { title: { text: unit }, labels: { formatter: v => fmtSmart(v) }, forceNiceScale: true },
                    grid: { borderColor: '#eee' },
                    tooltip: { y: { formatter: v => v === null ? 'n/a' : fmtSci(v) + ' ' + unit + ' (' + fmtSmart(v) + ')' } }
                };
                if (showTitle) opts.title = { text: cat, style: { fontSize: '14px', fontWeight: 600 } };
                return opts;
            };
            await mountChart('chart-absolute', build(sel.level, sel.cat, 420, 'opla_absolute', true));
            const ends = this.categories('endpoint');
            for (let i = 0; i < 2; i++) {
                const id = 'chart-abs-end-' + i, e = document.getElementById(id);
                if (!e) continue;
                if (ends[i]) await mountChart(id, build('endpoint', ends[i], 320, 'opla_endpoint_' + i, true));
                else { destroyChart(id); e.innerHTML = ''; }
            }
        },

        /* ----- View C: radar ----- */
        radarCategories() { return this.categories('midpoint').filter(c => !this.radarHidden.includes(c)); },
        toggleRadar(cat) { this.radarHidden = this.radarHidden.includes(cat) ? this.radarHidden.filter(c => c !== cat) : [...this.radarHidden, cat]; this.afterChange(); },
        radarAll(show) { this.radarHidden = show ? [] : this.categories('midpoint').slice(); this.afterChange(); },
        async renderRadar() {
            const act = this.active(), cats = this.radarCategories();
            const el = document.getElementById('chart-radar');
            if (!el) return;
            if (act.length < 1 || cats.length < 3) { destroyChart('chart-radar'); el.innerHTML = ''; return; }
            const series = act.map(c => ({ name: c.name, data: cats.map(cat => { const r = this.relative(c, 'midpoint', cat); return r === null ? 0 : +r.toFixed(2); }) }));
            const options = {
                chart: baseChart('radar', 640, 'opla_radar', { dropShadow: { enabled: false } }),
                series, colors: act.map(c => c.color),
                stroke: { width: 2 }, fill: { opacity: 0.12 }, markers: { size: 3, hover: { size: 5 } },
                xaxis: { categories: cats.map(c => shorten(c, 32)), labels: { style: { fontSize: '11px', colors: cats.map(() => '#444') } } },
                yaxis: { show: false, min: 0, tickAmount: 4 },
                plotOptions: { radar: { size: 210, polygons: { strokeColors: '#e5e5e5', connectorColors: '#e5e5e5', fill: { colors: ['#fafafa', '#fff'] } } } },
                legend: { position: 'bottom', fontSize: '13px' },
                tooltip: { y: { formatter: (v, o) => { const cat = cats[o.dataPointIndex]; const abs = this.getValue(act[o.seriesIndex], 'midpoint', cat); return Number(v).toFixed(1) + '% of ' + this.referenceLabel() + ' (' + fmtSci(abs) + ' ' + this.unitOf('midpoint', cat) + ')'; } },
                          x: { formatter: (v, o) => cats[o.dataPointIndex] || v } }
            };
            await mountChart('chart-radar', options);
        },

        /* ----- View D: heatmap table ----- */
        heatRows(level) {
            const act = this.active();
            const rows = this.categories(level).map(cat => {
                const vals = act.map(c => this.getValue(c, level, cat));
                const finite = vals.filter(v => v !== null);
                const mn = finite.length ? Math.min(...finite) : null, mx = finite.length ? Math.max(...finite) : null;
                return {
                    cat, unit: this.unitOf(level, cat),
                    cells: act.map((c, i) => {
                        const v = vals[i];
                        const t = (v === null || mn === null || mx === mn) ? null : (v - mn) / (mx - mn);
                        return { v, rel: this.relative(c, level, cat), t, best: v !== null && v === mn && finite.length > 1, worst: v !== null && v === mx && finite.length > 1 };
                    })
                };
            });
            if (this.heatSort !== null) {
                const idx = act.findIndex(c => c.id === this.heatSort);
                if (idx >= 0) rows.sort((a, b) => ((b.cells[idx].rel ?? -Infinity) - (a.cells[idx].rel ?? -Infinity)));
            }
            return rows;
        },
        heatAllRows() {
            const out = [];
            for (const level of ['midpoint', 'endpoint']) {
                const rows = this.heatRows(level);
                if (!rows.length) continue;
                out.push({ type: 'group', key: 'g-' + level, level, label: level === 'midpoint' ? 'Midpoint indicators' : 'Endpoint indicators', unit: '', cells: [] });
                rows.forEach(r => out.push({ type: 'row', key: level + '-' + r.cat, level, label: r.cat, unit: r.unit, cells: r.cells }));
            }
            return out;
        },
        sortBy(c) { this.heatSort = this.heatSort === c.id ? null : c.id; },

        /* ----- View E: stacked contributions ----- */
        async renderStacked() {
            const act = this.active();
            const el = document.getElementById('chart-stacked');
            if (!el) return;
            const sel = this.splitKey(this.stackCategory);
            if (!act.length || !sel) { destroyChart('chart-stacked'); el.innerHTML = ''; return; }
            const { level, cat } = sel;
            const unit = this.unitOf(level, cat);
            const names = this.contributorNames(level, cat);
            const breakdowns = act.map(c => this.breakdownFor(c, level, cat));
            const series = names.map((n, k) => ({
                name: n, color: CONTRIBUTOR_PALETTE[k % CONTRIBUTOR_PALETTE.length],
                data: breakdowns.map(b => { if (!b) return 0; const hit = b.find(x => x.name === n); return hit ? +hit.value.toPrecision(6) : 0; })
            }));
            const anyMissing = breakdowns.some(b => !b);
            if (anyMissing) series.push({ name: 'Total (no breakdown loaded)', color: NO_BREAKDOWN_COLOR, data: breakdowns.map((b, i) => b ? 0 : (this.getValue(act[i], level, cat) ?? 0)) });
            const percent = this.stackMode === 'percent';
            // ApexCharts' automatic scale misbehaves with very small numbers (e.g. DALY ~1e-5), so set the axis range explicitly
            const posTot = act.map((_, i) => series.reduce((a, s) => a + Math.max(0, s.data[i] || 0), 0));
            const negTot = act.map((_, i) => series.reduce((a, s) => a + Math.min(0, s.data[i] || 0), 0));
            const yMax = Math.max(0, ...posTot), yMin = Math.min(0, ...negTot);
            const span = (yMax - yMin) * 1.08 || 1;
            const mag = Math.pow(10, Math.floor(Math.log10(span / 6)));
            const step = [1, 2, 5, 10].map(m => m * mag).find(st => span / st <= 7) || mag * 10;
            const nMax = yMax > 0 ? Math.ceil(yMax * 1.08 / step) * step : 0;
            const nMin = yMin < 0 ? Math.floor(yMin * 1.08 / step) * step : 0;
            const yRange = percent ? {} : { min: nMin, max: nMax || step, tickAmount: Math.round(((nMax || step) - nMin) / step), forceNiceScale: false };
            const options = {
                chart: baseChart('bar', 500, 'opla_stacked', { stacked: true, stackType: percent ? '100%' : 'normal' }),
                series, colors: series.map(s => s.color),
                plotOptions: { bar: { columnWidth: act.length > 6 ? '70%' : '50%', borderRadius: 2, borderRadiusApplication: 'end', borderRadiusWhenStacked: 'last' } },
                stroke: { show: true, width: 2, colors: ['#fff'] },
                dataLabels: {
                    enabled: true, style: { fontSize: '11px', colors: ['#fff'] }, dropShadow: { enabled: false },
                    formatter: (v, o) => {
                        let p;
                        if (percent) { const sp = o.w.globals.seriesPercent; p = sp && sp[o.seriesIndex] ? sp[o.seriesIndex][o.dataPointIndex] : 0; }
                        else { const totals = o.w.globals.stackedSeriesTotals || []; const tot = totals[o.dataPointIndex] || 0; p = tot ? v / tot * 100 : 0; }
                        if (!Number.isFinite(p) || Math.abs(p) < 7) return '';
                        return percent ? p.toFixed(0) + '%' : fmtSmart(v);
                    }
                },
                xaxis: { categories: act.map(c => c.name), labels: { trim: true, style: { fontSize: '12px' } } },
                yaxis: Object.assign({ title: { text: percent ? 'Share of total (%)' : unit }, labels: { formatter: v => percent ? Number(v).toFixed(0) + '%' : fmtSmart(v) } }, yRange),
                legend: { position: 'bottom', fontSize: '12px' },
                grid: { borderColor: '#eee' },
                tooltip: { shared: false, intersect: true, y: { formatter: (v, o) => {
                    const sp = o.w.globals.seriesPercent; const p = sp && sp[o.seriesIndex] ? sp[o.seriesIndex][o.dataPointIndex] : null;
                    return fmtSci(v) + ' ' + unit + (Number.isFinite(p) ? ' (' + p.toFixed(1) + '% of total)' : '');
                } } }
            };
            await mountChart('chart-stacked', options);
        },
        stackedTable() {
            const sel = this.splitKey(this.stackCategory);
            if (!sel) return null;
            const act = this.active();
            const names = this.contributorNames(sel.level, sel.cat);
            return { unit: this.unitOf(sel.level, sel.cat), names, rows: act.map(c => ({ cand: c, total: this.getValue(c, sel.level, sel.cat), b: this.breakdownFor(c, sel.level, sel.cat) })) };
        },

        /* ---------------- session save / load ---------------- */
        saveSession() {
            const data = {
                app: 'opla-compare', version: APP_VERSION, saved: new Date().toISOString(),
                settings: { referenceId: this.referenceId, relLevel: this.relLevel, relLayout: this.relLayout, absCategory: this.absCategory, stackCategory: this.stackCategory, stackMode: this.stackMode, radarHidden: this.radarHidden, view: this.view },
                nextId: this.nextId,
                candidates: this.candidates.map(c => JSON.parse(JSON.stringify(c)))
            };
            download('opla_comparison.json', JSON.stringify(data, null, 2), 'application/json');
        },
        loadSession() {
            const input = document.createElement('input');
            input.type = 'file'; input.accept = 'application/json,.json';
            input.onchange = async e => {
                const f = e.target.files[0]; if (!f) return;
                try {
                    const data = JSON.parse(await f.text());
                    if (data.app !== 'opla-compare' || !Array.isArray(data.candidates)) throw new Error('This is not an OPLA comparison file. To add a single OPLA project, drop its lca_study.json on the drop zone of the Candidates step.');
                    // older sessions stored `meta`, `files` and `notices`; they are dropped
                    this.candidates = data.candidates.map(({ meta, files, notices, ...c }) => ({ summary: null, midTotals: null, endTotals: null, midShares: null, endShares: null, active: true, ...c }));
                    this.nextId = Math.max(data.nextId || 1, ...this.candidates.map(c => c.id + 1), 1);
                    Object.assign(this, data.settings || {});
                    if (!this.views.some(v => v.id === this.view)) this.view = 'candidates';
                    this.afterChange();
                } catch (err) { this.modal = { title: 'Could not load comparison', text: String(err.message || err) }; }
            };
            input.click();
        },
        clearAll() { this.modal = { title: 'Remove all candidates?', text: 'This clears every candidate from the comparison. Save the comparison first if you want to come back to it.', confirm: () => { this.candidates = []; this.referenceId = 'worst'; this.heatSort = null; this.modal = null; this.afterChange(); } }; },

        /* ---------------- exports ---------------- */
        exportTableCSV() {
            const act = this.active();
            if (!act.length) { this.modal = { title: 'Nothing to export', text: 'Load at least one candidate with results first.' }; return; }
            const rows = [];
            rows.push(['OPLA Results Comparator ' + APP_VERSION, 'exported ' + new Date().toISOString()]);
            rows.push(['Reference for relative values', this.referenceLabel()]);
            rows.push([]);
            rows.push(['Candidate', 'Functional unit', 'Production location', 'Usage location']);
            act.forEach(c => rows.push([c.name, c.fu, c.summary ? c.summary.productionLocation : '', c.summary ? c.summary.usageLocation : '']));
            rows.push([]);
            for (const level of ['midpoint', 'endpoint']) {
                rows.push([level === 'midpoint' ? 'MIDPOINT INDICATORS' : 'ENDPOINT INDICATORS']);
                rows.push(['Impact category', 'Unit', ...act.map(c => c.name), ...act.map(c => c.name + ' (% of reference)')]);
                for (const cat of this.categories(level)) {
                    rows.push([cat, this.unitOf(level, cat), ...act.map(c => { const v = this.getValue(c, level, cat); return v === null ? '' : fmtSci(v); }), ...act.map(c => { const r = this.relative(c, level, cat); return r === null ? '' : r.toFixed(2); })]);
                }
                rows.push([]);
            }
            // Contribution breakdown, absolute values, when available
            const withB = act.filter(c => c.midShares || c.endShares);
            if (withB.length) {
                rows.push(['CONTRIBUTION BREAKDOWN (absolute values = total x share)']);
                rows.push(['Level', 'Impact category', 'Unit', 'Candidate', 'Contributor', 'Share (%)', 'Value']);
                for (const level of ['midpoint', 'endpoint']) for (const cat of this.categories(level)) for (const c of withB) {
                    for (const b of (this.breakdownFor(c, level, cat) || [])) rows.push([level, cat, this.unitOf(level, cat), c.name, b.name, b.share, fmtSci(b.value)]);
                }
            }
            download('opla_comparison_table.csv', rows.map(r => r.map(csvEscape).join(',')).join('\n'), 'text/csv;charset=utf-8');
        },
    }));
});

})();
