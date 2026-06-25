"""
PropyleneSCProcess Class - Propylene from Steam Cracking
----------------------------------------------------------------------

This class represents propylene production via steam cracking, designed to be
DEPENDENT on the SteamCrackerProcess class. Instead of duplicating the steam
cracking logic, this class wraps SteamCrackerProcess and RE-REFERENCES the
outputs to propylene as the main product (functional unit: 1 kg propylene).

Design Philosophy - Modularity & Compatibility:
------------------------------------------------
The SteamCrackerProcess produces 1 kg ethylene as its reference product, with
propylene as a co-product. This class inverts that relationship:
- Takes a SteamCrackerProcess instance
- Scales ALL flows to produce 1 kg propylene instead
- Any changes to SteamCrackerProcess automatically propagate here

Process Overview:
    [Mixed Feedstocks] ──→ [Steam Cracker] ──→ [Propylene (main) + Co-products]
         (Butane, Ethane,                        (Ethylene becomes co-product,
          Propane, Naphtha,                       Butadiene, H2, CH4, BTX, etc.)
          Gasoil)

Mathematical Model - Re-referencing Equations:
-----------------------------------------------

Given SteamCrackerProcess outputs per 1 kg ethylene:
    m_propylene_per_kg_ethylene = steam_cracker.m_propylene

1. Scaling factor to produce 1 kg propylene:
   scale = 1 / m_propylene_per_kg_ethylene

2. All input flows scaled:
   m_input_new = m_input_orig × scale

3. All output flows scaled:
   m_output_new = m_output_orig × scale
   (Note: ethylene becomes a co-product in this reference)

Key Features:
- Zero code duplication - delegates all calculations to SteamCrackerProcess
- Automatic updates - changes to SC class propagate automatically
- Full parameter pass-through with sc_* prefix
- Maintains mass and energy balance consistency

Quick Start:
-----------
1. See all available parameters:
   >>> PropyleneSCProcess.show_parameters()

2. Create your model:
   >>> psc = PropyleneSCProcess(sc_f_naphtha=0.8, sc_f_ethane=0.2)

3. View your current settings:
   >>> psc.print_current_parameters()
"""

from steam_cracking_process import SteamCrackerProcess


class PropyleneSCProcess:
    """
    Propylene Production from Steam Cracking
    
    This class wraps SteamCrackerProcess and re-references all flows
    to produce 1 kg propylene as the functional unit instead of ethylene.
    """
    
    @staticmethod
    def show_parameters(detailed=True):
        """
        Display all available parameters that can be varied
        
        Args:
            detailed: If True, shows descriptions and defaults
        """
        print("="*80)
        print("AVAILABLE PARAMETERS FOR PropyleneSCProcess")
        print("="*80)
        print("\nThis class wraps SteamCrackerProcess with propylene as reference product.")
        print("All steam cracker parameters are accessible with 'sc_' prefix.")
        
        if detailed:
            print("\n" + "STEAM CRACKER (prefix: sc_)".center(80, "-"))
            print("\n  Feedstock Shares (auto-normalized):")
            params = [
                ("sc_f_butane", "Butane feedstock share", 0.028),
                ("sc_f_ethane", "Ethane feedstock share", 0.756),
                ("sc_f_gasoil", "Gasoil feedstock share", 0.001),
                ("sc_f_naphtha", "Naphtha feedstock share", 0.061),
                ("sc_f_propane", "Propane feedstock share", 0.154),
            ]
            for name, desc, default in params:
                print(f"    {name:25s} : {desc:35s} [{default}]")
            
            print("\n  Yield Scalars (Ethylene Selectivity):")
            print("    Note: Higher ethylene selectivity = LOWER propylene yield")
            yield_params = [
                ("sc_Y_ethylene_butane", "Ethylene yield scalar for butane", 1.0),
                ("sc_Y_ethylene_ethane", "Ethylene yield scalar for ethane", 1.0),
                ("sc_Y_ethylene_gasoil", "Ethylene yield scalar for gasoil", 1.0),
                ("sc_Y_ethylene_naphtha", "Ethylene yield scalar for naphtha", 1.0),
                ("sc_Y_ethylene_propane", "Ethylene yield scalar for propane", 1.0),
            ]
            for name, desc, default in yield_params:
                print(f"    {name:25s} : {desc:35s} [{default}]")
            
            print("\n  Combustion & Efficiency:")
            eff_params = [
                ("sc_f_h2_combusted", "H2 combustion fraction", 0.7),
                ("sc_f_ch4_combusted", "CH4 combustion fraction", 1.0),
                ("sc_thermal_eff", "Thermal efficiency", 0.89),
            ]
            for name, desc, default in eff_params:
                print(f"    {name:25s} : {desc:35s} [{default}]")
        else:
            print("\nFeedstock: sc_f_butane, sc_f_ethane, sc_f_gasoil, sc_f_naphtha, sc_f_propane")
            print("Yields: sc_Y_ethylene_butane, sc_Y_ethylene_ethane, sc_Y_ethylene_gasoil,")
            print("        sc_Y_ethylene_naphtha, sc_Y_ethylene_propane")
            print("Efficiency: sc_f_h2_combusted, sc_f_ch4_combusted, sc_thermal_eff")
        
        print("\n" + "="*80)
        print("USAGE EXAMPLES:")
        print("="*80)
        print("""
# Example 1: Higher naphtha feed (better propylene yield)
psc = PropyleneSCProcess(
    sc_f_naphtha=0.8,
    sc_f_ethane=0.2
)

# Example 2: Adjust ethylene selectivity (lower = more propylene)
psc = PropyleneSCProcess(
    sc_f_naphtha=0.7,
    sc_f_butane=0.3,
    sc_Y_ethylene_naphtha=0.95,  # Slightly lower ethylene selectivity
    sc_thermal_eff=0.90
)

# Example 3: Pass a pre-built steam cracker
sc = SteamCrackerProcess(f_naphtha=0.9)
psc = PropyleneSCProcess(steam_cracker=sc)

# Example 4: See underlying steam cracker details
SteamCrackerProcess.show_parameters()
        """)
        print("="*80)
    
    @staticmethod
    def get_parameter_template(format='dict'):
        """
        Get a template showing all parameters and their defaults
        
        Args:
            format: 'dict' or 'json'
        
        Returns:
            Dictionary or formatted string with all parameters
        """
        template = {
            'sc_f_butane': 0.028,
            'sc_f_ethane': 0.756,
            'sc_f_gasoil': 0.001,
            'sc_f_naphtha': 0.061,
            'sc_f_propane': 0.154,
            'sc_Y_ethylene_butane': 1.0,
            'sc_Y_ethylene_ethane': 1.0,
            'sc_Y_ethylene_gasoil': 1.0,
            'sc_Y_ethylene_naphtha': 1.0,
            'sc_Y_ethylene_propane': 1.0,
            'sc_f_h2_combusted': 0.7,
            'sc_f_ch4_combusted': 1.0,
            'sc_thermal_eff': 0.89,
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
        """Quick list of all parameter names (autocomplete-friendly)"""
        return [
            'sc_f_butane', 'sc_f_ethane', 'sc_f_gasoil', 'sc_f_naphtha', 'sc_f_propane',
            'sc_Y_ethylene_butane', 'sc_Y_ethylene_ethane', 'sc_Y_ethylene_gasoil',
            'sc_Y_ethylene_naphtha', 'sc_Y_ethylene_propane',
            'sc_f_h2_combusted', 'sc_f_ch4_combusted', 'sc_thermal_eff'
        ]
    
    def print_current_parameters(self):
        """Display the current parameter values of this instance"""
        print("="*80)
        print("CURRENT PROPYLENE FROM STEAM CRACKING PARAMETERS")
        print("="*80)
        
        print("\n Reference Product: 1 kg PROPYLENE")
        print(f"  Scaling factor from ethylene base = {self.scale_factor:.6f}")
        
        print("\n Steam Cracker Feedstock Shares:")
        print(f"  sc_f_butane  = {self.steam_cracker.f_butane_share_cracking:.6f}")
        print(f"  sc_f_ethane  = {self.steam_cracker.f_ethane_share_cracking:.6f}")
        print(f"  sc_f_gasoil  = {self.steam_cracker.f_gasoil_share_cracking:.6f}")
        print(f"  sc_f_naphtha = {self.steam_cracker.f_naphtha_share_cracking:.6f}")
        print(f"  sc_f_propane = {self.steam_cracker.f_propane_share_cracking:.6f}")
        
        print("\n Steam Cracker Yield Scalars:")
        print(f"  sc_Y_ethylene_butane  = {self.steam_cracker.Y_ethylene_butane:.4f}")
        print(f"  sc_Y_ethylene_ethane  = {self.steam_cracker.Y_ethylene_ethane:.4f}")
        print(f"  sc_Y_ethylene_gasoil  = {self.steam_cracker.Y_ethylene_gasoil:.4f}")
        print(f"  sc_Y_ethylene_naphtha = {self.steam_cracker.Y_ethylene_naphtha:.4f}")
        print(f"  sc_Y_ethylene_propane = {self.steam_cracker.Y_ethylene_propane:.4f}")
        
        print("\n Combustion & Efficiency:")
        print(f"  sc_f_h2_combusted  = {self.steam_cracker.f_hydrogen_combusted_cracker:.4f}")
        print(f"  sc_f_ch4_combusted = {self.steam_cracker.f_methane_combusted_cracker:.4f}")
        print(f"  sc_thermal_eff     = {self.steam_cracker.thermal_efficiency_cracker:.4f}")
        
        print("\n Key Results (per kg propylene):")
        print(f"  Total feed required (kg)         = {self.m_feed_total:.4f}")
        print(f"  Ethylene co-product (kg)         = {self.m_ethylene_coproduct:.4f}")
        print(f"  Total energy demand (MJ)         = {self.E_cracker:.4f}")
        print(f"  Natural gas demand (MJ)          = {self.E_NG_cracker:.4f}")
        
        print("="*80)
    
    def __init__(
        self,
        steam_cracker: SteamCrackerProcess | None = None,
        steam_cracker_kwargs: dict | None = None,
        **sc_params  # Catch sc_* parameters
    ):
        """
        Create a propylene from steam cracking process model
        
        To see all available parameters, run:
            PropyleneSCProcess.show_parameters()
        
        Args:
            steam_cracker: Pre-built SteamCrackerProcess instance (optional)
            steam_cracker_kwargs: Dict of parameters for SteamCrackerProcess (optional)
            **sc_params: Steam cracker parameters with 'sc_' prefix
                        (e.g., sc_f_butane, sc_thermal_eff, sc_Y_ethylene_naphtha)
        """
        
        # Reference product: 1 kg propylene
        self.m_propylene_ref = 1.0
        
        # ── Propylene-relevant feed defaults ──────────────────────────
        # The SteamCrackerProcess defaults are ethylene-oriented (75.6%
        # ethane).  For propylene, the crackers that actually contribute
        # significant propylene are predominantly naphtha- and LPG-fed.
        # These defaults reflect the global propylene-from-SC supply mix.
        PROPYLENE_SC_DEFAULTS = {
            'f_naphtha': 0.45,
            'f_propane': 0.30,
            'f_butane':  0.15,
            'f_ethane':  0.05,
            'f_gasoil':  0.05,
        }

        # Extract steam cracker parameters from sc_* prefixed kwargs
        extracted_sc_params = {}
        for key, value in sc_params.items():
            if key.startswith('sc_'):
                # Remove sc_ prefix: 'sc_f_butane' → 'f_butane'
                clean_key = key[3:]
                extracted_sc_params[clean_key] = value
            else:
                print(f"Warning: Unknown parameter '{key}'")
                print(f"   Steam cracker params should be prefixed with 'sc_'")

        # Build steam cracker
        if steam_cracker is not None:
            self.steam_cracker = steam_cracker
        else:
            # Start with propylene-relevant defaults, then layer user overrides
            if steam_cracker_kwargs is None:
                steam_cracker_kwargs = {}
            merged = {**PROPYLENE_SC_DEFAULTS, **steam_cracker_kwargs, **extracted_sc_params}

            self.steam_cracker = SteamCrackerProcess(**merged)
        
        # ========== ALLOCATION-BASED RE-REFERENCING ==========
        # The steam cracker is a multi-output process. Its attributes (m_naphtha,
        # E_cracker, etc.) are UNALLOCATED totals per 1 kg ethylene produced.
        # To get propylene's share, we apply PROPYLENE's economic allocation
        # factor directly, then scale to 1 kg propylene.
        #
        # Correct formula:
        #   flow_per_kg_propylene = flow_unallocated × AF_propylene / m_propylene
        #
        # Where:
        #   AF_propylene = economic allocation factor for propylene
        #   m_propylene  = unallocated propylene mass per kg ethylene
        #
        # Previously, the code used scale_factor = 1/m_propylene which applied
        # NO allocation, attributing the full unallocated burden to propylene.
        # This overestimated propylene's share by ~1/AF_propylene ≈ 5×.

        propylene_per_kg_ethylene = self.steam_cracker.m_propylene

        if propylene_per_kg_ethylene <= 0:
            raise ValueError(
                f"Steam cracker produces {propylene_per_kg_ethylene} kg propylene per kg ethylene. "
                "Cannot re-reference to propylene basis. Check feedstock mix."
            )

        # Get propylene's economic allocation factor from the cracker
        self.AF_propylene = self.steam_cracker.AF_propylene

        # Scale factor: AF_propylene / m_propylene
        # This converts unallocated-per-kg-ethylene → allocated-per-kg-propylene
        self.scale_factor = self.AF_propylene / propylene_per_kg_ethylene
        
        # ========== SCALED FEED REQUIREMENTS ==========
        self.m_feed_total = self.steam_cracker.m_feed_total * self.scale_factor
        self.m_butane = self.steam_cracker.m_butane * self.scale_factor
        self.m_ethane = self.steam_cracker.m_ethane * self.scale_factor
        self.m_gasoil = self.steam_cracker.m_gasoil * self.scale_factor
        self.m_naphtha = self.steam_cracker.m_naphtha * self.scale_factor
        self.m_propane = self.steam_cracker.m_propane * self.scale_factor
        
        # ========== SCALED ENERGY REQUIREMENTS ==========
        self.E_cracker = self.steam_cracker.E_cracker * self.scale_factor
        self.E_NG_cracker = self.steam_cracker.E_NG_cracker * self.scale_factor
        self.E_hydrogen_combusted = self.steam_cracker.E_hydrogen_combusted * self.scale_factor
        self.E_methane_combusted = self.steam_cracker.E_methane_combusted * self.scale_factor
        sc_elec_total = self.steam_cracker.E_base_electricity + self.steam_cracker.E_H2_purification
        self.E_electricity_total = sc_elec_total * self.scale_factor
        
        # ========== SCALED CO-PRODUCTS ==========
        # Ethylene is now a CO-PRODUCT (not the main product)
        self.m_ethylene_coproduct = self.steam_cracker.m_ethylene * self.scale_factor
        self.m_butadiene = self.steam_cracker.m_butadiene * self.scale_factor
        self.m_btx = self.steam_cracker.m_btx * self.scale_factor
        self.m_hydrogen_output = self.steam_cracker.m_hydrogen_output * self.scale_factor
        self.m_methane_output = self.steam_cracker.m_methane_output * self.scale_factor
        self.m_fueloil = self.steam_cracker.m_fueloil * self.scale_factor
        
        # ========== LCI FLOWS (per kg propylene) ==========
        self.input_flows = {
            "butane": self.m_butane,
            "ethane": self.m_ethane,
            "gasoil": self.m_gasoil,
            "naphtha": self.m_naphtha,
            "propane": self.m_propane,
            "heat, hydrogen gas combustion": self.E_hydrogen_combusted,
            "heat, methane gas combustion": self.E_methane_combusted,
            "heat, natural gas combustion": self.E_NG_cracker,
            "electricity, medium voltage": self.E_electricity_total,
        }
        
        self.output_flows = {
            "propylene": self.m_propylene_ref,  # Main product: 1 kg
            "ethylene": self.m_ethylene_coproduct,  # Now a co-product!
            "butadiene": self.m_butadiene,
            "benzene": self.m_btx,
            "hydrogen, gaseous, low pressure": self.m_hydrogen_output,
            "methane": self.m_methane_output,
            "heavy fuel oil": self.m_fueloil,
        }
    
    def to_dict(self):
        """Export complete parameter set and flows for LCA integration"""
        return {
            "parameters": {
                "reference_product": "propylene",
                "reference_quantity_kg": self.m_propylene_ref,
                "scale_factor_from_ethylene_basis": self.scale_factor,
                "steam_cracker_parameters": self.steam_cracker.to_dict()["parameters"],
            },
            "input_flows": self.input_flows,
            "output_flows": self.output_flows,
        }
    
    def get_propylene_yield_info(self):
        """
        Get detailed information about propylene yield from the steam cracker
        
        Returns:
            dict: Propylene yield breakdown by feedstock
        """
        sc = self.steam_cracker
        return {
            "propylene_per_kg_ethylene": sc.m_propylene,
            "ethylene_per_kg_propylene": self.m_ethylene_coproduct,
            "propylene_yields_by_feed": {
                "butane": sc.y_propylene_butane,
                "ethane": sc.y_propylene_ethane,
                "gasoil": sc.y_propylene_gasoil,
                "naphtha": sc.y_propylene_naphtha,
                "propane": sc.y_propylene_propane,
            },
            "feed_contributions_to_propylene": {
                "from_butane": sc.m_butane * sc.y_propylene_butane * self.scale_factor,
                "from_ethane": sc.m_ethane * sc.y_propylene_ethane * self.scale_factor,
                "from_gasoil": sc.m_gasoil * sc.y_propylene_gasoil * self.scale_factor,
                "from_naphtha": sc.m_naphtha * sc.y_propylene_naphtha * self.scale_factor,
                "from_propane": sc.m_propane * sc.y_propylene_propane * self.scale_factor,
            }
        }
