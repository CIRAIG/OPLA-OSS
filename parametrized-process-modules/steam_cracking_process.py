"""
Steam Cracking Process Module
=============================

This module provides the SteamCrackerProcess class, a complete mass and energy
balance model for steam cracking with configurable allocation methods for
co-product handling in Life Cycle Assessment (LCA).

The model is compliant with ISO 14044 standards and supports both:
- Economic allocation (allocation by mass × price)
- Mass allocation (allocation by mass)

Key Features:
    - Multi-feedstock capability (butane, ethane, propane, naphtha, gasoil)
    - Comprehensive co-product tracking (propylene, butadiene, hydrogen, methane, BTX)
    - Regional price library (6 markets)
    - Configurable yield scalars and energy recovery
    - Transparent mass and energy balance calculations
    - ISO 14044 compliant allocation methods

Quick Start:
    >>> from steam_cracking_process import SteamCrackerProcess
    >>> sc = SteamCrackerProcess(region='canada')
    >>> sc.print_current_parameters()

Module Contents:
    - REGIONAL_PRICES: Dict of commodity prices by region
    - SteamCrackerProcess: Main process modeling class
"""

"""
SteamCrackerProcess Class
----------------------------------------------------------------------

This class implements a complete mass and energy balance model for steam cracking
with CONFIGURABLE ALLOCATION METHODS for co-product handling in Life Cycle
Assessment (LCA), compliant with ISO 14044 standards.

Process Overview:
    [Mixed Feedstocks] ──→ [Steam Cracker] ──→ [Ethylene + Co-products]
         (Butane, Ethane,                        (Propylene, Butadiene,
          Propane, Naphtha,                       H2, CH4, BTX, etc.)
          Gasoil)

This class allocates all environmental burdens (feedstocks, energy) to products
using either ECONOMIC ALLOCATION or MASS ALLOCATION, following ISO 14044
guidelines for allocation in multi-output processes.

Allocation Methods (ISO 14044 Section 4.3.4):
---------------------------------------------

1. ECONOMIC ALLOCATION (default):
   Allocation Factor:  AF_j = (m_j × p_j) / Σ(m_k × p_k)

   Where:
   - AF_j = allocation factor for product j [-]
   - m_j  = mass of product j [kg]
   - p_j  = market price of product j [USD/kg]
   - Σ    = sum over all co-products k

   Economic allocation reflects the economic purpose driving production
   and is preferred when products have significantly different values
   per unit mass (e.g., hydrogen vs. fuel oil).

2. MASS ALLOCATION:
   Allocation Factor:  AF_j = m_j / Σ(m_k)

   Where:
   - AF_j = allocation factor for product j [-]
   - m_j  = mass of product j [kg]
   - Σ    = sum over all co-products k

   Mass allocation is based purely on physical relationships and is
   appropriate when products are physically similar or when economic
   data is unavailable or unreliable.

The model is designed as a reusable upstream process that can supply:
- Ethylene for downstream applications (PE, PET, PVC, MEG production)
- Propylene for polypropylene (PP) production
- Other co-products as needed

Key Features:
- Dual allocation methods: economic (mass × price) or mass-based (ISO 14044)
- Multi-feedstock capability with automatic normalization (5 feedstock types)
- Comprehensive co-product tracking (propylene, butadiene, hydrogen, BTX, etc.)
- Regional price library with 6 markets (Global, North America, Canada, Europe, China, Middle East)
- Configurable commodity prices for economic allocation
- Selectable reference product for allocated results
- Configurable energy recovery (H2/CH4 combustion vs. co-product recovery)
- Yield scalars for ethylene selectivity improvement
- Proper allocation of post-processing energy to specific co-products
- Transparent mass and energy balance calculations with mass conservation
- Built-in parameter discovery and validation

Mathematical Model - Equations Implemented:
--------------------------------------------

1. Total feed required per kg ethylene (basis):
   m_feed_total = 1 / Σ(f_i × y_i,ethylene)

   Where:
   - f_i = mass fraction of feedstock i [-]
   - y_i,ethylene = ethylene yield from feedstock i [kg ethylene/kg feedstock]

2. Ethylene contribution shares per feed:
   s_i = (f_i × y_i,ethylene) / Σ(f_j × y_j,ethylene)

   Where:
   - s_i = contribution share of feedstock i to total ethylene production [-]

3. Cracker energy demand (total, before allocation):
   E_cracker = Σ(s_i × E_i) / η

   Where:
   - s_i = contribution share of feedstock i to ethylene production [-]
   - E_i = specific energy demand for feedstock i [MJ/kg ethylene]
         (Source: Ullmann's Encyclopedia of Industrial Chemistry)
   - η = thermal efficiency of cracker [-]

   Note: This formulation uses the Ullmann's source values directly
   (MJ/kg ethylene), weighted by each feedstock's ethylene contribution
   share s_i. This is mathematically equivalent to Σ(m_i × e_i) / η
   since s_i × E_i = m_i × e_i, but preserves the source data as-is.

4. Off-gas combustion energy recovery:
   E_H2 = f_H2_comb × h_H2 × Σ(m_i × y_i,H2)
   E_CH4 = f_CH4_comb × h_CH4 × Σ(m_i × y_i,CH4)

   Where:
   - f_H2_comb, f_CH4_comb = fractions of H2/CH4 combusted onsite [-]
   - h_H2, h_CH4 = lower heating values [MJ/kg]
   - m_i = mass of feedstock i [kg]
   - y_i,H2, y_i,CH4 = H2/CH4 yields from feedstock i [kg/kg feedstock]

5. Natural gas demand (cracker, before allocation):
   E_NG_cracker = E_cracker - (E_H2 + E_CH4)

6. Co-product mass flows (per kg ethylene basis):
   m_product = Σ(m_i × y_i,product)

7. Yield scaling with mass balance conservation:
   y_ethylene_new = y_ethylene_orig × Y_scalar
   scale_others = (Total - y_eth_new) / (Total - y_eth_orig)
   y_product_new = y_product_orig × scale_others

   This ensures: Σ(all products) = constant (mass conservation)

8. Economic Value of each product:
   EV_j = m_j × p_j

   Where:
   - EV_j = economic value of product j [USD]
   - m_j = mass of product j [kg]
   - p_j = market price of product j [USD/kg]

9. Allocation Factor for product j (method-dependent):

   ECONOMIC ALLOCATION (allocation_method='economic'):
   AF_j = EV_j / Σ(EV_k) = (m_j × p_j) / Σ(m_k × p_k)

   MASS ALLOCATION (allocation_method='mass'):
   AF_j = m_j / Σ(m_k)

   Where:
   - AF_j = allocation factor for product j [-]
   - Σ(AF_j) = 1 (by definition, regardless of method)
   - Method is selected via allocation_method parameter

10. Allocated shared inputs per kg of reference product r:
    I_r,allocated = I_total × AF_r × SF_r

    Where:
    - I_total = total input (feedstock or energy) for 1 kg ethylene basis
    - AF_r = allocation factor for reference product r [-]
    - SF_r = 1/m_r = scaling factor [kg⁻¹]

11. Product-specific post-processing allocation:

    Base electricity (shared among all products):
      E_base = 0.121 kWh/kg ethylene basis

    H2 purification (allocated ONLY to hydrogen):
      E_H2_purif = m_H2_output × e_purif
      where e_purif = 0.500 kWh/kg H2

    CH4 compression (allocated ONLY to methane):
      E_NG_compress = m_CH4_output × f_compress × h_NG
      where f_compress = 0.0116 kg NG/kg CH4

12. Total allocated energy for reference product r:

    For hydrogen:
      E_elec = E_base × AF_H2 × SF_H2 + E_H2_purif × SF_H2

    For methane:
      E_NG = E_NG_cracker × AF_CH4 × SF_CH4 + E_NG_compress × SF_CH4

    For other products:
      E_elec = E_base × AF_r × SF_r  (no H2 purification)
      E_NG = E_NG_cracker × AF_r × SF_r  (no CH4 compression)

Process Assumptions:
--------------------
1. Ethyne/propyne hydrogenated to ethylene/propylene (yields aggregated)
2. All C4 compounds grouped as butadiene co-product
3. BTX (aromatics) grouped as benzene equivalent
4. Methane used as tail gas (combustion only unless recovered)
5. Hydrogen can be combusted or recovered as co-product
6. Yield improvements represent selectivity changes (trade-off between products)
7. Total product mass from each feedstock remains constant
8. Allocation method is user-selectable: economic (mass × price) or mass-based
9. For economic allocation: market prices at point of production are used
10. Shared inputs allocated to all products proportionally by allocation factor
11. Post-processing inputs allocated only to the specific co-product requiring them

Quick Start:
-----------
1. See all available parameters:
   >>> SteamCrackerProcess.show_parameters()

2. List available price regions:
   >>> SteamCrackerProcess.list_price_regions()

3. View prices for a specific region:
   >>> SteamCrackerProcess.show_regional_prices('canada')

4. Create model with ECONOMIC ALLOCATION and regional prices (RECOMMENDED):
   >>> sc = SteamCrackerProcess(
           region='canada',
           allocation_method='economic',  # AF = (m × p) / Σ(m × p)
           f_naphtha=0.8,
           f_ethane=0.2,
           reference_product='ethylene'
       )

5. Create model with MASS ALLOCATION:
   >>> sc = SteamCrackerProcess(
           region='canada',
           allocation_method='mass',  # AF = m / Σm
           f_naphtha=0.8,
           f_ethane=0.2,
           reference_product='ethylene'
       )

6. Create model with custom prices (economic allocation):
   >>> sc = SteamCrackerProcess(
           f_naphtha=0.8,
           f_ethane=0.2,
           price_ethylene=1.15,
           allocation_method='economic',
           reference_product='ethylene'
       )

7. View current settings and allocation results:
   >>> sc.print_current_parameters()

8. Get allocated inputs for any product:
   >>> inputs = sc.get_allocated_inputs_for_product('propylene')

9. Compare allocation methods:
   >>> sc_econ = SteamCrackerProcess(region='canada', allocation_method='economic')
   >>> sc_mass = SteamCrackerProcess(region='canada', allocation_method='mass')
   >>> print(f"Ethylene AF (economic): {sc_econ.AF_ethylene:.2%}")
   >>> print(f"Ethylene AF (mass):     {sc_mass.AF_ethylene:.2%}")
"""


# =============================================================================
# REGIONAL PRICE LIBRARY
# =============================================================================
# Commodity prices in USD/kg for different global markets
# Sources: ICIS, Platts, regional market reports (2024-2025 averages)
#
# Notes on hydrogen prices:
#   - Global Avg: Mixed production methods
#   - North America: Grey hydrogen (SMR)
#   - Canada (Alberta/Sarnia): Blue hydrogen (SMR + CCS)
#   - Europe (NWE/TTF): Green hydrogen (electrolysis)
#   - China (CFR/Spot): Coal gasification
#   - Middle East (FOB/Netback): Green hydrogen target price
# =============================================================================

REGIONAL_PRICES = {
    'global': {
        'name': 'Global Average',
        'description': 'Weighted global average prices across all markets',
        'prices': {
            'ethylene': 0.65,
            'propylene': 1.01,
            'butadiene': 1.04,
            'btx': 0.79,          # Benzene equivalent
            'methane': 0.37,
            'hydrogen': 2.50,     # Mixed production
            'fueloil': 0.51,      # VLSFO
        }
    },
    'north_america': {
        'name': 'North America',
        'description': 'US Gulf Coast and Mont Belvieu pricing',
        'prices': {
            'ethylene': 0.43,
            'propylene': 0.83,
            'butadiene': 0.65,
            'btx': 0.81,
            'methane': 0.18,
            'hydrogen': 1.16,     # Grey hydrogen (SMR)
            'fueloil': 0.46,
        }
    },
    'canada': {
        'name': 'Canada (Alberta/Sarnia)',
        'description': 'Canadian petrochemical hubs pricing',
        'prices': {
            'ethylene': 0.41,
            'propylene': 0.80,
            'butadiene': 0.65,
            'btx': 0.79,
            'methane': 0.09,
            'hydrogen': 1.50,     # Blue hydrogen (SMR + CCS)
            'fueloil': 0.48,
        }
    },
    'europe': {
        'name': 'Europe (NWE/TTF)',
        'description': 'Northwest Europe and TTF gas pricing',
        'prices': {
            'ethylene': 0.74,
            'propylene': 1.08,
            'butadiene': 1.12,
            'btx': 0.74,
            'methane': 0.55,
            'hydrogen': 7.35,     # Green hydrogen (electrolysis)
            'fueloil': 0.46,
        }
    },
    'china': {
        'name': 'China (CFR/Spot)',
        'description': 'Chinese domestic and CFR import pricing',
        'prices': {
            'ethylene': 0.69,
            'propylene': 0.95,
            'butadiene': 1.27,
            'btx': 0.78,
            'methane': 0.59,
            'hydrogen': 3.50,     # Coal gasification
            'fueloil': 0.50,
        }
    },
    'middle_east': {
        'name': 'Middle East (FOB/Netback)',
        'description': 'Gulf Cooperation Council FOB and netback pricing',
        'prices': {
            'ethylene': 0.63,
            'propylene': 1.17,
            'butadiene': 1.10,
            'btx': 0.73,
            'methane': 0.25,
            'hydrogen': 2.00,     # Green hydrogen target
            'fueloil': 0.48,
        }
    },
}


class SteamCrackerProcess:

    @staticmethod
    def show_parameters(detailed=True):
        """Display all available parameters that can be varied"""
        print("="*80)
        print("AVAILABLE PARAMETERS FOR SteamCrackerProcess")
        print("="*80)

        if detailed:
            print("\n" + "FEEDSTOCK SHARES".center(80, "-"))
            print("  (Auto-normalized to sum to 1.0)")
            params = [
                ("f_butane", "Share of butane feedstock", 0.028),
                ("f_ethane", "Share of ethane feedstock", 0.756),
                ("f_gasoil", "Share of gasoil feedstock", 0.001),
                ("f_naphtha", "Share of naphtha feedstock", 0.061),
                ("f_propane", "Share of propane feedstock", 0.154),
            ]
            for name, desc, default in params:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + "YIELD SCALARS (Ethylene Selectivity)".center(80, "-"))
            print("  (1.0 = baseline, >1.0 = improved selectivity toward ethylene)")
            params = [
                ("Y_ethylene_butane", "Ethylene yield scalar for butane", 1.0),
                ("Y_ethylene_ethane", "Ethylene yield scalar for ethane", 1.0),
                ("Y_ethylene_gasoil", "Ethylene yield scalar for gasoil", 1.0),
                ("Y_ethylene_naphtha", "Ethylene yield scalar for naphtha", 1.0),
                ("Y_ethylene_propane", "Ethylene yield scalar for propane", 1.0),
            ]
            for name, desc, default in params:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + "COMBUSTION & EFFICIENCY".center(80, "-"))
            params = [
                ("f_h2_combusted", "Fraction of H2 combusted onsite", 0.7),
                ("f_ch4_combusted", "Fraction of CH4 combusted onsite", 1.0),
                ("thermal_eff", "Thermal efficiency of cracker", 0.89),
            ]
            for name, desc, default in params:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + "COMMODITY PRICES (USD/kg)".center(80, "-"))
            params = [
                ("price_ethylene", "Market price of ethylene", 1.00),
                ("price_propylene", "Market price of propylene", 0.95),
                ("price_butadiene", "Market price of butadiene", 1.20),
                ("price_btx", "Market price of BTX", 0.85),
                ("price_hydrogen", "Market price of hydrogen", 2.50),
                ("price_methane", "Market price of methane", 0.30),
                ("price_fueloil", "Market price of fuel oil", 0.40),
            ]
            for name, desc, default in params:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + "REFERENCE PRODUCT".center(80, "-"))
            print(f"  {'reference_product':25s} : {'Product for allocated results':40s} [default: 'ethylene']")
            print("  Options: 'ethylene', 'propylene', 'butadiene', 'btx', 'hydrogen', 'methane', 'fueloil'")

            print("\n" + "ALLOCATION METHOD (ISO 14044)".center(80, "-"))
            print(f"  {'allocation_method':25s} : {'Method for burden allocation':40s} [default: 'economic']")
            print("  Options:")
            print("    'economic' : AF = (m × p) / Σ(m × p)  [allocation by economic value]")
            print("    'mass'     : AF = m / Σm              [allocation by mass]")

        print("="*80)

    @staticmethod
    def get_parameter_template(format='dict'):
        """Get a template showing all parameters and their defaults"""
        template = {
            'f_butane': 0.028, 'f_ethane': 0.756, 'f_gasoil': 0.001,
            'f_naphtha': 0.061, 'f_propane': 0.154,
            'Y_ethylene_butane': 1.0, 'Y_ethylene_ethane': 1.0,
            'Y_ethylene_gasoil': 1.0, 'Y_ethylene_naphtha': 1.0,
            'Y_ethylene_propane': 1.0,
            'f_h2_combusted': 0.7, 'f_ch4_combusted': 1.0, 'thermal_eff': 0.89,
            'price_ethylene': 1.00, 'price_propylene': 0.95,
            'price_butadiene': 1.20, 'price_btx': 0.85,
            'price_hydrogen': 2.50, 'price_methane': 0.30, 'price_fueloil': 0.40,
            'reference_product': 'ethylene',
            'allocation_method': 'economic',
        }
        if format == 'json':
            import json
            return json.dumps(template, indent=2)
        return template

    @staticmethod
    def list_parameters():
        """Quick list of all parameter names (autocomplete-friendly)"""
        return [
            'f_butane', 'f_ethane', 'f_gasoil', 'f_naphtha', 'f_propane',
            'Y_ethylene_butane', 'Y_ethylene_ethane', 'Y_ethylene_gasoil',
            'Y_ethylene_naphtha', 'Y_ethylene_propane',
            'f_h2_combusted', 'f_ch4_combusted', 'thermal_eff',
            'price_ethylene', 'price_propylene', 'price_butadiene',
            'price_btx', 'price_hydrogen', 'price_methane', 'price_fueloil',
            'reference_product', 'allocation_method'
        ]

    # =========================================================================
    # REGIONAL PRICE METHODS
    # =========================================================================

    @staticmethod
    def list_price_regions():
        """
        List all available price regions.

        Returns:
            List of region codes that can be used with get_regional_prices()
        """
        print("=" * 70)
        print("AVAILABLE PRICE REGIONS")
        print("=" * 70)
        for code, data in REGIONAL_PRICES.items():
            print(f"  '{code}': {data['name']}")
            print(f"      {data['description']}")
        print("=" * 70)
        return list(REGIONAL_PRICES.keys())

    @staticmethod
    def get_regional_prices(region):
        """
        Get price dictionary for a specific region.

        Args:
            region: Region code ('global', 'north_america', 'canada',
                    'europe', 'china', 'middle_east')

        Returns:
            Dictionary with price_* keys ready to unpack into __init__
        """
        region = region.lower().replace(' ', '_').replace('-', '_')
        if region not in REGIONAL_PRICES:
            available = list(REGIONAL_PRICES.keys())
            raise ValueError(f"Unknown region '{region}'. Available: {available}")

        prices = REGIONAL_PRICES[region]['prices']
        return {
            'price_ethylene': prices['ethylene'],
            'price_propylene': prices['propylene'],
            'price_butadiene': prices['butadiene'],
            'price_btx': prices['btx'],
            'price_hydrogen': prices['hydrogen'],
            'price_methane': prices['methane'],
            'price_fueloil': prices['fueloil'],
        }

    @staticmethod
    def show_regional_prices(region=None):
        """
        Display prices for a specific region or all regions.

        Args:
            region: Optional region code. If None, shows all regions.
        """
        if region is None:
            # Show comparison table
            print("=" * 100)
            print("REGIONAL COMMODITY PRICES (USD/kg)")
            print("=" * 100)
            print(f"{'Commodity':<12} {'Global':>10} {'N.America':>10} {'Canada':>10} {'Europe':>10} {'China':>10} {'M.East':>10}")
            print("-" * 100)

            commodities = ['ethylene', 'propylene', 'butadiene', 'btx', 'methane', 'hydrogen', 'fueloil']
            regions = ['global', 'north_america', 'canada', 'europe', 'china', 'middle_east']

            for comm in commodities:
                row = f"{comm:<12}"
                for reg in regions:
                    price = REGIONAL_PRICES[reg]['prices'][comm]
                    row += f" {price:>9.2f}"
                print(row)
            print("=" * 100)
        else:
            region = region.lower().replace(' ', '_').replace('-', '_')
            if region not in REGIONAL_PRICES:
                available = list(REGIONAL_PRICES.keys())
                raise ValueError(f"Unknown region '{region}'. Available: {available}")

            data = REGIONAL_PRICES[region]
            print("=" * 50)
            print(f"PRICES FOR: {data['name']}")
            print(f"  {data['description']}")
            print("=" * 50)
            for comm, price in data['prices'].items():
                print(f"  {comm:<12}: ${price:.2f}/kg")
            print("=" * 50)

    def print_current_parameters(self):
        """Display the current parameter values of this instance"""
        print("="*80)
        print("STEAM CRACKER PROCESS - ECONOMIC ALLOCATION")
        print("="*80)

        print("\n FEEDSTOCK SHARES (normalized):")
        print(f"  f_butane  = {self.f_butane_share_cracking:.6f}")
        print(f"  f_ethane  = {self.f_ethane_share_cracking:.6f}")
        print(f"  f_gasoil  = {self.f_gasoil_share_cracking:.6f}")
        print(f"  f_naphtha = {self.f_naphtha_share_cracking:.6f}")
        print(f"  f_propane = {self.f_propane_share_cracking:.6f}")

        print("\n YIELD SCALARS:")
        print(f"  Y_ethylene_butane  = {self.Y_ethylene_butane:.4f}")
        print(f"  Y_ethylene_ethane  = {self.Y_ethylene_ethane:.4f}")
        print(f"  Y_ethylene_gasoil  = {self.Y_ethylene_gasoil:.4f}")
        print(f"  Y_ethylene_naphtha = {self.Y_ethylene_naphtha:.4f}")
        print(f"  Y_ethylene_propane = {self.Y_ethylene_propane:.4f}")

        print("\n COMBUSTION & EFFICIENCY:")
        print(f"  f_h2_combusted  = {self.f_hydrogen_combusted_cracker:.2f}")
        print(f"  f_ch4_combusted = {self.f_methane_combusted_cracker:.2f}")
        print(f"  thermal_eff     = {self.thermal_efficiency_cracker:.4f}")

        print("\n COMMODITY PRICES (USD/kg):")
        print(f"  price_ethylene  = {self.price_ethylene:.2f}")
        print(f"  price_propylene = {self.price_propylene:.2f}")
        print(f"  price_butadiene = {self.price_butadiene:.2f}")
        print(f"  price_btx       = {self.price_btx:.2f}")
        print(f"  price_hydrogen  = {self.price_hydrogen:.2f}")
        print(f"  price_methane   = {self.price_methane:.2f}")
        print(f"  price_fueloil   = {self.price_fueloil:.2f}")

        print(f"\n REFERENCE PRODUCT: {self.reference_product}")

        print("\n" + "-"*80)
        print(" MASS BALANCE (per 1 kg ethylene basis):")
        print("-"*80)
        print(f"  Total feed required     = {self.m_feed_total:.4f} kg")
        print(f"  Ethylene produced       = {self.m_ethylene:.4f} kg")
        print(f"  Propylene produced      = {self.m_propylene:.4f} kg")
        print(f"  Butadiene produced      = {self.m_butadiene:.4f} kg")
        print(f"  BTX produced            = {self.m_btx:.4f} kg")
        print(f"  Hydrogen output         = {self.m_hydrogen_output:.4f} kg")
        print(f"  Methane output          = {self.m_methane_output:.4f} kg")
        print(f"  Fuel oil produced       = {self.m_fueloil:.4f} kg")

        print("\n" + "-"*80)
        print(" CRACKER ENERGY BY FEEDSTOCK (Source: Ullmann's):")
        print("-"*80)
        print(f"  E_ethane  = {self.E_ethane:.1f} MJ/kg ethylene")
        print(f"  E_propane = {self.E_propane:.1f} MJ/kg ethylene")
        print(f"  E_butane  = {self.E_butane:.1f} MJ/kg ethylene")
        print(f"  E_naphtha = {self.E_naphtha:.1f} MJ/kg ethylene")
        print(f"  E_gasoil  = {self.E_gasoil:.1f} MJ/kg ethylene")

        print("\n" + "-"*80)
        print(" ENERGY BALANCE (per 1 kg ethylene basis, before allocation):")
        print("-"*80)
        print(f"  Cracker energy (total)  = {self.E_cracker:.4f} MJ  [Σ(s_i × E_i) / η]")
        print(f"  H2 combustion recovery  = {self.E_hydrogen_combusted:.4f} MJ")
        print(f"  CH4 combustion recovery = {self.E_methane_combusted:.4f} MJ")
        print(f"  NG for cracker          = {self.E_NG_cracker:.4f} MJ")
        print(f"  Base electricity        = {self.E_base_electricity:.4f} kWh  (shared)")
        print(f"  H2 purification elec.   = {self.E_H2_purification:.4f} kWh  (H2-specific)")
        print(f"  CH4 compression NG      = {self.E_NG_CH4_compression:.4f} MJ   (CH4-specific)")

        print("\n" + "-"*80)
        method_name = "ECONOMIC" if self.allocation_method == 'economic' else "MASS"
        print(f" {method_name} ALLOCATION (ISO 14044):")
        print("-"*80)
        print(f"  Allocation method       = {self.allocation_method.upper()}")
        print(f"  Total product mass      = {self.total_product_mass:.4f} kg")
        print(f"  Total economic value    = ${self.total_economic_value:.4f}")

        if self.allocation_method == 'economic':
            print(f"\n  Economic Values (EV_j = m_j × p_j):")
            print(f"    EV_ethylene   = ${self.EV_ethylene:.4f}")
            print(f"    EV_propylene  = ${self.EV_propylene:.4f}")
            print(f"    EV_butadiene  = ${self.EV_butadiene:.4f}")
            print(f"    EV_btx        = ${self.EV_btx:.4f}")
            print(f"    EV_hydrogen   = ${self.EV_hydrogen:.4f}")
            print(f"    EV_methane    = ${self.EV_methane:.4f}")
            print(f"    EV_fueloil    = ${self.EV_fueloil:.4f}")
            print(f"\n  Allocation Factors (AF_j = EV_j / Σ EV_k):")
        else:
            print(f"\n  Allocation Factors (AF_j = m_j / Σ m_k):")

        print(f"    AF_ethylene   = {self.AF_ethylene:.4f} ({self.AF_ethylene*100:.2f}%)")
        print(f"    AF_propylene  = {self.AF_propylene:.4f} ({self.AF_propylene*100:.2f}%)")
        print(f"    AF_butadiene  = {self.AF_butadiene:.4f} ({self.AF_butadiene*100:.2f}%)")
        print(f"    AF_btx        = {self.AF_btx:.4f} ({self.AF_btx*100:.2f}%)")
        print(f"    AF_hydrogen   = {self.AF_hydrogen:.4f} ({self.AF_hydrogen*100:.2f}%)")
        print(f"    AF_methane    = {self.AF_methane:.4f} ({self.AF_methane*100:.2f}%)")
        print(f"    AF_fueloil    = {self.AF_fueloil:.4f} ({self.AF_fueloil*100:.2f}%)")
        print(f"    Σ AF_j        = {sum(self.allocation_factors.values()):.4f} (verification)")

        print("\n" + "-"*80)
        print(f" ALLOCATED RESULTS (per 1 kg {self.reference_product}):")
        print("-"*80)
        print(f"  Allocation factor       = {self.AF_reference:.4f}")
        print(f"  Mass produced           = {self.mass_reference:.4f} kg (per kg ethylene basis)")
        print(f"  Scale factor (1/m_r)    = {self.scale_to_reference:.4f}")
        print(f"\n  Allocated Feedstock:")
        print(f"    Butane                = {self.allocated_m_butane:.6f} kg")
        print(f"    Ethane                = {self.allocated_m_ethane:.6f} kg")
        print(f"    Gasoil                = {self.allocated_m_gasoil:.6f} kg")
        print(f"    Naphtha               = {self.allocated_m_naphtha:.6f} kg")
        print(f"    Propane               = {self.allocated_m_propane:.6f} kg")
        print(f"    Total feed            = {self.allocated_m_feed_total:.6f} kg")
        print(f"\n  Allocated Energy:")
        print(f"    NG (cracker share)    = {self.allocated_E_NG_cracker:.4f} MJ")
        print(f"    NG (CH4 compression)  = {self.allocated_E_NG_CH4_compression:.4f} MJ")
        print(f"    NG (total)            = {self.allocated_E_NG_total:.4f} MJ")
        print(f"    Elec (base share)     = {self.allocated_E_base_electricity:.4f} kWh")
        print(f"    Elec (H2 purification)= {self.allocated_E_H2_purification:.4f} kWh")
        print(f"    Elec (total)          = {self.allocated_E_electricity_total:.4f} kWh")

        print("="*80)

    def __init__(
        self,
        region=None,
        f_butane=0.028, f_ethane=0.756, f_gasoil=0.001,
        f_naphtha=0.061, f_propane=0.154,
        Y_ethylene_butane=1.0, Y_ethylene_ethane=1.0, Y_ethylene_gasoil=1.0,
        Y_ethylene_naphtha=1.0, Y_ethylene_propane=1.0,
        f_h2_combusted=0.7, f_ch4_combusted=1.0, thermal_eff=0.89,
        price_ethylene=None, price_propylene=None, price_butadiene=None,
        price_btx=None, price_hydrogen=None, price_methane=None, price_fueloil=None,
        reference_product='ethylene',
        allocation_method='economic'
    ):
        """
        Create a steam cracker process model with configurable allocation method.

        This model calculates mass and energy balances for steam cracking and
        allocates environmental burdens to co-products based on EITHER:
        - Economic value (mass × price) - ISO 14044 economic allocation
        - Mass only - ISO 14044 mass allocation

        Post-processing energy (H2 purification, CH4 compression) is allocated
        only to the respective co-products, not shared among all products.

        Args:
            region: Optional region code ('global', 'north_america', 'canada',
                    'europe', 'china', 'middle_east'). When provided, regional
                    prices are used as defaults. Explicit price_* arguments
                    override regional prices.
            f_butane to f_propane: Feedstock shares (auto-normalized to sum to 1.0)
            Y_ethylene_*: Yield scalars for ethylene selectivity (1.0 = baseline)
            f_h2_combusted: Fraction of H2 combusted on-site for energy [0-1]
            f_ch4_combusted: Fraction of CH4 combusted on-site for energy [0-1]
            thermal_eff: Cracker thermal efficiency [0-1]
            price_*: Commodity prices in USD/kg for economic allocation.
                    If None and region is provided, regional prices are used.
                    If None and region is None, hardcoded defaults are used.
            reference_product: Product for which allocated results are calculated
                              ('ethylene', 'propylene', 'butadiene', 'btx',
                               'hydrogen', 'methane', 'fueloil')
            allocation_method: 'economic' or 'mass'
                              - 'economic': AF = (m × p) / Σ(m × p)
                              - 'mass': AF = m / Σm
        """
        # Validate allocation method
        if allocation_method not in ['economic', 'mass']:
            raise ValueError(f"allocation_method must be 'economic' or 'mass', got '{allocation_method}'")
        self.allocation_method = allocation_method

        # Store region if provided
        self.price_region = region

        # Handle regional pricing with fallback to hardcoded defaults
        if region is not None:
            regional = SteamCrackerProcess.get_regional_prices(region)
            price_ethylene = price_ethylene if price_ethylene is not None else regional['price_ethylene']
            price_propylene = price_propylene if price_propylene is not None else regional['price_propylene']
            price_butadiene = price_butadiene if price_butadiene is not None else regional['price_butadiene']
            price_btx = price_btx if price_btx is not None else regional['price_btx']
            price_hydrogen = price_hydrogen if price_hydrogen is not None else regional['price_hydrogen']
            price_methane = price_methane if price_methane is not None else regional['price_methane']
            price_fueloil = price_fueloil if price_fueloil is not None else regional['price_fueloil']
        else:
            # No region - use hardcoded defaults for any None prices
            price_ethylene = price_ethylene if price_ethylene is not None else 1.00
            price_propylene = price_propylene if price_propylene is not None else 0.95
            price_butadiene = price_butadiene if price_butadiene is not None else 1.20
            price_btx = price_btx if price_btx is not None else 0.85
            price_hydrogen = price_hydrogen if price_hydrogen is not None else 2.50
            price_methane = price_methane if price_methane is not None else 0.30
            price_fueloil = price_fueloil if price_fueloil is not None else 0.40

        # Store prices
        self.price_ethylene = price_ethylene
        self.price_propylene = price_propylene
        self.price_butadiene = price_butadiene
        self.price_btx = price_btx
        self.price_hydrogen = price_hydrogen
        self.price_methane = price_methane
        self.price_fueloil = price_fueloil

        # Store reference product
        self.reference_product = reference_product

        # Store yield scalars
        self.Y_ethylene_butane = Y_ethylene_butane
        self.Y_ethylene_ethane = Y_ethylene_ethane
        self.Y_ethylene_gasoil = Y_ethylene_gasoil
        self.Y_ethylene_naphtha = Y_ethylene_naphtha
        self.Y_ethylene_propane = Y_ethylene_propane

        # Normalize feed shares
        total_share = f_butane + f_ethane + f_gasoil + f_naphtha + f_propane
        self.f_butane_share_cracking  = f_butane  / total_share
        self.f_ethane_share_cracking  = f_ethane  / total_share
        self.f_gasoil_share_cracking  = f_gasoil  / total_share
        self.f_naphtha_share_cracking = f_naphtha / total_share
        self.f_propane_share_cracking = f_propane / total_share

        # Combustion fractions
        self.f_hydrogen_combusted_cracker = f_h2_combusted
        self.f_methane_combusted_cracker  = f_ch4_combusted

        # Thermal efficiency
        self.thermal_efficiency_cracker = thermal_eff

        # Heating values (LHV, MJ/kg)
        self.h_hydrogen_cracker = 121.899
        self.h_methane_cracker  = 49.998

        # ==========================================
        # BASELINE YIELDS (from literature/data)
        # ==========================================

        # BUTANE baseline yields
        y_eth_bu_o = 0.41085 + 0.00427  # ethylene + ethyne
        y_pro_bu_o = 0.18635 + 0.0093   # propylene + propyne
        y_but_bu_o = 0.04375 + 0.001 + 0.03051  # C4 compounds
        y_btx_bu_o = 0.03007 + 0.00891 + 0.00269 + 0.00128 + 0.00011 + 0.01999
        y_h2_bu_o  = 0.01408
        y_ch4_bu_o = 0.22159
        y_fo_bu_o  = 0.011

        total_bu = y_eth_bu_o + y_pro_bu_o + y_but_bu_o + y_btx_bu_o + y_h2_bu_o + y_ch4_bu_o + y_fo_bu_o
        y_eth_bu_n = y_eth_bu_o * Y_ethylene_butane
        scale_bu = (total_bu - y_eth_bu_n) / (total_bu - y_eth_bu_o) if (total_bu - y_eth_bu_o) > 0 else 1.0

        self.y_ethylene_butane  = y_eth_bu_n
        self.y_propylene_butane = y_pro_bu_o * scale_bu
        self.y_butadiene_butane = y_but_bu_o * scale_bu
        self.y_btx_butane       = y_btx_bu_o * scale_bu
        self.y_hydrogen_butane  = y_h2_bu_o * scale_bu
        self.y_methane_butane   = y_ch4_bu_o * scale_bu
        self.y_fueloil_butane   = y_fo_bu_o * scale_bu

        # ETHANE baseline yields
        y_eth_et_o = 0.79931 + 0.00678
        y_pro_et_o = 0.01935 + 0.00033
        y_but_et_o = 0.02781 + 0.00077 + 0.003
        y_btx_et_o = 0.00855 + 0.00125 + 0.00047 + 0.00015 + 0.00544
        y_h2_et_o  = 0.06200
        y_ch4_et_o = 0.05845
        y_fo_et_o  = 0.003

        total_et = y_eth_et_o + y_pro_et_o + y_but_et_o + y_btx_et_o + y_h2_et_o + y_ch4_et_o + y_fo_et_o
        y_eth_et_n = y_eth_et_o * Y_ethylene_ethane
        scale_et = (total_et - y_eth_et_n) / (total_et - y_eth_et_o) if (total_et - y_eth_et_o) > 0 else 1.0

        self.y_ethylene_ethane  = y_eth_et_n
        self.y_propylene_ethane = y_pro_et_o * scale_et
        self.y_butadiene_ethane = y_but_et_o * scale_et
        self.y_btx_ethane       = y_btx_et_o * scale_et
        self.y_hydrogen_ethane  = y_h2_et_o * scale_et
        self.y_methane_ethane   = y_ch4_et_o * scale_et
        self.y_fueloil_ethane   = y_fo_et_o * scale_et

        # GASOIL baseline yields
        y_eth_go_o = 0.28352 + 0.00401
        y_pro_go_o = 0.14193 + 0.00633
        y_but_go_o = 0.05822 + 0.00123 + 0.03624
        y_btx_go_o = 0.05474 + 0.03496 + 0.01182 + 0.0092 + 0.0037 + 0.07301
        y_h2_go_o  = 0.00892
        y_ch4_go_o = 0.1085
        y_fo_go_o  = 0.163

        total_go = y_eth_go_o + y_pro_go_o + y_but_go_o + y_btx_go_o + y_h2_go_o + y_ch4_go_o + y_fo_go_o
        y_eth_go_n = y_eth_go_o * Y_ethylene_gasoil
        scale_go = (total_go - y_eth_go_n) / (total_go - y_eth_go_o) if (total_go - y_eth_go_o) > 0 else 1.0

        self.y_ethylene_gasoil  = y_eth_go_n
        self.y_propylene_gasoil = y_pro_go_o * scale_go
        self.y_butadiene_gasoil = y_but_go_o * scale_go
        self.y_btx_gasoil       = y_btx_go_o * scale_go
        self.y_hydrogen_gasoil  = y_h2_go_o * scale_go
        self.y_methane_gasoil   = y_ch4_go_o * scale_go
        self.y_fueloil_gasoil   = y_fo_go_o * scale_go

        # NAPHTHA baseline yields
        y_eth_na_o = 0.29578 + 0.00359
        y_pro_na_o = 0.16754 + 0.00602
        y_but_na_o = 0.04814 + 0.00095 + 0.05803
        y_btx_na_o = 0.06448 + 0.03095 + 0.01086 + 0.01171 + 0.00791 + 0.11299
        y_h2_na_o  = 0.01100
        y_ch4_na_o = 0.14168
        y_fo_na_o  = 0.027

        total_na = y_eth_na_o + y_pro_na_o + y_but_na_o + y_btx_na_o + y_h2_na_o + y_ch4_na_o + y_fo_na_o
        y_eth_na_n = y_eth_na_o * Y_ethylene_naphtha
        scale_na = (total_na - y_eth_na_n) / (total_na - y_eth_na_o) if (total_na - y_eth_na_o) > 0 else 1.0

        self.y_ethylene_naphtha  = y_eth_na_n
        self.y_propylene_naphtha = y_pro_na_o * scale_na
        self.y_butadiene_naphtha = y_but_na_o * scale_na
        self.y_btx_naphtha       = y_btx_na_o * scale_na
        self.y_hydrogen_naphtha  = y_h2_na_o * scale_na
        self.y_methane_naphtha   = y_ch4_na_o * scale_na
        self.y_fueloil_naphtha   = y_fo_na_o * scale_na

        # PROPANE baseline yields
        y_eth_pr_o = 0.43721 + 0.00532
        y_pro_pr_o = 0.16515 + 0.00579
        y_but_pr_o = 0.03252 + 0.00091 + 0.01121
        y_btx_pr_o = 0.02415 + 0.00482 + 0.00235 + 0.00056 + 0.00012 + 0.01428
        y_h2_pr_o  = 0.01868
        y_ch4_pr_o = 0.2621
        y_fo_pr_o  = 0.011

        total_pr = y_eth_pr_o + y_pro_pr_o + y_but_pr_o + y_btx_pr_o + y_h2_pr_o + y_ch4_pr_o + y_fo_pr_o
        y_eth_pr_n = y_eth_pr_o * Y_ethylene_propane
        scale_pr = (total_pr - y_eth_pr_n) / (total_pr - y_eth_pr_o) if (total_pr - y_eth_pr_o) > 0 else 1.0

        self.y_ethylene_propane  = y_eth_pr_n
        self.y_propylene_propane = y_pro_pr_o * scale_pr
        self.y_butadiene_propane = y_but_pr_o * scale_pr
        self.y_btx_propane       = y_btx_pr_o * scale_pr
        self.y_hydrogen_propane  = y_h2_pr_o * scale_pr
        self.y_methane_propane   = y_ch4_pr_o * scale_pr
        self.y_fueloil_propane   = y_fo_pr_o * scale_pr

        # ============ MASS BALANCE CALCULATIONS ============

        self.m_ethylene_basis = 1.0  # Reference: 1 kg ethylene

        # Mixed ethylene yield (Eq. 1 denominator)
        feed_ethylene_yield = (
            self.f_butane_share_cracking * self.y_ethylene_butane +
            self.f_ethane_share_cracking * self.y_ethylene_ethane +
            self.f_gasoil_share_cracking * self.y_ethylene_gasoil +
            self.f_naphtha_share_cracking * self.y_ethylene_naphtha +
            self.f_propane_share_cracking * self.y_ethylene_propane
        )

        # Total feed required (Eq. 1)
        self.m_feed_total = self.m_ethylene_basis / feed_ethylene_yield

        # Individual feedstock masses
        self.m_butane  = self.f_butane_share_cracking  * self.m_feed_total
        self.m_ethane  = self.f_ethane_share_cracking  * self.m_feed_total
        self.m_gasoil  = self.f_gasoil_share_cracking  * self.m_feed_total
        self.m_naphtha = self.f_naphtha_share_cracking * self.m_feed_total
        self.m_propane = self.f_propane_share_cracking * self.m_feed_total

        # Ethylene contribution shares (Eq. 2)
        self.s_butane  = (self.f_butane_share_cracking  * self.y_ethylene_butane)  / feed_ethylene_yield
        self.s_ethane  = (self.f_ethane_share_cracking  * self.y_ethylene_ethane)  / feed_ethylene_yield
        self.s_gasoil  = (self.f_gasoil_share_cracking  * self.y_ethylene_gasoil)  / feed_ethylene_yield
        self.s_naphtha = (self.f_naphtha_share_cracking * self.y_ethylene_naphtha) / feed_ethylene_yield
        self.s_propane = (self.f_propane_share_cracking * self.y_ethylene_propane) / feed_ethylene_yield

        # =============================================================
        # Cracker energy demand per kg ethylene, by feedstock type
        # Source: Ullmann's Encyclopedia of Industrial Chemistry
        # =============================================================
        self.E_ethane  = 16.0    # MJ/kg ethylene from ethane cracking
        self.E_propane = 20.0    # MJ/kg ethylene from propane cracking
        self.E_butane  = 21.5    # MJ/kg ethylene from butane cracking
        self.E_naphtha = 23.0    # MJ/kg ethylene from naphtha cracking
        self.E_gasoil  = 27.0    # MJ/kg ethylene from gas oil cracking

        # Cracker energy demand (Eq. 3): E_cracker = Σ(s_i × E_i) / η
        # Uses contribution shares (s_i) to weight each feedstock's energy
        # per kg ethylene (E_i), giving the mixed-feed energy per kg ethylene.
        E_cracker_ideal = (
            self.s_butane  * self.E_butane  +
            self.s_ethane  * self.E_ethane  +
            self.s_gasoil  * self.E_gasoil  +
            self.s_naphtha * self.E_naphtha +
            self.s_propane * self.E_propane
        )
        self.E_cracker = E_cracker_ideal / self.thermal_efficiency_cracker

        # ============ CO-PRODUCT MASSES (Eq. 6) ============

        self.m_ethylene = self.m_ethylene_basis  # 1.0 kg by definition

        self.m_propylene = (
            self.m_butane * self.y_propylene_butane + self.m_ethane * self.y_propylene_ethane +
            self.m_gasoil * self.y_propylene_gasoil + self.m_naphtha * self.y_propylene_naphtha +
            self.m_propane * self.y_propylene_propane
        )
        self.m_butadiene = (
            self.m_butane * self.y_butadiene_butane + self.m_ethane * self.y_butadiene_ethane +
            self.m_gasoil * self.y_butadiene_gasoil + self.m_naphtha * self.y_butadiene_naphtha +
            self.m_propane * self.y_butadiene_propane
        )
        self.m_btx = (
            self.m_butane * self.y_btx_butane + self.m_ethane * self.y_btx_ethane +
            self.m_gasoil * self.y_btx_gasoil + self.m_naphtha * self.y_btx_naphtha +
            self.m_propane * self.y_btx_propane
        )
        self.m_fueloil = (
            self.m_butane * self.y_fueloil_butane + self.m_ethane * self.y_fueloil_ethane +
            self.m_gasoil * self.y_fueloil_gasoil + self.m_naphtha * self.y_fueloil_naphtha +
            self.m_propane * self.y_fueloil_propane
        )
        self.m_hydrogen_gross = (
            self.m_butane * self.y_hydrogen_butane + self.m_ethane * self.y_hydrogen_ethane +
            self.m_gasoil * self.y_hydrogen_gasoil + self.m_naphtha * self.y_hydrogen_naphtha +
            self.m_propane * self.y_hydrogen_propane
        )
        self.m_methane_gross = (
            self.m_butane * self.y_methane_butane + self.m_ethane * self.y_methane_ethane +
            self.m_gasoil * self.y_methane_gasoil + self.m_naphtha * self.y_methane_naphtha +
            self.m_propane * self.y_methane_propane
        )

        # Off-gas combustion energy recovery (Eq. 4)
        self.E_hydrogen_combusted = self.f_hydrogen_combusted_cracker * self.h_hydrogen_cracker * self.m_hydrogen_gross
        self.E_methane_combusted = self.f_methane_combusted_cracker * self.h_methane_cracker * self.m_methane_gross

        # Natural gas for cracker - shared (Eq. 5)
        self.E_NG_cracker = self.E_cracker - (self.E_hydrogen_combusted + self.E_methane_combusted)

        # Co-product outputs (not combusted)
        self.m_hydrogen_output = (1 - self.f_hydrogen_combusted_cracker) * self.m_hydrogen_gross
        self.m_methane_output = (1 - self.f_methane_combusted_cracker) * self.m_methane_gross

        # ============ POST-PROCESSING ENERGY (Eq. 11) ============

        # Base electricity - shared among all products
        self.E_base_electricity = 0.121  # kWh per kg ethylene basis

        # H2 purification electricity - allocated ONLY to hydrogen
        self.E_H2_purification_per_kg = 1706 / 3412.142  # ~0.500 kWh/kg H2
        self.E_H2_purification = self.m_hydrogen_output * self.E_H2_purification_per_kg

        # CH4 compression NG - allocated ONLY to methane
        self.NG_compression_factor = 0.0116  # kg NG per kg CH4
        self.h_NG = 49.998  # MJ/kg NG (same as methane LHV)
        self.E_NG_CH4_compression = self.m_methane_output * self.NG_compression_factor * self.h_NG

        # ============ ALLOCATION CALCULATIONS (Eq. 8-9) ============

        # Economic values (always calculated for reference, even if using mass allocation)
        self.EV_ethylene  = self.m_ethylene * self.price_ethylene
        self.EV_propylene = self.m_propylene * self.price_propylene
        self.EV_butadiene = self.m_butadiene * self.price_butadiene
        self.EV_btx       = self.m_btx * self.price_btx
        self.EV_hydrogen  = self.m_hydrogen_output * self.price_hydrogen
        self.EV_methane   = self.m_methane_output * self.price_methane
        self.EV_fueloil   = self.m_fueloil * self.price_fueloil

        # Total economic value
        self.total_economic_value = (
            self.EV_ethylene + self.EV_propylene + self.EV_butadiene +
            self.EV_btx + self.EV_hydrogen + self.EV_methane + self.EV_fueloil
        )

        # Total mass (for mass allocation)
        self.total_product_mass = (
            self.m_ethylene + self.m_propylene + self.m_butadiene +
            self.m_btx + self.m_hydrogen_output + self.m_methane_output + self.m_fueloil
        )

        # Calculate allocation factors based on chosen method
        if self.allocation_method == 'economic':
            # Economic allocation: AF = EV_j / Σ EV_k
            self.AF_ethylene  = self.EV_ethylene  / self.total_economic_value
            self.AF_propylene = self.EV_propylene / self.total_economic_value
            self.AF_butadiene = self.EV_butadiene / self.total_economic_value
            self.AF_btx       = self.EV_btx       / self.total_economic_value
            self.AF_hydrogen  = self.EV_hydrogen  / self.total_economic_value
            self.AF_methane   = self.EV_methane   / self.total_economic_value
            self.AF_fueloil   = self.EV_fueloil   / self.total_economic_value
        else:
            # Mass allocation: AF = m_j / Σ m_k
            self.AF_ethylene  = self.m_ethylene        / self.total_product_mass
            self.AF_propylene = self.m_propylene       / self.total_product_mass
            self.AF_butadiene = self.m_butadiene       / self.total_product_mass
            self.AF_btx       = self.m_btx             / self.total_product_mass
            self.AF_hydrogen  = self.m_hydrogen_output / self.total_product_mass
            self.AF_methane   = self.m_methane_output  / self.total_product_mass
            self.AF_fueloil   = self.m_fueloil         / self.total_product_mass

        self.allocation_factors = {
            'ethylene': self.AF_ethylene, 'propylene': self.AF_propylene,
            'butadiene': self.AF_butadiene, 'btx': self.AF_btx,
            'hydrogen': self.AF_hydrogen, 'methane': self.AF_methane,
            'fueloil': self.AF_fueloil
        }

        # Reference product parameters
        self.AF_reference = self.allocation_factors.get(reference_product, self.AF_ethylene)

        self.unallocated_masses = {
            'ethylene': self.m_ethylene, 'propylene': self.m_propylene,
            'butadiene': self.m_butadiene, 'btx': self.m_btx,
            'hydrogen': self.m_hydrogen_output, 'methane': self.m_methane_output,
            'fueloil': self.m_fueloil
        }

        self.mass_reference = self.unallocated_masses.get(reference_product, self.m_ethylene)
        self.scale_to_reference = 1.0 / self.mass_reference  # Eq. 11: SF_r = 1/m_r

        # ============ ALLOCATED RESULTS (Eq. 10, 12) ============

        # Shared inputs - allocated proportionally (Eq. 10)
        self.allocated_m_butane  = self.m_butane  * self.AF_reference * self.scale_to_reference
        self.allocated_m_ethane  = self.m_ethane  * self.AF_reference * self.scale_to_reference
        self.allocated_m_gasoil  = self.m_gasoil  * self.AF_reference * self.scale_to_reference
        self.allocated_m_naphtha = self.m_naphtha * self.AF_reference * self.scale_to_reference
        self.allocated_m_propane = self.m_propane * self.AF_reference * self.scale_to_reference
        self.allocated_m_feed_total = self.m_feed_total * self.AF_reference * self.scale_to_reference

        self.allocated_E_cracker = self.E_cracker * self.AF_reference * self.scale_to_reference
        self.allocated_E_hydrogen_combusted = self.E_hydrogen_combusted * self.AF_reference * self.scale_to_reference
        self.allocated_E_methane_combusted = self.E_methane_combusted * self.AF_reference * self.scale_to_reference

        # Cracker NG (shared) - allocated proportionally
        self.allocated_E_NG_cracker = self.E_NG_cracker * self.AF_reference * self.scale_to_reference

        # Base electricity (shared) - allocated proportionally
        self.allocated_E_base_electricity = self.E_base_electricity * self.AF_reference * self.scale_to_reference

        # ============ PRODUCT-SPECIFIC POST-PROCESSING (Eq. 12) ============

        # H2 purification: ONLY allocated to hydrogen
        if reference_product == 'hydrogen':
            self.allocated_E_H2_purification = self.E_H2_purification * self.scale_to_reference
        else:
            self.allocated_E_H2_purification = 0.0

        # CH4 compression: ONLY allocated to methane
        if reference_product == 'methane':
            self.allocated_E_NG_CH4_compression = self.E_NG_CH4_compression * self.scale_to_reference
        else:
            self.allocated_E_NG_CH4_compression = 0.0

        # Total allocated energy
        self.allocated_E_electricity_total = self.allocated_E_base_electricity + self.allocated_E_H2_purification
        self.allocated_E_NG_total = self.allocated_E_NG_cracker + self.allocated_E_NG_CH4_compression

        # ============ LCI FLOWS ============

        self.input_flows = {
            "butane": self.allocated_m_butane,
            "ethane": self.allocated_m_ethane,
            "gasoil": self.allocated_m_gasoil,
            "naphtha": self.allocated_m_naphtha,
            "propane": self.allocated_m_propane,
            "heat, hydrogen gas combustion": self.allocated_E_hydrogen_combusted,
            "heat, methane gas combustion": self.allocated_E_methane_combusted,
            "heat, natural gas combustion": self.allocated_E_NG_total,
            "electricity, medium voltage": self.allocated_E_electricity_total,
        }

        self.output_flows = {self.reference_product: 1.0}

    def get_allocation_factor(self, product):
        """
        Get allocation factor for any product.

        Args:
            product: Product name ('ethylene', 'propylene', etc.)

        Returns:
            Allocation factor AF_j [-]
        """
        return self.allocation_factors.get(product, 0.0)

    def get_allocated_inputs_for_product(self, product):
        """
        Get allocated input flows for a specific product.

        Shared inputs (feedstocks, cracker energy, base electricity) are
        allocated proportionally based on the selected allocation method
        (economic or mass).

        Product-specific post-processing (H2 purification, CH4 compression)
        is allocated only to the respective co-product.

        Args:
            product: 'ethylene', 'propylene', 'butadiene', 'btx',
                    'hydrogen', 'methane', or 'fueloil'

        Returns:
            Dictionary of allocated input flows per kg of that product
        """
        AF = self.allocation_factors.get(product, 0.0)
        mass = self.unallocated_masses.get(product, 1.0)
        scale = 1.0 / mass if mass > 0 else 0.0

        # Shared inputs - allocated proportionally
        allocated_base_elec = self.E_base_electricity * AF * scale
        allocated_NG_cracker = self.E_NG_cracker * AF * scale

        # Product-specific post-processing
        if product == 'hydrogen':
            allocated_H2_purif = self.E_H2_purification * scale
        else:
            allocated_H2_purif = 0.0

        if product == 'methane':
            allocated_CH4_compress = self.E_NG_CH4_compression * scale
        else:
            allocated_CH4_compress = 0.0

        return {
            "butane": self.m_butane * AF * scale,
            "ethane": self.m_ethane * AF * scale,
            "gasoil": self.m_gasoil * AF * scale,
            "naphtha": self.m_naphtha * AF * scale,
            "propane": self.m_propane * AF * scale,
            "heat, hydrogen gas combustion": self.E_hydrogen_combusted * AF * scale,
            "heat, methane gas combustion": self.E_methane_combusted * AF * scale,
            "heat, natural gas combustion": allocated_NG_cracker + allocated_CH4_compress,
            "electricity, medium voltage": allocated_base_elec + allocated_H2_purif,
        }

    def to_dict(self):
        """Export complete parameter set and flows for LCA integration."""
        return {
            "parameters": {
                "feed_shares": {
                    "f_butane_share_cracking": self.f_butane_share_cracking,
                    "f_ethane_share_cracking": self.f_ethane_share_cracking,
                    "f_gasoil_share_cracking": self.f_gasoil_share_cracking,
                    "f_naphtha_share_cracking": self.f_naphtha_share_cracking,
                    "f_propane_share_cracking": self.f_propane_share_cracking
                },
                "yield_scalars": {
                    "Y_ethylene_butane": self.Y_ethylene_butane,
                    "Y_ethylene_ethane": self.Y_ethylene_ethane,
                    "Y_ethylene_gasoil": self.Y_ethylene_gasoil,
                    "Y_ethylene_naphtha": self.Y_ethylene_naphtha,
                    "Y_ethylene_propane": self.Y_ethylene_propane
                },
                "ethylene_contribution_shares": {
                    "s_butane": self.s_butane,
                    "s_ethane": self.s_ethane,
                    "s_gasoil": self.s_gasoil,
                    "s_naphtha": self.s_naphtha,
                    "s_propane": self.s_propane
                },
                "prices": {
                    "price_ethylene": self.price_ethylene,
                    "price_propylene": self.price_propylene,
                    "price_butadiene": self.price_butadiene,
                    "price_btx": self.price_btx,
                    "price_hydrogen": self.price_hydrogen,
                    "price_methane": self.price_methane,
                    "price_fueloil": self.price_fueloil
                },
                "combustion_fractions": {
                    "f_hydrogen_combusted_cracker": self.f_hydrogen_combusted_cracker,
                    "f_methane_combusted_cracker": self.f_methane_combusted_cracker
                },
                "thermal_efficiency_cracker": self.thermal_efficiency_cracker,
                "reference_product": self.reference_product,
            },
            "allocation_factors": self.allocation_factors,
            "economic_values": {
                "EV_ethylene": self.EV_ethylene,
                "EV_propylene": self.EV_propylene,
                "EV_butadiene": self.EV_butadiene,
                "EV_btx": self.EV_btx,
                "EV_hydrogen": self.EV_hydrogen,
                "EV_methane": self.EV_methane,
                "EV_fueloil": self.EV_fueloil,
                "total_economic_value": self.total_economic_value
            },
            "unallocated_masses": self.unallocated_masses,
            "energy_breakdown": {
                "E_cracker": self.E_cracker,
                "E_NG_cracker": self.E_NG_cracker,
                "E_base_electricity": self.E_base_electricity,
                "E_H2_purification": self.E_H2_purification,
                "E_NG_CH4_compression": self.E_NG_CH4_compression,
            },
            "input_flows": self.input_flows,
            "output_flows": self.output_flows
        }
