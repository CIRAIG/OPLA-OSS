"""
PropyleneProcess Class - Propylene Production Orchestrator
----------------------------------------------------------------------

This class is a system-level orchestrator that combines three propylene
production pathways into a unified model with configurable production shares:

1. Steam Cracking (SC) - Propylene as co-product (PropyleneSCProcess)
2. Fluid Catalytic Cracking (FCC) - High-severity mode (FCCProcess)
3. Propane Dehydrogenation (PDH) - On-purpose production (PDHProcess)
   - PDH is anchored to ecoinvent v3.10.1 UPR with two scalars

Production System Overview:

    [α_sc]  Steam Cracking  ──────────────────┐
            (Mixed feedstocks → Propylene)    │
                                               │
    [α_fcc] Fluid Catalytic Cracking ─────────┼──→ [Propylene Mix]
            (VGO → Propylene)                 │     (1 kg total)
                                               │
    [α_pdh] Propane Dehydrogenation ──────────┘
            (Propane → Propylene)
            ecoinvent v3.10.1 UPR baseline

Mathematical Model:
-------------------

1. Production share allocation:
   α_sc + α_fcc + α_pdh = 1.0 (auto-normalized)

2. Aggregated flows:
   m_input_total = Σ(α_i × m_input_i)

Key Features:
- Flexible production mix allocation (α_sc, α_fcc, α_pdh)
- Full parameter pass-through to each subprocess (sc_*, fcc_*, pdh_*)
- Unified LCI output for downstream use
- Technosphere inputs aggregated; direct emissions handled downstream
  (FCC has emission_flows from coke combustion; PDH and SC do not)

Quick Start:
-----------
1. See ALL available parameters:
   >>> PropyleneProcess.show_parameters()

2. Create your model (flat parameter interface):
   >>> pp = PropyleneProcess(
   ...     alpha_sc=0.40,
   ...     alpha_fcc=0.25,
   ...     alpha_pdh=0.35,
   ...     sc_f_naphtha=0.8,
   ...     pdh_Y_selectivity=1.05
   ... )

3. View your current settings:
   >>> pp.print_current_parameters()
"""

from propylene_sc_process import PropyleneSCProcess
from fcc_process import FCCProcess
from pdh_process import PDHProcess


class PropyleneProcess:
    """
    Propylene Production Orchestrator

    Combines Steam Cracking, FCC, and PDH routes with configurable
    production shares for unified LCI modeling.
    """

    @staticmethod
    def show_parameters(detailed=True):
        """
        Display ALL available parameters across the entire propylene system
        """
        print("="*80)
        print("COMPLETE PARAMETER REFERENCE FOR PropyleneProcess")
        print("="*80)
        print("\nThis orchestrator combines three propylene production routes.")
        print("Use prefixes to organize parameters by subprocess:")
        print("  • alpha_* = Production share allocation")
        print("  • sc_*    = Steam Cracking parameters")
        print("  • fcc_*   = Fluid Catalytic Cracking parameters")
        print("  • pdh_*   = Propane Dehydrogenation parameters")
        print("="*80)

        if detailed:
            # Production shares
            print("\n" + "PRODUCTION SHARES (auto-normalized)".center(80, "-"))
            share_params = [
                ("alpha_sc", "Share from Steam Cracking", 0.40),
                ("alpha_fcc", "Share from FCC", 0.25),
                ("alpha_pdh", "Share from PDH", 0.35),
            ]
            for name, desc, default in share_params:
                print(f"  {name:20s} : {desc:40s} [{default}]")

            # Steam Cracking
            print("\n" + "STEAM CRACKING (prefix: sc_)".center(80, "-"))
            print("  Wraps SteamCrackerProcess with propylene as reference product")
            sc_params = [
                ("sc_f_butane", "Butane feedstock share", 0.028),
                ("sc_f_ethane", "Ethane feedstock share", 0.756),
                ("sc_f_naphtha", "Naphtha feedstock share", 0.061),
                ("sc_f_propane", "Propane feedstock share", 0.154),
                ("sc_thermal_eff", "Thermal efficiency", 0.89),
            ]
            for name, desc, default in sc_params:
                print(f"  {name:20s} : {desc:40s} [{default}]")
            print("  ... see PropyleneSCProcess.show_parameters() for full list")

            # FCC
            print("\n" + "FLUID CATALYTIC CRACKING (prefix: fcc_)".center(80, "-"))
            print("  High-Severity FCC (Petrochemical Mode)")
            fcc_params = [
                ("fcc_Y_propylene", "Propylene yield scalar", 1.0),
                ("fcc_Y_ethylene", "Ethylene yield scalar", 1.0),
                ("fcc_Y_butylenes", "Butylenes yield scalar", 1.0),
                ("fcc_f_zsm5", "ZSM-5 additive fraction", 0.08),
            ]
            for name, desc, default in fcc_params:
                print(f"  {name:20s} : {desc:40s} [{default}]")
            print("  ... see FCCProcess.show_parameters() for full list")

            # PDH
            print("\n" + "PROPANE DEHYDROGENATION (prefix: pdh_)".center(80, "-"))
            print("  ecoinvent v3.10.1 UPR-anchored (single-output, no emissions)")
            pdh_params = [
                ("pdh_Y_selectivity", "Selectivity scalar (>1 = less propane)", 1.0),
                ("pdh_eta_energy", "Energy efficiency scalar (>1 = less energy)", 1.0),
            ]
            for name, desc, default in pdh_params:
                print(f"  {name:20s} : {desc:40s} [{default}]")
            print("  ... see PDHProcess.show_parameters() for full list")
        else:
            print("\nShares: alpha_sc, alpha_fcc, alpha_pdh")
            print("SC:     sc_f_butane, sc_f_ethane, sc_f_naphtha, sc_thermal_eff, ...")
            print("FCC:    fcc_Y_propylene, fcc_Y_ethylene, fcc_Y_butylenes, fcc_f_zsm5, ...")
            print("PDH:    pdh_Y_selectivity, pdh_eta_energy")

        print("\n" + "="*80)
        print("USAGE EXAMPLES:")
        print("="*80)
        print("""
# Example 1: Default production mix
pp = PropyleneProcess()  # 40% SC, 25% FCC, 35% PDH

# Example 2: PDH-heavy with improved selectivity
pp = PropyleneProcess(
    alpha_sc=0.20,
    alpha_fcc=0.15,
    alpha_pdh=0.65,
    pdh_Y_selectivity=1.05,
    pdh_eta_energy=1.10
)

# Example 3: Naphtha-heavy SC with improved FCC
pp = PropyleneProcess(
    alpha_sc=0.50,
    alpha_fcc=0.30,
    alpha_pdh=0.20,
    sc_f_naphtha=0.8,
    sc_f_ethane=0.2,
    fcc_Y_propylene=1.10,
    fcc_f_zsm5=0.12
)

# Example 4: Pass pre-built process objects
sc = PropyleneSCProcess(sc_f_naphtha=0.9)
pdh = PDHProcess(Y_selectivity=1.05)
pp = PropyleneProcess(
    sc_process=sc,
    pdh_process=pdh,
    alpha_sc=0.30,
    alpha_pdh=0.70,
    alpha_fcc=0.0  # No FCC
)
        """)
        print("="*80)

    @staticmethod
    def get_parameter_template(format='dict'):
        """
        Get a complete template showing ALL parameters and their defaults
        """
        template = {
            # Production shares
            'alpha_sc': 0.40,
            'alpha_fcc': 0.25,
            'alpha_pdh': 0.35,
            # Steam Cracking parameters (sc_*)
            'sc_f_butane': 0.028,
            'sc_f_ethane': 0.756,
            'sc_f_gasoil': 0.001,
            'sc_f_naphtha': 0.061,
            'sc_f_propane': 0.154,
            'sc_f_h2_combusted': 0.7,
            'sc_f_ch4_combusted': 1.0,
            'sc_thermal_eff': 0.89,
            # FCC parameters (fcc_*)
            'fcc_Y_propylene': 1.0,
            'fcc_Y_ethylene': 1.0,
            'fcc_Y_butylenes': 1.0,
            'fcc_f_zsm5': 0.08,
            'fcc_T_riser': 600.0,
            'fcc_T_regen': 720.0,
            'fcc_T_feed_preheat': 280.0,
            # PDH parameters (pdh_*)
            'pdh_Y_selectivity': 1.0,
            'pdh_eta_energy': 1.0,
        }

        if format == 'dict':
            return template
        elif format == 'json':
            import json
            return json.dumps(template, indent=2)
        else:
            return template

    @staticmethod
    def list_parameters():
        """Quick list of ALL parameter names with prefixes"""
        return list(PropyleneProcess.get_parameter_template().keys())

    def print_current_parameters(self):
        """Display the current parameter values across all subprocesses"""
        print("="*80)
        print("CURRENT PROPYLENE PROCESS PARAMETERS")
        print("="*80)

        # Production shares
        print("\n" + "PRODUCTION SHARES".center(80, "-"))
        print(f"  alpha_sc  = {self.alpha_sc:.4f} ({self.alpha_sc*100:.1f}%)")
        print(f"  alpha_fcc = {self.alpha_fcc:.4f} ({self.alpha_fcc*100:.1f}%)")
        print(f"  alpha_pdh = {self.alpha_pdh:.4f} ({self.alpha_pdh*100:.1f}%)")

        # Steam Cracking summary
        if self.sc is not None and self.alpha_sc > 0:
            print("\n" + "STEAM CRACKING (SC)".center(80, "-"))
            print(f"  Feed mix: naphtha={self.sc.steam_cracker.f_naphtha_share_cracking:.2%}, "
                  f"ethane={self.sc.steam_cracker.f_ethane_share_cracking:.2%}, "
                  f"propane={self.sc.steam_cracker.f_propane_share_cracking:.2%}")
            print(f"  Thermal efficiency = {self.sc.steam_cracker.thermal_efficiency_cracker:.4f}")
            print(f"  Feed per kg propylene = {self.sc.m_feed_total:.4f} kg")
            print(f"  Ethylene co-product = {self.sc.m_ethylene_coproduct:.4f} kg/kg propylene")
        elif self.alpha_sc > 0:
            print("\n  SC route: alpha > 0 but no process built")
        else:
            print("\n  SC route not active (alpha_sc = 0)")

        # FCC summary
        if self.fcc is not None and self.alpha_fcc > 0:
            print("\n" + "FLUID CATALYTIC CRACKING (FCC)".center(80, "-"))
            print(f"  Propylene yield = {self.fcc.y_propylene:.4f} kg/kg VGO")
            print(f"  ZSM-5 fraction = {self.fcc.f_zsm5:.4f}")
            print(f"  VGO per kg propylene = {self.fcc.m_vgo:.4f} kg")
            print(f"  Allocated CO2 = {self.fcc.allocated_CO2_total:.4f} kg/kg {self.fcc.reference_product}")
            print(f"  Allocated electricity = {self.fcc.allocated_elec_kWh:.4f} kWh/kg {self.fcc.reference_product}")
        elif self.alpha_fcc > 0:
            print("\n  FCC route: alpha > 0 but no process built")
        else:
            print("\n  FCC route not active (alpha_fcc = 0)")

        # PDH summary
        if self.pdh is not None and self.alpha_pdh > 0:
            print("\n" + "PROPANE DEHYDROGENATION (PDH)".center(80, "-"))
            print(f"  Anchored to ecoinvent v3.10.1 UPR (single-output, no emissions)")
            print(f"  Y_selectivity = {self.pdh.Y_selectivity:.4f}  (1.0 = ecoinvent baseline)")
            print(f"  eta_energy    = {self.pdh.eta_energy:.4f}  (1.0 = ecoinvent baseline)")
            print(f"  Propane per kg propylene = {self.pdh.m_propane:.4f} kg")
            print(f"  Steam (heat)             = {self.pdh.E_steam:.4f} MJ")
            print(f"  Electricity              = {self.pdh.E_electricity:.4f} kWh")
            print(f"  Natural gas              = {self.pdh.E_ng:.6f} m3")
        elif self.alpha_pdh > 0:
            print("\n  PDH route: alpha > 0 but no process built")
        else:
            print("\n  PDH route not active (alpha_pdh = 0)")

        # Aggregated results
        print("\n" + "AGGREGATED LCI FLOWS (per kg propylene)".center(80, "-"))
        print("  Input flows:")
        for flow, val in sorted(self.input_flows.items(), key=lambda x: -x[1]):
            if val > 1e-8:
                print(f"    {flow:55s} = {val:.6f}")
        print("  Output flows:")
        for flow, val in self.output_flows.items():
            if val > 1e-8:
                print(f"    {flow:55s} = {val:.6f}")
        if self.emission_flows:
            print("  Emission flows:")
            for flow, val in self.emission_flows.items():
                if val > 1e-8:
                    print(f"    {flow:55s} = {val:.6f}")

        print("="*80)

    def __init__(
        self,
        # Pre-built process instances (optional)
        sc_process: PropyleneSCProcess | None = None,
        fcc_process: FCCProcess | None = None,
        pdh_process: PDHProcess | None = None,
        # Production shares
        alpha_sc: float = 0.40,
        alpha_fcc: float = 0.25,
        alpha_pdh: float = 0.35,
        **params  # Flat parameter interface (sc_*, fcc_*, pdh_*)
    ):
        """
        Create a propylene production orchestrator

        To see all available parameters, run:
            PropyleneProcess.show_parameters()

        Args:
            sc_process: Pre-built PropyleneSCProcess (optional)
            fcc_process: Pre-built FCCProcess (optional)
            pdh_process: Pre-built PDHProcess (optional)
            alpha_sc: Production share from Steam Cracking (0-1)
            alpha_fcc: Production share from FCC (0-1)
            alpha_pdh: Production share from PDH (0-1)
            **params: Parameters with prefixes (sc_*, fcc_*, pdh_*)
        """

        # Reference product: 1 kg propylene
        self.m_propylene_ref = 1.0

        # Normalize production shares
        total_share = alpha_sc + alpha_fcc + alpha_pdh
        if total_share <= 0:
            raise ValueError("Production shares must sum to a positive value")

        self.alpha_sc = alpha_sc / total_share
        self.alpha_fcc = alpha_fcc / total_share
        self.alpha_pdh = alpha_pdh / total_share

        # Extract parameters by prefix
        sc_params = self._extract_params(params, 'sc_')
        fcc_params = self._extract_params(params, 'fcc_')
        pdh_params = self._extract_params(params, 'pdh_')

        # Check for unknown parameters
        known_prefixes = {'sc_', 'fcc_', 'pdh_', 'alpha_'}
        for key in params.keys():
            if not any(key.startswith(prefix) for prefix in known_prefixes):
                print(f"Warning: Unknown parameter '{key}'")
                print(f"   Valid prefixes: sc_, fcc_, pdh_")

        # ========== BUILD SUBPROCESSES ==========

        # Steam Cracking
        if sc_process is not None:
            self.sc = sc_process
        elif self.alpha_sc > 0:
            # Add sc_ prefix back for PropyleneSCProcess
            sc_kwargs = {f'sc_{k}': v for k, v in sc_params.items()}
            self.sc = PropyleneSCProcess(**sc_kwargs)
        else:
            self.sc = None

        # FCC
        if fcc_process is not None:
            self.fcc = fcc_process
        elif self.alpha_fcc > 0:
            self.fcc = FCCProcess(**fcc_params)
        else:
            self.fcc = None

        # PDH (ecoinvent-anchored: Y_selectivity, eta_energy)
        if pdh_process is not None:
            self.pdh = pdh_process
        elif self.alpha_pdh > 0:
            self.pdh = PDHProcess(**pdh_params)
        else:
            self.pdh = None

        # ========== AGGREGATE LCI FLOWS ==========
        self.input_flows = {}
        self.output_flows = {'propylene': self.m_propylene_ref}
        self.emission_flows = {}

        # Aggregate from SC
        if self.sc is not None and self.alpha_sc > 0:
            self._add_weighted_flows(self.input_flows, self.sc.input_flows, self.alpha_sc)
            sc_outputs = {k: v for k, v in self.sc.output_flows.items() if k != 'propylene'}
            self._add_weighted_flows(self.output_flows, sc_outputs, self.alpha_sc)

        # Aggregate from FCC
        if self.fcc is not None and self.alpha_fcc > 0:
            self._add_weighted_flows(self.input_flows, self.fcc.input_flows, self.alpha_fcc)
            fcc_outputs = {k: v for k, v in self.fcc.output_flows.items() if k != 'propylene'}
            self._add_weighted_flows(self.output_flows, fcc_outputs, self.alpha_fcc)
            if hasattr(self.fcc, 'emission_flows'):
                self._add_weighted_flows(self.emission_flows, self.fcc.emission_flows, self.alpha_fcc)

        # Aggregate from PDH
        # PDH (ecoinvent-anchored) has input_flows and output_flows only — no emission_flows.
        if self.pdh is not None and self.alpha_pdh > 0:
            self._add_weighted_flows(self.input_flows, self.pdh.input_flows, self.alpha_pdh)
            pdh_outputs = {k: v for k, v in self.pdh.output_flows.items() if k != 'propylene'}
            self._add_weighted_flows(self.output_flows, pdh_outputs, self.alpha_pdh)
            # PDH has no emission_flows (direct emissions handled downstream)

    @staticmethod
    def _extract_params(params: dict, prefix: str) -> dict:
        """
        Extract parameters with a specific prefix and strip the prefix.
        """
        extracted = {}
        for key, value in params.items():
            if key.startswith(prefix):
                clean_key = key[len(prefix):]
                extracted[clean_key] = value
        return extracted

    @staticmethod
    def _add_weighted_flows(target: dict, flows: dict, weight: float):
        """Add weighted flows to target dictionary"""
        for k, v in flows.items():
            if isinstance(v, (int, float)):
                target[k] = target.get(k, 0.0) + v * weight

    def to_dict(self):
        """Export complete parameter set and flows for LCA integration"""
        result = {
            "parameters": {
                "production_shares": {
                    "alpha_sc": self.alpha_sc,
                    "alpha_fcc": self.alpha_fcc,
                    "alpha_pdh": self.alpha_pdh,
                },
            },
            "input_flows": self.input_flows,
            "output_flows": self.output_flows,
            "emission_flows": self.emission_flows,
        }

        # Add subprocess parameters if active
        if self.sc is not None:
            result["parameters"]["steam_cracking"] = self.sc.to_dict()["parameters"]
        if self.fcc is not None:
            result["parameters"]["fcc"] = self.fcc.to_dict()["parameters"]
        if self.pdh is not None:
            result["parameters"]["pdh"] = self.pdh.to_dict()["parameters"]

        return result

    def scenario_comparison(self, scenarios: dict):
        """
        Compare different production mix scenarios

        Args:
            scenarios: Dict of scenario names to (alpha_sc, alpha_fcc, alpha_pdh) tuples

        Returns:
            dict: Comparison of key metrics for each scenario
        """
        results = {}

        for name, (a_sc, a_fcc, a_pdh) in scenarios.items():
            scenario = PropyleneProcess(
                alpha_sc=a_sc,
                alpha_fcc=a_fcc,
                alpha_pdh=a_pdh
            )

            # Derive metrics from aggregated flow dicts
            elec = scenario.input_flows.get('electricity, medium voltage', 0.0)
            co2 = scenario.emission_flows.get('Carbon dioxide, fossil', 0.0)

            # Thermal: sum of all heat-type flows
            thermal = 0.0
            for k, v in scenario.input_flows.items():
                if 'heat' in k.lower() or 'steam' in k.lower():
                    thermal += v

            results[name] = {
                'shares': (scenario.alpha_sc, scenario.alpha_fcc, scenario.alpha_pdh),
                'electricity_kWh': elec,
                'thermal_MJ': thermal,
                'CO2_kg': co2,
            }

        return results
