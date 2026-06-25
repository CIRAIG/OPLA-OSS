"""
tpa_process.py
==============
Terephthalic acid (TPA) production model.

Models the TPA production chain from p-xylene feedstock, including
two upstream p-xylene routes (pyrolysis gas and reformate):

    [Pyrolysis gas] ──┐
                      ├→ [p-Xylene] → [TPA purification] → TPA
    [Reformate]     ──┘

Parameters control thermal efficiencies (eta), yield scalars (Y),
and route shares (alpha) for each stage.

╔══════════════════════════════════════════════════════════════════════╗
║  OPEN-SOURCE VERSION — CONTAINS DUMMY ecoinvent DATA                  ║
║  The six *_ORIG baseline constants in class TPAProcess are            ║
║  ecoinvent-licensed and have been replaced with PLACEHOLDER values.   ║
║  They are the ONLY ecoinvent-derived data in this file. See the       ║
║  "DUMMY DATA" block below for the source activities and how to        ║
║  restore real values from a licensed ecoinvent v3.10.1 database.      ║
╚══════════════════════════════════════════════════════════════════════╝

Equations:
    Heat:  E_new = E_orig / eta       (higher eta → less heat needed)
    Yield: m_new = m_orig / Y         (higher Y → less feed needed)
    Route: m_pX_from_pyr = alpha_pyr × m_pX_total
           m_pX_from_ref = alpha_ref × m_pX_total
"""


class TPAProcess:

    # ═══════════════════ DUMMY DATA — ecoinvent-licensed ════════════════════
    # The six values below are PLACEHOLDERS, not real ecoinvent data.
    # To reproduce real results, replace each with the corresponding aggregated
    # exchange amount from your licensed ecoinvent v3.10.1 (UPR) database:
    #   E_TPA_ORIG, M_PX_TO_TPA_ORIG → "purified terephthalic acid production"
    #                       (RoW): heat input [MJ/kg] and p-xylene input [kg/kg]
    #   E_PYR_ORIG, M_FEED_PYR_ORIG  → p-xylene production, pyrolysis-gas route
    #                       (RoW): heat [MJ/kg pX] and pyrolysis-gas feed [kg/kg pX]
    #   E_REF_ORIG, M_FEED_REF_ORIG  → p-xylene production, reformate route
    #                       (RoW): heat [MJ/kg pX] and reformate feed [kg/kg pX]
    #   (confirm the exact p-xylene activity names against your ecoinvent build)
    # ════════════════════════════════════════════════════════════════════════
    E_TPA_ORIG = 2.0          # DUMMY — replace with real ecoinvent value (MJ heat / kg TPA)
    M_PX_TO_TPA_ORIG = 0.70   # DUMMY — replace with real ecoinvent value (kg p-xylene / kg TPA)
    E_PYR_ORIG = 3.0          # DUMMY — replace with real ecoinvent value (MJ heat / kg p-xylene, pyrolysis)
    M_FEED_PYR_ORIG = 1.20    # DUMMY — replace with real ecoinvent value (kg pyrolysis gas / kg p-xylene)
    E_REF_ORIG = 6.0          # DUMMY — replace with real ecoinvent value (MJ heat / kg p-xylene, reformate)
    M_FEED_REF_ORIG = 1.10    # DUMMY — replace with real ecoinvent value (kg reformate / kg p-xylene)

    def __init__(
        self,
        eta_TPA: float = 1.0,
        Y_TPA: float = 1.0,
        eta_pyr: float = 1.0,
        Y_pyr: float = 1.0,
        eta_ref: float = 1.0,
        Y_ref: float = 1.0,
        alpha_pyr: float = 0.11,
        alpha_ref: float = 0.89,
    ):
        self.eta_TPA = eta_TPA
        self.Y_TPA = Y_TPA
        self.eta_pyr = eta_pyr
        self.Y_pyr = Y_pyr
        self.eta_ref = eta_ref
        self.Y_ref = Y_ref
        self.alpha_pyr = alpha_pyr
        self.alpha_ref = alpha_ref

        # TPA purification
        self.E_TPA = self.E_TPA_ORIG / eta_TPA
        self.m_pX_per_TPA = self.M_PX_TO_TPA_ORIG / Y_TPA

        # p-Xylene demand split
        self.m_pX_from_pyr = alpha_pyr * self.m_pX_per_TPA
        self.m_pX_from_ref = alpha_ref * self.m_pX_per_TPA

        # p-Xylene from pyrolysis gas
        self.E_pyr = self.E_PYR_ORIG / eta_pyr
        self.m_feed_pyr = self.M_FEED_PYR_ORIG / Y_pyr

        # p-Xylene from reformate
        self.E_ref = self.E_REF_ORIG / eta_ref
        self.m_feed_ref = self.M_FEED_REF_ORIG / Y_ref

    def to_dict(self):
        """Export parameter set for LCA integration."""
        return {
            "parameters": {
                "eta_TPA": self.eta_TPA,
                "Y_TPA": self.Y_TPA,
                "E_TPA": self.E_TPA,
                "m_pX_per_TPA": self.m_pX_per_TPA,
                "eta_pyr": self.eta_pyr,
                "Y_pyr": self.Y_pyr,
                "E_pyr": self.E_pyr,
                "m_feed_pyr": self.m_feed_pyr,
                "eta_ref": self.eta_ref,
                "Y_ref": self.Y_ref,
                "E_ref": self.E_ref,
                "m_feed_ref": self.m_feed_ref,
                "alpha_pyr": self.alpha_pyr,
                "alpha_ref": self.alpha_ref,
                "m_pX_from_pyr": self.m_pX_from_pyr,
                "m_pX_from_ref": self.m_pX_from_ref,
            }
        }
