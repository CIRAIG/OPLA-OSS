"""
eg_process.py
=============
Ethylene glycol (EG) production model.

Models the two-stage conversion from ethylene to EG:

    Ethylene → [EO stage] → Ethylene Oxide → [EG stage] → Ethylene Glycol

Each stage has a yield scalar (Y_EO, Y_EG) that adjusts the input
requirement while keeping the reference product fixed at 1 kg.

╔══════════════════════════════════════════════════════════════════════╗
║  OPEN-SOURCE VERSION — CONTAINS DUMMY ecoinvent DATA                  ║
║  The two baseline constants in class EGProcess (M_ETH_PER_EO_ORIG and ║
║  M_EO_PER_EG_ORIG) are ecoinvent-licensed and have been replaced with ║
║  PLACEHOLDER values. They are the ONLY ecoinvent-derived data in this ║
║  file. See the "DUMMY DATA" block below for the source activities and ║
║  how to restore real values from a licensed ecoinvent v3.10.1 db.     ║
╚══════════════════════════════════════════════════════════════════════╝

The class integrates with SteamCrackerProcess for parametric control
of ethylene supply. Steam cracker parameters are passed through via
the 'sc_' prefix.

Equations:
    m_ethylene_per_EO = M_ETH_PER_EO_ORIG / Y_EO
    m_EO_per_EG       = M_EO_PER_EG_ORIG  / Y_EG
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steam_cracking_process import SteamCrackerProcess


class EGProcess:

    # ═══════════════════ DUMMY DATA — ecoinvent-licensed ════════════════════
    # The values below are PLACEHOLDERS, not real ecoinvent data.
    # To reproduce real results, replace them with the input amounts from your
    # licensed ecoinvent v3.10.1 (UPR) database:
    #   M_ETH_PER_EO_ORIG → "ethylene oxide production" (RoW): ethylene input
    #                       per kg ethylene oxide                 [kg/kg]
    #   M_EO_PER_EG_ORIG  → "ethylene glycol production" (RoW): ethylene-oxide
    #                       input per kg ethylene glycol          [kg/kg]
    # ════════════════════════════════════════════════════════════════════════
    M_ETH_PER_EO_ORIG = 0.80   # DUMMY — replace with real ecoinvent value (kg ethylene / kg EO)
    M_EO_PER_EG_ORIG  = 0.70   # DUMMY — replace with real ecoinvent value (kg EO / kg EG)

    def __init__(
        self,
        Y_EO: float = 1.0,
        Y_EG: float = 1.0,
        steam_cracker: SteamCrackerProcess | None = None,
        **sc_params
    ):
        self.Y_EO = Y_EO
        self.Y_EG = Y_EG

        # Adjusted mass inputs per stage
        self.m_eth_per_EO = self.M_ETH_PER_EO_ORIG / Y_EO
        self.m_EO_per_EG = self.M_EO_PER_EG_ORIG / Y_EG

        # Build steam cracker (strip 'sc_' prefix from kwargs)
        if steam_cracker is not None:
            self.steam_cracker = steam_cracker
        else:
            sc_kwargs = {}
            for key, value in sc_params.items():
                if key.startswith('sc_'):
                    sc_kwargs[key[3:]] = value
            self.steam_cracker = SteamCrackerProcess(**sc_kwargs)

    def to_dict(self):
        """Export parameter set for LCA integration."""
        return {
            "parameters": {
                "Y_EO": self.Y_EO,
                "Y_EG": self.Y_EG,
                "m_eth_per_EO": self.m_eth_per_EO,
                "m_EO_per_EG": self.m_EO_per_EG,
            },
            "steam_cracker_parameters": self.steam_cracker.to_dict()["parameters"],
        }
