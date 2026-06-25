# Parametrized Process Modules (OSS)

Open-source, standalone parametric process models for life-cycle inventory work.
Each module models one production step and exposes tuneable parameters
(yields, efficiencies, route shares, feedstock mixes).

## What is it ?

The Parametrized Process Modules are a set of standalone Python models, one per production step in the petrochemical and bio-based polymer value chains: steam cracking, fluid catalytic cracking (FCC), propane dehydrogenation (PDH), propylene production, ethylene glycol (EG) production, terephthalic acid (TPA) production, and bioethanol production. Each module represents the foreground inventory of its process for a fixed reference output (e.g. 1 kg of product) and exposes the key technological levers as adjustable parameters: feedstock mix, conversion yields, energy efficiencies, allocation method, and route shares. Changing a parameter rescales the corresponding material and energy flows, so a user can explore alternative process configurations without rebuilding the inventory by hand.

The modules are designed to sit on top of background databases (ecoinvent) rather than replace them: they compute the process-specific exchanges and hand them off to the LCA model using ecoinvent-compatible flow names. Where a module relies on ecoinvent baseline values (PDH, EG, TPA, and bioethanol), those few data points are clearly marked in the code as dummy placeholders and annotated with the exact ecoinvent v3.10.1 activity they correspond to, so anyone holding an ecoinvent license can drop in the real numbers. The remaining parameters (steam-cracker yields, FCC heat balances, prices) come from open literature and are included as-is.

## ecoinvent data: what's real and what's dummy

Some modules are anchored to **ecoinvent v3.10.1** background data, which is
licensed and cannot be redistributed. In those modules the ecoinvent-derived
numbers have been **replaced with clearly-labelled dummy (placeholder) values**
so the code is fully open-source and runs out of the box. **The numbers these
modules produce are therefore NOT real LCA results** until you substitute real
ecoinvent values.

| Module | ecoinvent data? | Where the dummy data is |
|---|---|---|
| `steam_cracking_process.py` | No — Ullmann's Encyclopedia (literature) | — |
| `fcc_process.py` | No — Sadeghbeigi / Maadhah (literature) | — |
| `propylene_process.py` | No — orchestration only | — |
| `pdh_process.py` | **Yes** | `BASELINE_*` constants in `PDHProcess` |
| `eg_process.py` | **Yes** | `M_ETH_PER_EO_ORIG`, `M_EO_PER_EG_ORIG` in `EGProcess` |
| `tpa_process.py` | **Yes** | six `*_ORIG` constants in `TPAProcess` |
| `bioethanol_production_process.py` | **Yes** | `original_heat_demand`, `original_mass_demand` dicts |

## How to find and replace the dummy data

Every placeholder is marked in the code. To locate all of it:

```bash
grep -rn "DUMMY" .
```

Each dummy block names the exact **ecoinvent v3.10.1** activity (and, where
known, the UPR UUID and geography) it stands in for, plus the unit. To
reproduce real results, open your licensed ecoinvent database, look up that
activity, and replace each `# DUMMY` value with the real amount. No scripts,
Brightway, or external files are needed — the data points are few and live
directly in the code.

The feedstock-share defaults in `bioethanol_production_process.py`
(`f_ethanol_*`) are **scenario assumptions, not ecoinvent data**, and are left
at their real values.

## Dependencies between modules

- `eg_process.py` imports `steam_cracking_process.py` (included).
- `propylene_process.py` imports `pdh_process.py`, `fcc_process.py`, and
  **`propylene_sc_process.py`** — the last is *not* in this folder. Add it
  (it contains no ecoinvent data) if you need `propylene_process.py` to run.
- `pdh_process.py`, `tpa_process.py`, `bioethanol_production_process.py` are
  self-contained.

No third-party packages are required (Python 3 standard library only).
