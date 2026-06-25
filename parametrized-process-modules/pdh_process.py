"""
PDHProcess Class - Propylene from Propane Dehydrogenation (v3)
==============================================================================

This class implements a Life Cycle Inventory (LCI) model for propylene production
via Propane Dehydrogenation (PDH), anchored to ecoinvent v3.10.1 UPR data.

╔══════════════════════════════════════════════════════════════════════╗
║  OPEN-SOURCE VERSION — CONTAINS DUMMY ecoinvent DATA                  ║
║  The 10 BASELINE_* constants in class PDHProcess are ecoinvent-       ║
║  licensed and have been replaced with PLACEHOLDER values. They are    ║
║  the ONLY ecoinvent-derived data in this file. The source activity    ║
║  and how to restore real values are given in the "DUMMY DATA" block   ║
║  next to the constants. The numbers in the baseline table below are   ║
║  shown as (dummy) for the same reason.                                ║
╚══════════════════════════════════════════════════════════════════════╝

Process Overview:
    [Propane] --> [PDH Reactor] --> [Propylene]
                       |
                [Regenerator] <-- [Coked Catalyst]

Fundamental Reaction:
    C3H8 -> C3H6 + H2    dH298 ~ +124 kJ/mol (highly endothermic)

Baseline Data Source:
    ecoinvent v3.10.1 UPR: "propylene production, from propane dehydrogenation"
    Geography: RoW (Rest of World)
    UUID: 504a24f5-789c-5276-9363-cd2f6919dec9
    Functional unit: 1 kg propylene

    All baseline values are taken DIRECTLY from the ecoinvent UPR aggregated
    exchanges. At default scalars (Y_selectivity=1.0, eta_energy=1.0), the
    model reproduces the UPR exactly.

Model Design:
    - Single-output process: 1 kg propylene (no co-products, no allocation)
    - Two user-facing scalars:
        Y_selectivity : improves propane-to-propylene yield (reduces feed + feed-linked flows)
        eta_energy    : improves energy efficiency (reduces heat + electricity + energy-linked flows)
    - Technosphere inputs only (no direct emissions; handled downstream)
    - ecoinvent-compatible flow names throughout

Scalar Mechanics:
    Y_selectivity (default 1.0, range ~0.9-1.2):
        Higher = better selectivity = less propane per kg propylene.
        Scales: propane, chlorine, DMS, NaOH, nitrogen, compressed air, SAN copolymer
        Formula: flow = baseline / Y_selectivity

    eta_energy (default 1.0, range ~0.8-1.2):
        Higher = better energy efficiency = less heat and electricity.
        Scales: steam, natural gas, electricity
        Formula: flow = baseline / eta_energy

ecoinvent UPR Baseline (aggregated, per 1 kg propylene):
---------------------------------------------------------
  TECHNOSPHERE INPUTS (real values are ecoinvent-licensed; shown as dummy):
    propane                                 (dummy) kg
    electricity, medium voltage             (dummy) kWh
    heat, from steam, in chemical industry  (dummy) MJ
    natural gas, high pressure              (dummy) m3
    chlorine, gaseous                       (dummy) kg
    dimethyl sulfide                        (dummy) kg
    nitrogen, liquid                        (dummy) kg
    sodium hydroxide, 50% solution          (dummy) kg
    compressed air, 1200 kPa gauge          (dummy) m3
    styrene-acrylonitrile copolymer         (dummy) kg

  PRODUCT OUTPUT:
    propylene                               1.00000000 kg

Quick Start:
-----------
1. See all parameters:
   >>> PDHProcess.show_parameters()

2. Create baseline model (reproduces ecoinvent UPR):
   >>> pdh = PDHProcess()

3. Create with 5% selectivity improvement:
   >>> pdh = PDHProcess(Y_selectivity=1.05)

4. View results:
   >>> pdh.print_current_parameters()

5. Get flows dict:
   >>> pdh.input_flows
"""


class PDHProcess:
    """
    Propane Dehydrogenation Process for Propylene Production.

    Anchored to ecoinvent v3.10.1 UPR. Single-output (1 kg propylene).
    Two scalars: Y_selectivity (yield) and eta_energy (efficiency).
    Technosphere inputs only — no direct emissions (handled downstream).
    """

    # =========================================================================
    # DUMMY DATA — ecoinvent-licensed baseline (REPLACED WITH PLACEHOLDERS)
    # -------------------------------------------------------------------------
    # The 10 BASELINE_* values below are NOT real ecoinvent data. To reproduce
    # real results, replace each with the corresponding aggregated exchange
    # amount (per 1 kg propylene) from your licensed ecoinvent database:
    #     ecoinvent v3.10.1 UPR
    #     activity: "propylene production, from propane dehydrogenation"
    #     geography: RoW
    #     UUID: 504a24f5-789c-5276-9363-cd2f6919dec9
    # =========================================================================

    # --- Feed-linked flows (scale with Y_selectivity) ---
    BASELINE_PROPANE          = 1.0       # DUMMY (kg propane per kg propylene)
    BASELINE_CHLORINE         = 0.0001    # DUMMY (kg; Pt catalyst promoter)
    BASELINE_DMS              = 0.00003   # DUMMY (kg; dimethyl sulfide promoter)
    BASELINE_NAOH             = 0.005     # DUMMY (kg; NaOH 50% solution)
    BASELINE_NITROGEN         = 0.008     # DUMMY (kg; liquid N2 purge)
    BASELINE_COMPRESSED_AIR   = 0.03      # DUMMY (m3; compressed air, 1200 kPa)
    BASELINE_SAN_COPOLYMER    = 0.0001    # DUMMY (kg; SAN copolymer, minor)

    # --- Energy-linked flows (scale with eta_energy) ---
    BASELINE_STEAM            = 6.0       # DUMMY (MJ; heat, from steam)
    BASELINE_NG               = 0.1       # DUMMY (m3; natural gas, high pressure)
    BASELINE_ELECTRICITY      = 0.1       # DUMMY (kWh; electricity, medium voltage)

    # =========================================================================
    # STATIC METHODS
    # =========================================================================

    @staticmethod
    def show_parameters(detailed=True):
        """Display all available parameters."""
        print("=" * 80)
        print("AVAILABLE PARAMETERS FOR PDHProcess (ecoinvent-anchored)")
        print("=" * 80)

        if detailed:
            print("\n" + " YIELD SCALAR ".center(80, "-"))
            print("  Y_selectivity    : Selectivity improvement scalar      [default: 1.0]")
            print("                     >1.0 = better selectivity = less propane per kg propylene")
            print("                     Scales: propane, chlorine, DMS, NaOH, N2, air, SAN")

            print("\n" + " ENERGY SCALAR ".center(80, "-"))
            print("  eta_energy       : Energy efficiency scalar            [default: 1.0]")
            print("                     >1.0 = more efficient = less heat and electricity")
            print("                     Scales: steam, natural gas, electricity")

            print("\n" + " ECOINVENT UPR BASELINE (per 1 kg propylene) ".center(80, "-"))
            print("  Feed-linked flows:")
            print(f"    propane                    = {PDHProcess.BASELINE_PROPANE:.8f} kg")
            print(f"    chlorine, gaseous          = {PDHProcess.BASELINE_CHLORINE:.8f} kg")
            print(f"    dimethyl sulfide           = {PDHProcess.BASELINE_DMS:.8f} kg")
            print(f"    NaOH, 50% solution         = {PDHProcess.BASELINE_NAOH:.8f} kg")
            print(f"    nitrogen, liquid            = {PDHProcess.BASELINE_NITROGEN:.8f} kg")
            print(f"    compressed air, 1200 kPa   = {PDHProcess.BASELINE_COMPRESSED_AIR:.8f} m3")
            print(f"    SAN copolymer              = {PDHProcess.BASELINE_SAN_COPOLYMER:.8f} kg")
            print("  Energy-linked flows:")
            print(f"    steam (heat)               = {PDHProcess.BASELINE_STEAM:.8f} MJ")
            print(f"    natural gas, high pressure  = {PDHProcess.BASELINE_NG:.8f} m3")
            print(f"    electricity, medium voltage = {PDHProcess.BASELINE_ELECTRICITY:.8f} kWh")

        print("=" * 80)

    @staticmethod
    def get_parameter_template(format='dict'):
        """Get a template showing all parameters and their defaults."""
        template = {
            'Y_selectivity': 1.0,
            'eta_energy': 1.0,
        }
        if format == 'json':
            import json
            return json.dumps(template, indent=2)
        return template

    @staticmethod
    def list_parameters():
        """Quick list of all parameter names."""
        return ['Y_selectivity', 'eta_energy']

    # =========================================================================
    # CONSTRUCTOR
    # =========================================================================

    def __init__(
        self,
        Y_selectivity: float = 1.0,
        eta_energy: float = 1.0,
    ):
        """
        Create a PDH process model anchored to ecoinvent v3.10.1 UPR.

        At default scalars (1.0, 1.0), all flows reproduce the ecoinvent UPR
        exactly. Increasing a scalar improves that aspect of performance
        (less feed or less energy per kg propylene).

        Args:
            Y_selectivity: Selectivity improvement scalar (>1.0 = less propane)
            eta_energy:    Energy efficiency scalar (>1.0 = less energy)
        """
        # =====================================================================
        # VALIDATION
        # =====================================================================
        if Y_selectivity <= 0:
            raise ValueError("Y_selectivity must be positive")
        if eta_energy <= 0:
            raise ValueError("eta_energy must be positive")

        self.Y_selectivity = Y_selectivity
        self.eta_energy = eta_energy

        # =====================================================================
        # FEED-LINKED FLOWS (scale with Y_selectivity)
        # Higher selectivity -> less propane throughput -> less of everything
        # that scales with feed rate.
        # =====================================================================
        self.m_propane        = self.BASELINE_PROPANE        / Y_selectivity
        self.m_chlorine       = self.BASELINE_CHLORINE       / Y_selectivity
        self.m_dms            = self.BASELINE_DMS            / Y_selectivity
        self.m_naoh           = self.BASELINE_NAOH           / Y_selectivity
        self.m_nitrogen       = self.BASELINE_NITROGEN       / Y_selectivity
        self.m_compressed_air = self.BASELINE_COMPRESSED_AIR / Y_selectivity
        self.m_san            = self.BASELINE_SAN_COPOLYMER  / Y_selectivity

        # =====================================================================
        # ENERGY-LINKED FLOWS (scale with eta_energy)
        # Higher efficiency -> less energy per kg propylene.
        # =====================================================================
        self.E_steam       = self.BASELINE_STEAM       / eta_energy
        self.E_ng          = self.BASELINE_NG          / eta_energy
        self.E_electricity = self.BASELINE_ELECTRICITY / eta_energy

        # =====================================================================
        # LCI FLOW DICTIONARIES — ecoinvent-compatible names
        # =====================================================================
        # Technosphere inputs only. No direct emissions (handled downstream).
        #
        # Flow name mapping to ecoinvent v3.10.1 activities:
        #   "propane"                         -> propane production
        #   "electricity, medium voltage"     -> market for electricity, medium voltage
        #   "heat, from steam, in chemical industry" -> steam production, in chemical industry
        #   "natural gas, high pressure"      -> market for natural gas, high pressure
        #   "chlorine, gaseous"               -> chlor-alkali electrolysis
        #   "dimethyl sulfide"                -> dimethyl sulfide production
        #   "sodium hydroxide, without water, in 50% solution state"
        #                                     -> chlor-alkali electrolysis
        #   "nitrogen, liquid"                -> air separation, cryogenic
        #   "compressed air, 1200 kPa gauge"  -> compressed air production
        #   "styrene-acrylonitrile copolymer" -> SAN copolymer production
        # =====================================================================

        self.input_flows = {
            "propane":                                              self.m_propane,         # kg
            "electricity, medium voltage":                          self.E_electricity,     # kWh
            "heat, from steam, in chemical industry":               self.E_steam,           # MJ
            "natural gas, high pressure":                           self.E_ng,              # m3
            "chlorine, gaseous":                                    self.m_chlorine,        # kg
            "dimethyl sulfide":                                     self.m_dms,             # kg
            "sodium hydroxide, without water, in 50% solution state": self.m_naoh,          # kg
            "nitrogen, liquid":                                     self.m_nitrogen,        # kg
            "compressed air, 1200 kPa gauge":                       self.m_compressed_air,  # m3
            "styrene-acrylonitrile copolymer":                      self.m_san,             # kg
        }

        self.output_flows = {"propylene": 1.0}  # kg

    # =========================================================================
    # OUTPUT METHODS
    # =========================================================================

    def print_current_parameters(self):
        """Display complete model results."""
        print("=" * 80)
        print("PDH PROCESS MODEL — ecoinvent v3.10.1 UPR Baseline")
        print("Source: propylene production, from propane dehydrogenation (RoW)")
        print("=" * 80)

        print("\n" + "-" * 80)
        print(" SCALARS:")
        print("-" * 80)
        print(f"  Y_selectivity  = {self.Y_selectivity:.4f}  (1.0 = ecoinvent baseline)")
        print(f"  eta_energy     = {self.eta_energy:.4f}  (1.0 = ecoinvent baseline)")

        print("\n" + "-" * 80)
        print(" TECHNOSPHERE INPUTS (per 1 kg propylene):")
        print(f" ecoinvent-compatible flow names")
        print("-" * 80)

        units_map = {
            "propane": "kg",
            "electricity, medium voltage": "kWh",
            "heat, from steam, in chemical industry": "MJ",
            "natural gas, high pressure": "m3",
            "chlorine, gaseous": "kg",
            "dimethyl sulfide": "kg",
            "sodium hydroxide, without water, in 50% solution state": "kg",
            "nitrogen, liquid": "kg",
            "compressed air, 1200 kPa gauge": "m3",
            "styrene-acrylonitrile copolymer": "kg",
        }

        print("  Feed-linked (scale with Y_selectivity):")
        feed_flows = ["propane", "chlorine, gaseous", "dimethyl sulfide",
                      "sodium hydroxide, without water, in 50% solution state",
                      "nitrogen, liquid", "compressed air, 1200 kPa gauge",
                      "styrene-acrylonitrile copolymer"]
        for name in feed_flows:
            val = self.input_flows[name]
            unit = units_map[name]
            print(f"    {name:55s} = {val:.8f} {unit}")

        print("  Energy-linked (scale with eta_energy):")
        energy_flows = ["heat, from steam, in chemical industry",
                        "natural gas, high pressure",
                        "electricity, medium voltage"]
        for name in energy_flows:
            val = self.input_flows[name]
            unit = units_map[name]
            print(f"    {name:55s} = {val:.8f} {unit}")

        print("\n  PRODUCT OUTPUT:")
        for name, val in self.output_flows.items():
            print(f"    {name:55s} = {val:.8f} kg")

        print("=" * 80)

    def to_dict(self):
        """Export complete parameter set and flows for LCA integration."""
        return {
            'parameters': {
                'Y_selectivity': self.Y_selectivity,
                'eta_energy': self.eta_energy,
            },
            'input_flows': self.input_flows,
            'output_flows': self.output_flows,
        }
