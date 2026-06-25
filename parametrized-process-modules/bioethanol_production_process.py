"""
Bioethanol Production Process Module
=====================================

Parameterized bioethanol production superstructure for Life Cycle Inventory.

This class provides a flexible framework for representing 28 ethanol
production pathways across 5 feedstock groups (maize, sugarcane, sugarbeet,
potatoes, wood) and combining them into a single, adjustable ethanol
supply mix.

╔══════════════════════════════════════════════════════════════════════╗
║  OPEN-SOURCE VERSION — CONTAINS DUMMY ecoinvent DATA                  ║
║  The per-route baselines in self.original_heat_demand and             ║
║  self.original_mass_demand are ecoinvent-derived and have been        ║
║  replaced with PLACEHOLDER values (see the "DUMMY DATA" blocks).      ║
║  The feedstock-share defaults (f_ethanol_*) are scenario assumptions, ║
║  NOT ecoinvent data, and are left unchanged. Replace the dummy        ║
║  baselines with the heat/mass demands of the matching ecoinvent       ║
║  v3.10.1 ethanol-production activities to reproduce real results.     ║
╚══════════════════════════════════════════════════════════════════════╝

It is designed as a foreground superstructure that operates on top of
existing unit processes (e.g., ecoinvent datasets), without performing
internal mass or energy balances. Instead, it exposes high-level
parameters that modify the contribution and resource requirements of
each ethanol pathway.

Main capabilities:

1) Feedstock share variation (f_ethanol_*):
   28 fractional contribution parameters. Shares are normalized to
   ensure they sum to <= 1.

2) Thermal-energy modeling:
   - 5 feedstock-level thermal efficiency parameters (one per group).
   - Each route has a baseline heat demand (MJ per kg ethanol).
   - Adjusted: Q_new_i = Q_orig_i / efficiency[group_i]

3) Feedstock mass modeling:
   - 5 feedstock-level yield parameters (one per group).
   - Each route has a baseline mass demand (kg feedstock per kg ethanol).
   - Adjusted: m_new_i = m_orig_i / yield[group_i]

Total user-facing parameters: 38
  - 28 feedstock shares
  - 5 thermal efficiencies
  - 5 yield scalars

Based on the original BioethanolProductionProcess notebook by Ameed.
Extended to accept efficiency and yield as constructor arguments.
"""


class BioethanolProductionProcess:
    """
    Parameterized bioethanol production superstructure.

    Produces 1 kg of ethanol (95% solution state) from a weighted mix
    of 28 ethanol production routes. Exposes E_* (adjusted heat) and
    M_* (adjusted mass) attributes for each route.
    """

    # Route → CSV template mapping (used by InventoryGenerator)
    ROUTE_TO_TEMPLATE = {
        # MAIZE
        'ethanol_maize_US': 'maize',
        'ethanol_maize_BR': 'maize',
        'ethanol_maize_RoW': 'maize',
        # SUGARCANE
        'ethanol_sugarcane_mauto_BR': 'sc_mauto',
        'ethanol_sugarcane_tauto_BR': 'sc_tauto',
        'ethanol_sugarcane_mannexed_BR': 'sc_mannexed',
        'ethanol_sugarcane_tannexed_BR': 'sc_tannexed',
        'ethanol_sugarcane_mauto_IN': 'sc_mauto',
        'ethanol_sugarcane_tauto_IN': 'sc_tauto',
        'ethanol_sugarcane_mannexed_IN': 'sc_mannexed',
        'ethanol_sugarcane_tannexed_IN': 'sc_tannexed',
        'ethanol_sugarcane_mauto_RoW': 'sc_mauto',
        'ethanol_sugarcane_tauto_RoW': 'sc_tauto',
        'ethanol_sugarcane_mannexed_RoW': 'sc_mannexed',
        'ethanol_sugarcane_tannexed_RoW': 'sc_tannexed',
        # SUGARBEET
        'ethanol_sugarbeet_US': 'sugarbeet',
        'ethanol_sugarbeet_FR': 'sugarbeet',
        'ethanol_sugarbeet_DE': 'sugarbeet',
        'ethanol_sugarbeet_CH': 'sugarbeet',
        'ethanol_sugarbeet_RU': 'sugarbeet',
        'ethanol_sugarbeet_RoW': 'sugarbeet',
        # POTATO
        'ethanol_potatoes_CN': 'potato',
        'ethanol_potatoes_IN': 'potato',
        'ethanol_potatoes_RoW': 'potato',
        # WOOD
        'ethanol_wood_CA': 'wood',
        'ethanol_wood_SE': 'wood',
        'ethanol_wood_CH': 'wood',
        'ethanol_wood_RoW': 'wood',
    }

    def __init__(
        self,
        # ----- FEEDSTOCK SHARE PARAMETERS (28) -----
        f_ethanol_maize_US: float = 0.59,
        f_ethanol_maize_BR: float = 0.0082608695652,
        f_ethanol_maize_RoW: float = 0.0082608695652,

        f_ethanol_sugarcane_mauto_BR: float = 0.055,
        f_ethanol_sugarcane_tauto_BR: float = 0.055,
        f_ethanol_sugarcane_mannexed_BR: float = 0.055,
        f_ethanol_sugarcane_tannexed_BR: float = 0.055,

        f_ethanol_sugarcane_mauto_IN: float = 0.0082608695652,
        f_ethanol_sugarcane_tauto_IN: float = 0.0082608695652,
        f_ethanol_sugarcane_mannexed_IN: float = 0.0082608695652,
        f_ethanol_sugarcane_tannexed_IN: float = 0.0082608695652,

        f_ethanol_sugarcane_mauto_RoW: float = 0.0082608695652,
        f_ethanol_sugarcane_tauto_RoW: float = 0.0082608695652,
        f_ethanol_sugarcane_mannexed_RoW: float = 0.0082608695652,
        f_ethanol_sugarcane_tannexed_RoW: float = 0.0082608695652,

        f_ethanol_sugarbeet_US: float = 0.0082608695652,
        f_ethanol_sugarbeet_FR: float = 0.0082608695652,
        f_ethanol_sugarbeet_DE: float = 0.0082608695652,
        f_ethanol_sugarbeet_CH: float = 0.0082608695652,
        f_ethanol_sugarbeet_RU: float = 0.0082608695652,
        f_ethanol_sugarbeet_RoW: float = 0.0082608695652,

        f_ethanol_potatoes_CN: float = 0.0082608695652,
        f_ethanol_potatoes_IN: float = 0.0082608695652,
        f_ethanol_potatoes_RoW: float = 0.0082608695652,

        f_ethanol_wood_CA: float = 0.0082608695652,
        f_ethanol_wood_SE: float = 0.0082608695652,
        f_ethanol_wood_CH: float = 0.0082608695652,
        f_ethanol_wood_RoW: float = 0.0082608695652,

        # ----- THERMAL EFFICIENCY PARAMETERS (5) -----
        efficiency_maize: float = 1.0,
        efficiency_sugarcane: float = 1.0,
        efficiency_sugarbeet: float = 1.0,
        efficiency_potato: float = 1.0,
        efficiency_wood: float = 1.0,

        # ----- YIELD PARAMETERS (5) -----
        yield_maize: float = 1.0,
        yield_sugarcane: float = 1.0,
        yield_sugarbeet: float = 1.0,
        yield_potato: float = 1.0,
        yield_wood: float = 1.0,
    ):
        # ─────────────────────────────────────────────
        # 1) STORE & NORMALIZE FEEDSTOCK SHARES
        # ─────────────────────────────────────────────
        share_params = {
            'f_ethanol_maize_US': f_ethanol_maize_US,
            'f_ethanol_maize_BR': f_ethanol_maize_BR,
            'f_ethanol_maize_RoW': f_ethanol_maize_RoW,

            'f_ethanol_sugarcane_mauto_BR': f_ethanol_sugarcane_mauto_BR,
            'f_ethanol_sugarcane_tauto_BR': f_ethanol_sugarcane_tauto_BR,
            'f_ethanol_sugarcane_mannexed_BR': f_ethanol_sugarcane_mannexed_BR,
            'f_ethanol_sugarcane_tannexed_BR': f_ethanol_sugarcane_tannexed_BR,

            'f_ethanol_sugarcane_mauto_IN': f_ethanol_sugarcane_mauto_IN,
            'f_ethanol_sugarcane_tauto_IN': f_ethanol_sugarcane_tauto_IN,
            'f_ethanol_sugarcane_mannexed_IN': f_ethanol_sugarcane_mannexed_IN,
            'f_ethanol_sugarcane_tannexed_IN': f_ethanol_sugarcane_tannexed_IN,

            'f_ethanol_sugarcane_mauto_RoW': f_ethanol_sugarcane_mauto_RoW,
            'f_ethanol_sugarcane_tauto_RoW': f_ethanol_sugarcane_tauto_RoW,
            'f_ethanol_sugarcane_mannexed_RoW': f_ethanol_sugarcane_mannexed_RoW,
            'f_ethanol_sugarcane_tannexed_RoW': f_ethanol_sugarcane_tannexed_RoW,

            'f_ethanol_sugarbeet_US': f_ethanol_sugarbeet_US,
            'f_ethanol_sugarbeet_FR': f_ethanol_sugarbeet_FR,
            'f_ethanol_sugarbeet_DE': f_ethanol_sugarbeet_DE,
            'f_ethanol_sugarbeet_CH': f_ethanol_sugarbeet_CH,
            'f_ethanol_sugarbeet_RU': f_ethanol_sugarbeet_RU,
            'f_ethanol_sugarbeet_RoW': f_ethanol_sugarbeet_RoW,

            'f_ethanol_potatoes_CN': f_ethanol_potatoes_CN,
            'f_ethanol_potatoes_IN': f_ethanol_potatoes_IN,
            'f_ethanol_potatoes_RoW': f_ethanol_potatoes_RoW,

            'f_ethanol_wood_CA': f_ethanol_wood_CA,
            'f_ethanol_wood_SE': f_ethanol_wood_SE,
            'f_ethanol_wood_CH': f_ethanol_wood_CH,
            'f_ethanol_wood_RoW': f_ethanol_wood_RoW,
        }

        total = sum(share_params.values())
        if total > 1.0:
            share_params = {k: v / total for k, v in share_params.items()}

        for name, value in share_params.items():
            setattr(self, name, value)

        # ─────────────────────────────────────────────
        # 2) REFERENCE OUTPUT (1 kg ETHANOL)
        # ─────────────────────────────────────────────
        self.m_ethanol = 1.0
        self.input_flows = share_params.copy()
        self.output_flows = {'ethanol': self.m_ethanol}

        # ─────────────────────────────────────────────
        # 3) FEEDSTOCK-LEVEL THERMAL EFFICIENCY
        # ─────────────────────────────────────────────
        self.feedstock_efficiency = {
            'maize': efficiency_maize,
            'sugarcane': efficiency_sugarcane,
            'sugarbeet': efficiency_sugarbeet,
            'potato': efficiency_potato,
            'wood': efficiency_wood,
        }

        # ─────────────────────────────────────────────
        # 4) ORIGINAL HEAT DEMAND PER PROCESS (MJ/kg ethanol)
        # ═════════════ DUMMY DATA — ecoinvent-licensed ══════════════
        # The non-zero values below are PLACEHOLDERS, not real ecoinvent
        # data. Replace each with the heat (MJ per kg ethanol) of the
        # matching ecoinvent v3.10.1 ethanol-production activity for that
        # feedstock/region (confirm exact activity names in your build).
        # Zeros are structural (bagasse / wood co-generation = no external
        # heat) and are NOT licensed data.
        # ─────────────────────────────────────────────
        self.original_heat_demand = {
            # MAIZE
            'ethanol_maize_US': 10.0,   # DUMMY (real value ecoinvent-licensed)
            'ethanol_maize_BR': 10.0,   # DUMMY
            'ethanol_maize_RoW': 10.0,  # DUMMY
            # SUGARCANE (no external heat — bagasse co-gen)
            'ethanol_sugarcane_mauto_BR': 0,
            'ethanol_sugarcane_tauto_BR': 0,
            'ethanol_sugarcane_mannexed_BR': 0,
            'ethanol_sugarcane_tannexed_BR': 0,
            'ethanol_sugarcane_mauto_IN': 0,
            'ethanol_sugarcane_tauto_IN': 0,
            'ethanol_sugarcane_mannexed_IN': 0,
            'ethanol_sugarcane_tannexed_IN': 0,
            'ethanol_sugarcane_mauto_RoW': 0,
            'ethanol_sugarcane_tauto_RoW': 0,
            'ethanol_sugarcane_mannexed_RoW': 0,
            'ethanol_sugarcane_tannexed_RoW': 0,
            # SUGARBEET
            'ethanol_sugarbeet_US': 2.0,   # DUMMY
            'ethanol_sugarbeet_FR': 2.0,   # DUMMY
            'ethanol_sugarbeet_DE': 2.0,   # DUMMY
            'ethanol_sugarbeet_CH': 2.0,   # DUMMY
            'ethanol_sugarbeet_RU': 2.0,   # DUMMY
            'ethanol_sugarbeet_RoW': 2.0,  # DUMMY
            # POTATOES
            'ethanol_potatoes_CN': 15.0,   # DUMMY
            'ethanol_potatoes_IN': 15.0,   # DUMMY
            'ethanol_potatoes_RoW': 15.0,  # DUMMY
            # WOOD (no external heat — co-gen)
            'ethanol_wood_CA': 0,
            'ethanol_wood_SE': 0,
            'ethanol_wood_CH': 0,
            'ethanol_wood_RoW': 0,
        }

        # ─────────────────────────────────────────────
        # 5) FEEDSTOCK-LEVEL YIELD
        # ─────────────────────────────────────────────
        self.feedstock_yield = {
            'maize': yield_maize,
            'sugarcane': yield_sugarcane,
            'sugarbeet': yield_sugarbeet,
            'potato': yield_potato,
            'wood': yield_wood,
        }

        # ─────────────────────────────────────────────
        # 6) ORIGINAL MASS DEMAND PER PROCESS (kg/kg ethanol)
        # ═════════════ DUMMY DATA — ecoinvent-licensed ══════════════
        # The values below are PLACEHOLDERS, not real ecoinvent data.
        # Replace each with the feedstock mass (kg per kg ethanol) of the
        # matching ecoinvent v3.10.1 ethanol-production activity for that
        # feedstock/region (confirm exact activity names in your build).
        # ─────────────────────────────────────────────
        self.original_mass_demand = {
            # MAIZE
            'ethanol_maize_US': 3.0,   # DUMMY (real value ecoinvent-licensed)
            'ethanol_maize_BR': 3.0,   # DUMMY
            'ethanol_maize_RoW': 3.0,  # DUMMY
            # SUGARCANE
            'ethanol_sugarcane_mauto_BR': 9.0,     # DUMMY
            'ethanol_sugarcane_tauto_BR': 12.0,    # DUMMY
            'ethanol_sugarcane_mannexed_BR': 6.0,  # DUMMY
            'ethanol_sugarcane_tannexed_BR': 8.0,  # DUMMY
            'ethanol_sugarcane_mauto_IN': 9.0,     # DUMMY
            'ethanol_sugarcane_tauto_IN': 12.0,    # DUMMY
            'ethanol_sugarcane_mannexed_IN': 6.0,  # DUMMY
            'ethanol_sugarcane_tannexed_IN': 8.0,  # DUMMY
            'ethanol_sugarcane_mauto_RoW': 9.0,    # DUMMY
            'ethanol_sugarcane_tauto_RoW': 12.0,   # DUMMY
            'ethanol_sugarcane_mannexed_RoW': 6.0, # DUMMY
            'ethanol_sugarcane_tannexed_RoW': 8.0, # DUMMY
            # SUGARBEET
            'ethanol_sugarbeet_US': 6.5,   # DUMMY
            'ethanol_sugarbeet_FR': 6.5,   # DUMMY
            'ethanol_sugarbeet_DE': 6.5,   # DUMMY
            'ethanol_sugarbeet_CH': 6.5,   # DUMMY
            'ethanol_sugarbeet_RU': 6.5,   # DUMMY
            'ethanol_sugarbeet_RoW': 6.5,  # DUMMY
            # POTATOES
            'ethanol_potatoes_CN': 14.0,   # DUMMY
            'ethanol_potatoes_IN': 14.0,   # DUMMY
            'ethanol_potatoes_RoW': 14.0,  # DUMMY
            # WOOD
            'ethanol_wood_CA': 3.8,   # DUMMY
            'ethanol_wood_SE': 3.8,   # DUMMY
            'ethanol_wood_CH': 3.8,   # DUMMY
            'ethanol_wood_RoW': 3.8,  # DUMMY
        }

        # ─────────────────────────────────────────────
        # 7) MAP PROCESS → FEEDSTOCK GROUP
        # ─────────────────────────────────────────────
        self.feedstock_group = {
            'ethanol_maize_US': 'maize',
            'ethanol_maize_BR': 'maize',
            'ethanol_maize_RoW': 'maize',
            'ethanol_sugarcane_mauto_BR': 'sugarcane',
            'ethanol_sugarcane_tauto_BR': 'sugarcane',
            'ethanol_sugarcane_mannexed_BR': 'sugarcane',
            'ethanol_sugarcane_tannexed_BR': 'sugarcane',
            'ethanol_sugarcane_mauto_IN': 'sugarcane',
            'ethanol_sugarcane_tauto_IN': 'sugarcane',
            'ethanol_sugarcane_mannexed_IN': 'sugarcane',
            'ethanol_sugarcane_tannexed_IN': 'sugarcane',
            'ethanol_sugarcane_mauto_RoW': 'sugarcane',
            'ethanol_sugarcane_tauto_RoW': 'sugarcane',
            'ethanol_sugarcane_mannexed_RoW': 'sugarcane',
            'ethanol_sugarcane_tannexed_RoW': 'sugarcane',
            'ethanol_sugarbeet_US': 'sugarbeet',
            'ethanol_sugarbeet_FR': 'sugarbeet',
            'ethanol_sugarbeet_DE': 'sugarbeet',
            'ethanol_sugarbeet_CH': 'sugarbeet',
            'ethanol_sugarbeet_RU': 'sugarbeet',
            'ethanol_sugarbeet_RoW': 'sugarbeet',
            'ethanol_potatoes_CN': 'potato',
            'ethanol_potatoes_IN': 'potato',
            'ethanol_potatoes_RoW': 'potato',
            'ethanol_wood_CA': 'wood',
            'ethanol_wood_SE': 'wood',
            'ethanol_wood_CH': 'wood',
            'ethanol_wood_RoW': 'wood',
        }

        # ─────────────────────────────────────────────
        # 8) COMPUTE ADJUSTED HEAT (E_*) AND MASS (M_*)
        # ─────────────────────────────────────────────
        for process_name, E_orig in self.original_heat_demand.items():
            feedstock = self.feedstock_group[process_name]
            eff = self.feedstock_efficiency[feedstock]
            E_new = E_orig / eff if eff != 0 else float("inf")
            setattr(self, f"E_{process_name}", E_new)

        for process_name, m_orig in self.original_mass_demand.items():
            feedstock = self.feedstock_group[process_name]
            y = self.feedstock_yield[feedstock]
            m_new = m_orig / y if y != 0 else float("inf")
            setattr(self, f"M_{process_name}", m_new)

    # ─────────────────────────────────────────────────
    # Helper methods
    # ─────────────────────────────────────────────────

    def get_adjusted_heat_inputs(self) -> dict:
        """Return adjusted heat input E for each ethanol process."""
        adjusted = {}
        for process_name, E_orig in self.original_heat_demand.items():
            feedstock = self.feedstock_group[process_name]
            eff = self.feedstock_efficiency[feedstock]
            adjusted[process_name] = E_orig / eff if eff != 0 else float("inf")
        return adjusted

    def get_adjusted_mass_inputs(self) -> dict:
        """Return adjusted mass demand for each ethanol process."""
        adjusted = {}
        for process_name, m_orig in self.original_mass_demand.items():
            feedstock = self.feedstock_group[process_name]
            y = self.feedstock_yield[feedstock]
            adjusted[process_name] = m_orig / y if y != 0 else float("inf")
        return adjusted

    def get_route_names(self) -> list:
        """Return list of all 28 route names."""
        return list(self.feedstock_group.keys())

    def get_share(self, route_name: str) -> float:
        """Return the normalized feedstock share for a route."""
        return self.input_flows.get(f'f_{route_name}', 0.0)

    def to_dict(self) -> dict:
        return {
            'parameters': self.input_flows.copy(),
            'reference_output': {'m_ethanol': self.m_ethanol},
            'input_flows': self.input_flows,
            'output_flows': self.output_flows,
            'feedstock_efficiency': self.feedstock_efficiency.copy(),
            'feedstock_yield': self.feedstock_yield.copy(),
        }

    @staticmethod
    def show_parameters():
        """Print all tuneable parameters with descriptions."""
        print("=" * 75)
        print("  BioethanolProductionProcess — Tuneable Parameters")
        print("=" * 75)
        print("\n  FEEDSTOCK SHARES (28 params, must sum to <= 1.0):")
        print("  ─" * 35)
        groups = {
            'Maize': ['f_ethanol_maize_US', 'f_ethanol_maize_BR',
                       'f_ethanol_maize_RoW'],
            'Sugarcane': [f'f_ethanol_sugarcane_{t}_{l}'
                          for t in ('mauto', 'tauto', 'mannexed', 'tannexed')
                          for l in ('BR', 'IN', 'RoW')],
            'Sugar beet': [f'f_ethanol_sugarbeet_{l}'
                           for l in ('US', 'FR', 'DE', 'CH', 'RU', 'RoW')],
            'Potatoes': [f'f_ethanol_potatoes_{l}'
                         for l in ('CN', 'IN', 'RoW')],
            'Wood': [f'f_ethanol_wood_{l}'
                     for l in ('CA', 'SE', 'CH', 'RoW')],
        }
        for group_name, params in groups.items():
            print(f"\n    {group_name}:")
            for p in params:
                print(f"      {p}")

        print("\n  THERMAL EFFICIENCY (5 params, default 1.0):")
        print("  ─" * 35)
        for g in ('maize', 'sugarcane', 'sugarbeet', 'potato', 'wood'):
            print(f"    efficiency_{g}")

        print("\n  YIELD SCALARS (5 params, default 1.0):")
        print("  ─" * 35)
        for g in ('maize', 'sugarcane', 'sugarbeet', 'potato', 'wood'):
            print(f"    yield_{g}")
