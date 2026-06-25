"""
FCCProcess Class - Propylene from High-Severity Fluid Catalytic Cracking (v4)
==============================================================================

This class implements a Life Cycle Inventory (LCI) model for propylene production
via High-Severity Fluid Catalytic Cracking (HS-FCC) with CONFIGURABLE ALLOCATION
METHODS for co-product handling in Life Cycle Assessment (LCA), compliant with
ISO 14044 standards.

Process Overview:
    [Vacuum Gas Oil (VGO)] --> [HS-FCC Reactor/Regenerator] --> [Propylene + Co-products]
                                                                 (Gasoline, Ethylene,
                                                                  Butylenes, LCO, HCO, etc.)

The FCC is an AUTOTHERMAL process: coke deposited on the catalyst during cracking
is burned in the regenerator to provide ALL the heat needed for cracking. This is
fundamentally different from steam cracking, which uses an external natural gas
furnace. The key closure variable is CATALYST CIRCULATION RATE (not fuel demand).

Allocation Methods (ISO 14044 Section 4.3.4):
----------------------------------------------
1. ECONOMIC ALLOCATION (default):
   AF_j = (m_j * p_j) / sum(m_k * p_k)

2. MASS ALLOCATION:
   AF_j = m_j / sum(m_k)

Data Sources (with page numbers):
---------------------------------
YIELDS:
  - Maadhah et al. (2008), "A New Catalytic Cracking Process to Maximize
    Refinery Propylene", Arabian J. Sci. Eng. 33(1B), pp.17-28.
    Table 8 (p.27): HS-FCC Demo Plant, Base + 8wt% ZSM-5, 600C, untreated VGO
    Table 9 (p.27): HS-FCC with hydrotreated feed, Demo Plant
    Table 6 (p.25): Effect of feed oil type on product yields (for C2= estimate)
    Table 4 (p.22): Operating conditions (T=600C, C/O=13-40, feed preheat=280C)

ENERGY & HEAT BALANCE:
  - Sadeghbeigi, R. (2012), "Fluid Catalytic Cracking Handbook", 3rd ed.,
    Butterworth-Heinemann (Elsevier).
    p.134, Table 6.4: Heats of reaction (cracking endotherm)
    p.142, Table 7.2: Operating data (steam rates: dispersion, stripping, dome)
    p.150, Table 7.4A: Normalized FCC yields
    p.154, Example 7.4: Coke burning stoichiometry and heat release
        - C -> CO2: 14,087 Btu/lb = 32.76 MJ/kg C
        - H -> H2O: 51,571 Btu/lb = 119.96 MJ/kg H
        - S -> SO2:  3,983 Btu/lb =   9.27 MJ/kg S
    p.155: Cat/oil ratio = 4.68 (conventional); delta coke = 0.88 wt%
    p.156-157: Heat of cracking = 120-220 Btu/lb feed (case study: 134.4 Btu/lb)
              Catalyst Cp = 0.285 Btu/(lb*F) = 1.09 kJ/(kg*C)
    p.159: Coke hydrogen content 5-6 wt% for well-stripped catalyst
    p.109: Catalyst makeup rate: 0.1-1.0 lb/bbl feed (typically 1-2% of inventory/day)
    p.118-120: SOx and NOx emission mechanisms
        - SOx: >95% is SO2 (p.118)
        - NOx: 7% of coke nitrogen -> NOx in full-burn regenerator (p.120)

NON-COMBUSTION EMISSIONS:
  - GREET 2024 (R&D GREET1_2024.xlsm), Argonne National Laboratory.
    Sheet "Petroleum", Row 80 (Propylene), Column DT (Non-Combustion Emissions):
      VOC:  1.561 g/mmBtu fuel throughput
      CO:   0.383 g/mmBtu
      PM10: 0.133 g/mmBtu
      PM2.5: 0.090 g/mmBtu
      CH4:  (from column DT, row 139/144)
      BC:   0.000 g/mmBtu (non-combustion)
      OC:   0.000 g/mmBtu (non-combustion)
    These represent fugitive emissions from equipment leaks, valves, flanges,
    and catalyst fines — NOT from coke combustion (which we calculate directly).

VGO FEEDSTOCK PROXY (for ecoinvent integration):
  - ecoinvent v3.10: "heavy fuel oil production, petroleum refinery operation"
    Justified by matching boiling range (350-550C) and LHV (~40 MJ/kg).

Mathematical Model - Equations Implemented:
--------------------------------------------

BLOCK A: MASS BALANCE (Eqs 1-3)

  Eq 1. VGO feed per kg propylene (functional unit):
        m_VGO = 1 / y_propylene
        [Source: Maadhah Table 8, p.27]

  Eq 2. Co-product masses:
        m_i = m_VGO * y_i    for each product i
        [Source: Maadhah Tables 8-9, p.27]

  Eq 3. Coke mass decomposition:
        m_C = m_coke * w_C;  m_H = m_coke * w_H
        m_S = m_coke * w_S;  m_N = m_coke * w_N
        [Source: Sadeghbeigi p.154, p.159]

BLOCK B: REGENERATOR HEAT RELEASE (Eq 4)

  Eq 4. Coke combustion heat (full-burn mode):
        Q_coke = m_C * dH_C_to_CO2 + m_H * dH_H_to_H2O + m_S * dH_S_to_SO2
        [Source: Sadeghbeigi p.154, Example 7.4]

BLOCK C: HEAT DEMANDS (Eqs 5-6)

  Eq 5. Total riser heat demand:
        Q_demand = Q_crack + Q_vap + Q_sensible + Q_steam_superheat + Q_loss
        where:
          Q_crack    = m_VGO * dH_crack          [Sadeghbeigi p.156-157]
          Q_vap      = m_VGO * dH_vap_VGO        [~210 kJ/kg VGO, typical]
          Q_sensible = m_VGO * Cp_vapor * (T_riser - T_feed_preheat)
          Q_steam    = m_steam * (h_steam_out - h_steam_in)
          Q_loss     = f_loss * Q_coke            [3% radiation/mechanical]

  Eq 6. Catalyst circulation (heat balance closure):
        m_cat_circ = Q_demand / [Cp_cat * (T_regen - T_riser)]
        CTO = m_cat_circ / m_VGO
        [Source: Sadeghbeigi p.155-156]

BLOCK D: EXTERNAL ENERGY INPUTS (Eqs 7-9)

  Eq 7. Combustion air and blower electricity:
        m_air = stoichiometric_air(m_C, m_H, m_S) * (1 + f_excess_air)
        E_blower = m_air * e_blower_specific
        [Source: Sadeghbeigi p.142, Table 7.2 (90,000 scfm for 50,000 bpd)]

  Eq 8. Wet gas compressor electricity:
        E_WGC = m_gas_products * e_WGC_specific
        [Industry standard: ~0.15 MJ/kg gas for 1.5 -> 15 bar staged compression]

  Eq 9. Total electricity demand:
        E_elec = E_blower + E_WGC + E_aux
        [Source: Industry data, ~10-15 kWh/bbl = ~35-50 kWh/t VGO]

BLOCK E: STEAM BALANCE (Eq 10)

  Eq 10. Steam consumption:
         m_steam = m_VGO * (f_dispersion + f_stripping + f_dome)
         [Source: Sadeghbeigi p.142, Table 7.2]
         Defaults: dispersion=0.012, stripping=0.018, dome=0.002 (total ~3.2 wt%)

BLOCK F: REGENERATOR EMISSIONS (Eqs 11-13)

  Eq 11. CO2 from coke combustion:
         m_CO2 = m_C * (44/12)
         [Source: Stoichiometry, confirmed by Sadeghbeigi p.154]

  Eq 12. SO2 from coke combustion:
         m_SO2 = m_S * (64/32)
         [Source: Sadeghbeigi p.118; >95% of coke sulfur -> SO2]

  Eq 13. NOx from coke combustion:
         m_NOx = m_N * f_N_to_NOx * (46/14)
         [Source: Sadeghbeigi p.120; f_N_to_NOx = 0.07 for full-burn]

BLOCK G: NON-COMBUSTION EMISSIONS (Eq 14)

  Eq 14. Fugitive/process emissions (from GREET 2024):
         For each pollutant p in {VOC, CO, PM10, PM2.5}:
           m_p = EF_p * Q_coke_mmBtu
         where EF_p is the GREET non-combustion emission factor (g/mmBtu)
         and Q_coke_mmBtu is the coke combustion heat in mmBtu.
         [Source: GREET 2024, Petroleum sheet, col DT, rows 131-138]

BLOCK H: CATALYST MAKEUP (Eq 15)

  Eq 15. Fresh catalyst consumption:
         m_cat_makeup = m_VGO * r_cat_makeup
         [Source: Sadeghbeigi p.109; default r = 0.0003 kg/kg VGO]

BLOCK I: ALLOCATION (Eqs 16-17)

  Eq 16. Allocation factors:
         Economic: AF_j = (m_j * p_j) / sum(m_k * p_k)
         Mass:     AF_j = m_j / sum(m_k)
         [ISO 14044 Section 4.3.4]

  Eq 17. Allocated LCI flows per kg reference product:
         F_allocated = F_total * AF_ref * SF_ref
         where SF_ref = 1 / m_ref (scaling from propylene basis to 1 kg ref product)

Process Assumptions:
--------------------
1. Full-burn regenerator (all coke -> CO2, no partial combustion CO)
2. VGO is the sole feedstock (no recycle or blending)
3. Coke is NOT a sellable co-product (consumed in regenerator)
4. H2S exits in cracked products (not in flue gas) - tracked separately
5. Yield improvements from scalars trade off against gasoline/heavier products
6. Catalyst is USY + ZSM-5 blend (ZSM-5 fraction is configurable)
7. Feed preheat energy is provided internally from waste heat recovery
8. All steam is imported (conservative; excess steam from waste heat not credited)

Baseline Yields (Maadhah 2008, Table 8, HS-FCC Demo, Base + 8wt% ZSM-5, p.27):
---------------------------------------------------------------------------------
  Component          wt% of VGO    Source
  ─────────────────  ────────────  ──────────────────────────────────
  Fuel gas (H2+C1+C2 sat)  6.3    Derived: Table 9 H2-C2 (10.4) minus C2= (4.1)
  Ethylene (C2=)           4.1    Estimated from Table 6, p.25 (Arabian Light VGO)
  Propylene (C3=)         20.4    Table 8, p.27 (direct measurement)
  Butylenes (C4=)         19.0    Table 8, p.27 (direct measurement)
  LPG saturates            6.6    Derived: Table 9 LPG (46.0) - C3= - C4=
  Gasoline (C5+)          35.7    Tables 8-9, p.27 (direct measurement)
  LCO                      1.1    Table 8, p.27 (direct measurement)
  HCO / Slurry             4.4    Table 8, p.27 (direct measurement)
  Coke                     2.3    Tables 8-9, p.27 (direct measurement)
  ─────────────────  ────────────
  TOTAL                   99.9    (mass balance closure)

Quick Start:
-----------
1. See all available parameters:
   >>> FCCProcess.show_parameters()

2. Create model with default HS-FCC yields:
   >>> fcc = FCCProcess(region='global', reference_product='propylene')

3. Create with custom prices for economic allocation:
   >>> fcc = FCCProcess(price_propylene=1.20, price_gasoline=0.80)

4. View full results:
   >>> fcc.print_current_parameters()

5. Get allocated inputs for any product:
   >>> inputs = fcc.get_allocated_inputs_for_product('ethylene')
"""


# =============================================================================
# REGIONAL PRICE LIBRARY
# =============================================================================
# Commodity prices in USD/kg for different global markets.
# NOTE: All prices set to 1.0 as placeholders until actual market data
# (e.g., from ICIS, Platts, or regional market reports) is obtained.
# =============================================================================

# =============================================================================
# FCC CO-PRODUCT GLOBAL AVERAGE PRICES — SOURCES
# =============================================================================
#
# propylene:     $1.01/kg — ICIS/IHS Markit 2022–2024 composite global average
#                           (polymer-grade propylene, consistent with SC global)
# ethylene:      $0.65/kg — ICIS/IHS Markit 2022–2024 composite global average
#                           (polymer-grade ethylene, consistent with SC global)
# butylenes:     $1.10/kg — IMARC Group (Dec 2023), global mixed C4 olefins
#                           (n-butylene/isobutylene average across US/China/EU)
# lpg_saturates: $0.53/kg — IndexBox (2024), global average LPG export price
#                           (~$533/tonne; propane/butane mixture)
# gasoline:      $0.66/kg — Statista/Trading Economics (2023), FCC gasoline
#                           (naphtha-range, ~$655/tonne global average)
# lco:           $0.35/kg — Global trade data (2023–2024), light cycle oil
#                           (diesel-range but high-sulfur/aromatic, trades at
#                            significant discount to ULSD)
# slurry:        $0.51/kg — Aligned with SC global heavy fuel oil (IHS Markit);
#                           FCC slurry oil is residual-grade, similar to HFO
# fuel_gas:      $0.25/kg — EIA Henry Hub 2023 average ($3.63/MMBtu) converted
#                           to $/kg energy-equivalent for refinery fuel gas
# =============================================================================

REGIONAL_PRICES_FCC = {
    'global': {
        'name': 'Global Average',
        'description': 'Weighted global average prices across all markets (2022-2024)',
        'prices': {
            'propylene': 1.01, 'ethylene': 0.65, 'butylenes': 1.10,
            'gasoline': 0.66, 'lco': 0.35, 'slurry': 0.51,
            'fuel_gas': 0.25, 'lpg_saturates': 0.53,
        }
    },
    # ─────────────────────────────────────────────────────────────────────
    # NORTH AMERICA (US Gulf Coast / Mont Belvieu)
    # ─────────────────────────────────────────────────────────────────────
    # propylene/ethylene: Consistent with SC regional prices (ICIS/IHS)
    # butylenes:     $1.06/kg — USGC C4 olefins (ChemAnalyst/IMARC, crude C4 + olefin uplift)
    # lpg_saturates: $0.55/kg — Mont Belvieu propane/butane mix ($550/MT, Argus Media 2024)
    # gasoline:      $0.61/kg — USGC FCC gasoline/naphtha (Procurementresource 2024)
    # lco:           $0.34/kg — USGC LCO (diesel proxy minus sulfur discount, ~$8-15/bbl below crude)
    # slurry:        $0.48/kg — USGC HFO/CSO (aligned with SC fueloil=$0.46 + slight premium)
    # fuel_gas:      $0.22/kg — Henry Hub natural gas ~$2.66/MMBtu Jan 2025 (EIA)
    'north_america': {
        'name': 'North America',
        'description': 'US Gulf Coast and Mont Belvieu pricing (2022-2024)',
        'prices': {
            'propylene': 0.83, 'ethylene': 0.43, 'butylenes': 1.06,
            'gasoline': 0.61, 'lco': 0.34, 'slurry': 0.48,
            'fuel_gas': 0.22, 'lpg_saturates': 0.55,
        }
    },
    # ─────────────────────────────────────────────────────────────────────
    # CANADA (Alberta/Sarnia)
    # ─────────────────────────────────────────────────────────────────────
    # propylene/ethylene: Consistent with SC regional prices
    # butylenes:     $1.03/kg — Canadian C4 olefins (slightly below USGC, NRCan data)
    # lpg_saturates: $0.58/kg — Alberta propane/butane (NRCan propane price reports 2024)
    # gasoline:      $0.63/kg — Canadian naphtha (Procurementresource, slight premium over USGC)
    # lco:           $0.35/kg — Canadian LCO (aligned with global average)
    # slurry:        $0.50/kg — Canadian HFO (SC fueloil=$0.48 reference)
    # fuel_gas:      $0.10/kg — AECO gas hub, historically lowest in North America
    'canada': {
        'name': 'Canada (Alberta/Sarnia)',
        'description': 'Canadian petrochemical hubs pricing (2022-2024)',
        'prices': {
            'propylene': 0.80, 'ethylene': 0.41, 'butylenes': 1.03,
            'gasoline': 0.63, 'lco': 0.35, 'slurry': 0.50,
            'fuel_gas': 0.10, 'lpg_saturates': 0.58,
        }
    },
    # ─────────────────────────────────────────────────────────────────────
    # EUROPE (Northwest Europe / TTF)
    # ─────────────────────────────────────────────────────────────────────
    # propylene/ethylene: Consistent with SC regional prices
    # butylenes:     $1.28/kg — NWE C4 olefins (premium market, ChemAnalyst/IMARC)
    # lpg_saturates: $0.60/kg — NWE LPG ($540-570/MT, Argus Media 2024)
    # gasoline:      $0.75/kg — NWE naphtha (IMARC naphtha pricing report 2024)
    # lco:           $0.38/kg — NWE LCO (above global avg, European diesel premiums)
    # slurry:        $0.54/kg — NWE HFO (European bunkering prices, SC fueloil=$0.46)
    # fuel_gas:      $0.60/kg — TTF natural gas ~$12.40/MMBtu (Statista 2024-2025)
    'europe': {
        'name': 'Europe (NWE)',
        'description': 'Northwest Europe and TTF pricing (2022-2024)',
        'prices': {
            'propylene': 1.08, 'ethylene': 0.74, 'butylenes': 1.28,
            'gasoline': 0.75, 'lco': 0.38, 'slurry': 0.54,
            'fuel_gas': 0.60, 'lpg_saturates': 0.60,
        }
    },
    # ─────────────────────────────────────────────────────────────────────
    # CHINA (CFR / Spot)
    # ─────────────────────────────────────────────────────────────────────
    # propylene/ethylene: Consistent with SC regional prices
    # butylenes:     $1.15/kg — Chinese C4 olefins (IMARC 2023, above global avg)
    # lpg_saturates: $0.66/kg — Chinese LPG ($660-670/MT, import-heavy, Argus 2024)
    # gasoline:      $0.72/kg — Chinese naphtha (NE Asia tracking, Procurementresource)
    # lco:           $0.40/kg — Chinese LCO (diesel proxy, Statista regional diesel 2024)
    # slurry:        $0.60/kg — NE Asia HFO (bunkering prices, SC fueloil=$0.50)
    # fuel_gas:      $0.64/kg — East Asia LNG ~$10.73/MMBtu (Statista/NGI 2024)
    'china': {
        'name': 'China (CFR/Spot)',
        'description': 'Chinese domestic and CFR import pricing (2022-2024)',
        'prices': {
            'propylene': 0.95, 'ethylene': 0.69, 'butylenes': 1.15,
            'gasoline': 0.72, 'lco': 0.40, 'slurry': 0.60,
            'fuel_gas': 0.64, 'lpg_saturates': 0.66,
        }
    },
    # ─────────────────────────────────────────────────────────────────────
    # MIDDLE EAST (FOB / Netback)
    # ─────────────────────────────────────────────────────────────────────
    # propylene/ethylene: Consistent with SC regional prices
    # butylenes:     $1.10/kg — GCC C4 olefins (aligned with global, IMARC)
    # lpg_saturates: $0.53/kg — GCC LPG ($500-560/MT, lowest region, Argus 2024)
    # gasoline:      $0.66/kg — ME naphtha (FOB AG, aligned with global average)
    # lco:           $0.32/kg — ME LCO (lowest diesel-range pricing, limited local demand)
    # slurry:        $0.52/kg — ME HFO (bunkering/bunker fuel, SC fueloil=$0.48)
    # fuel_gas:      $0.27/kg — ME natural gas (subsidized/associated gas, ~$3/MMBtu)
    'middle_east': {
        'name': 'Middle East (FOB/Netback)',
        'description': 'Gulf Cooperation Council FOB and netback pricing (2022-2024)',
        'prices': {
            'propylene': 1.17, 'ethylene': 0.63, 'butylenes': 1.10,
            'gasoline': 0.66, 'lco': 0.32, 'slurry': 0.52,
            'fuel_gas': 0.27, 'lpg_saturates': 0.53,
        }
    },
}


class FCCProcess:
    """
    High-Severity Fluid Catalytic Cracking Process for Propylene Production.

    Models HS-FCC (Petrochemical Mode) with autothermal heat balance from
    coke combustion and CONFIGURABLE ALLOCATION METHODS (economic or mass)
    for co-product handling in ISO 14044 compliant LCA.

    Sellable co-products (included in allocation):
        propylene, ethylene, butylenes, lpg_saturates, gasoline, lco, slurry, fuel_gas

    Non-sellable (NOT included in allocation):
        coke (burned in regenerator for process heat -> CO2/SO2/NOx emissions)
    """

    # =========================================================================
    # BASELINE YIELDS: Maadhah et al. (2008), Table 8, p.27
    # HS-FCC Demo Plant, Base + 8wt% ZSM-5, 600C, untreated VGO
    # =========================================================================
    BASELINE_YIELDS = {
        # Product              wt fraction   Source
        'fuel_gas':     0.063,  # H2+C1+C2 sat; derived: Table 9 H2-C2(10.4%) - C2=(4.1%)
        'ethylene':     0.041,  # C2=; estimated from Table 6 p.25, Arabian Light VGO
        'propylene':    0.204,  # C3=; Table 8 p.27, direct measurement
        'butylenes':    0.190,  # C4=; Table 8 p.27, direct measurement
        'lpg_saturates': 0.066, # C3+C4 sat; derived: Table 9 LPG(46.0%) - C3= - C4=
        'gasoline':     0.357,  # C5+ naphtha; Tables 8-9 p.27, direct measurement
        'lco':          0.011,  # Light Cycle Oil; Table 8 p.27
        'slurry':       0.044,  # HCO/Slurry; Table 8 p.27
        'coke':         0.023,  # Coke; Tables 8-9 p.27; burned in regenerator
    }

    # =========================================================================
    # COKE COMPOSITION: Sadeghbeigi (2012), p.154, p.159
    # Typical for well-stripped HS-FCC catalyst
    # =========================================================================
    DEFAULT_COKE_COMPOSITION = {
        'w_C': 0.920,   # Carbon wt fraction [Sadeghbeigi p.154, Example 7.4]
        'w_H': 0.055,   # Hydrogen wt fraction [Sadeghbeigi p.159: 5-6 wt%]
        'w_S': 0.020,   # Sulfur wt fraction [Sadeghbeigi p.154]
        'w_N': 0.005,   # Nitrogen wt fraction [derived from p.120: basic N ~400 ppm]
    }

    # =========================================================================
    # HEATS OF COMBUSTION: Sadeghbeigi (2012), p.154, Example 7.4
    # =========================================================================
    DH_C_TO_CO2 = 32.76    # MJ/kg C  (14,087 Btu/lb)
    DH_H_TO_H2O = 119.96   # MJ/kg H  (51,571 Btu/lb)
    DH_S_TO_SO2 = 9.27     # MJ/kg S  ( 3,983 Btu/lb)

    # =========================================================================
    # THERMODYNAMIC PARAMETERS
    # =========================================================================
    DH_CRACKING = 0.312     # MJ/kg feed, endothermic [Sadeghbeigi p.156: 134 Btu/lb]
    DH_VAP_VGO  = 0.210     # MJ/kg VGO, vaporization enthalpy [typical heavy gas oil]
    CP_LIQUID   = 0.00200   # MJ/(kg*C), VGO liquid heat capacity [~2.0 kJ/(kg*C)]
    CP_VAPOR    = 0.00275   # MJ/(kg*C), VGO vapor heat capacity [~2.75 kJ/(kg*C)]
    T_VAP_VGO   = 380.0     # C, average VGO boiling point [typical 370-400C]
    CP_CAT      = 0.00109   # MJ/(kg*C), catalyst heat capacity [Sadeghbeigi p.156: 0.285 Btu/(lb*F)]
    F_HEAT_LOSS = 0.03      # Fraction of Q_coke lost to radiation/mechanical [3%]
    LHV_NG      = 50.0      # MJ/kg natural gas lower heating value
    ETA_FURNACE = 0.85      # Feed preheat furnace thermal efficiency

    # =========================================================================
    # NON-COMBUSTION EMISSION FACTORS: GREET 2024
    # Petroleum sheet, Row 80 (Propylene), Column DT
    # Units: grams per mmBtu of fuel throughput
    # =========================================================================
    GREET_NON_COMBUSTION_EF = {
        'VOC':   1.561,   # g/mmBtu [GREET 2024, Petroleum, DT row 131]
        'CO':    0.383,   # g/mmBtu [GREET 2024, Petroleum, DT row 132]
        'PM10':  0.133,   # g/mmBtu [GREET 2024, Petroleum, DT row 134]
        'PM2.5': 0.090,   # g/mmBtu [GREET 2024, Petroleum, DT row 135]
    }
    MJ_PER_MMBTU = 1055.06  # Conversion: 1 mmBtu = 1055.06 MJ

    # =========================================================================
    # STATIC METHODS
    # =========================================================================

    @staticmethod
    def show_parameters(detailed=True):
        """Display all available parameters that can be varied."""
        print("=" * 80)
        print("AVAILABLE PARAMETERS FOR FCCProcess (HS-FCC)")
        print("=" * 80)

        if detailed:
            print("\n" + " YIELD SCALARS ".center(80, "-"))
            print("  (1.0 = baseline from Maadhah 2008 Table 8; >1.0 = improved yield)")
            for name, desc, default in [
                ("Y_propylene", "Propylene yield scalar", 1.0),
                ("Y_ethylene",  "Ethylene yield scalar",  1.0),
                ("Y_butylenes", "Butylenes yield scalar", 1.0),
            ]:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + " OPERATING PARAMETERS ".center(80, "-"))
            for name, desc, default in [
                ("T_riser",        "Riser outlet temperature (C)",           600.0),
                ("T_regen",        "Regenerator temperature (C)",            720.0),
                ("T_feed_preheat", "Feed preheat temperature (C)",           280.0),
                ("f_excess_air",   "Excess air fraction for regenerator",    0.15),
                ("f_zsm5",         "ZSM-5 fraction in catalyst inventory",   0.08),
            ]:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + " STEAM PARAMETERS (Sadeghbeigi p.142, Table 7.2) ".center(80, "-"))
            for name, desc, default in [
                ("f_steam_dispersion", "Dispersion steam (wt frac of feed)", 0.012),
                ("f_steam_stripping",  "Stripping steam (wt frac of feed)",  0.018),
                ("f_steam_dome",       "Dome steam (wt frac of feed)",       0.002),
            ]:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + " CATALYST & COKE PARAMETERS ".center(80, "-"))
            for name, desc, default in [
                ("r_cat_makeup", "Catalyst makeup rate (kg/kg VGO)",   0.0003),
                ("w_C_coke",     "Coke carbon weight fraction",        0.920),
                ("w_H_coke",     "Coke hydrogen weight fraction",      0.055),
                ("w_S_coke",     "Coke sulfur weight fraction",        0.020),
                ("w_N_coke",     "Coke nitrogen weight fraction",      0.005),
                ("f_N_to_NOx",   "Fraction coke N -> NOx (full-burn)", 0.07),
            ]:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + " ELECTRICITY PARAMETERS ".center(80, "-"))
            for name, desc, default in [
                ("e_blower",     "Air blower specific energy (MJ/kg air)",  0.110),
                ("e_WGC",        "Wet gas compressor (MJ/kg gas product)",  0.150),
                ("e_aux",        "Auxiliary electricity (MJ/kg VGO)",       0.020),
            ]:
                print(f"  {name:25s} : {desc:40s} [default: {default}]")

            print("\n" + " COMMODITY PRICES (USD/kg) ".center(80, "-"))
            for name in ['propylene', 'ethylene', 'butylenes', 'gasoline',
                         'lco', 'slurry', 'fuel_gas', 'lpg_saturates']:
                print(f"  price_{name:20s} : Market price [default: 1.00]")

            print("\n" + " ALLOCATION & REFERENCE ".center(80, "-"))
            print(f"  {'reference_product':25s} : Product for allocated results [default: 'propylene']")
            print(f"  {'allocation_method':25s} : 'economic' or 'mass' [default: 'economic']")

            print("\n" + " BASELINE YIELDS (Maadhah 2008 Table 8, wt frac of VGO) ".center(80, "-"))
            for product, yld in FCCProcess.BASELINE_YIELDS.items():
                print(f"  y_{product:20s} = {yld:.3f}")

        print("=" * 80)

    @staticmethod
    def get_parameter_template(format='dict'):
        """Get a template showing all parameters and their defaults."""
        template = {
            'Y_propylene': 1.0, 'Y_ethylene': 1.0, 'Y_butylenes': 1.0,
            'T_riser': 600.0, 'T_regen': 720.0, 'T_feed_preheat': 280.0,
            'f_excess_air': 0.15, 'f_zsm5': 0.08,
            'f_steam_dispersion': 0.012, 'f_steam_stripping': 0.018,
            'f_steam_dome': 0.002,
            'r_cat_makeup': 0.0003,
            'w_C_coke': 0.920, 'w_H_coke': 0.055,
            'w_S_coke': 0.020, 'w_N_coke': 0.005,
            'f_N_to_NOx': 0.07,
            'e_blower': 0.110, 'e_WGC': 0.150, 'e_aux': 0.020,
            'price_propylene': 1.0, 'price_ethylene': 1.0,
            'price_butylenes': 1.0, 'price_gasoline': 1.0,
            'price_lco': 1.0, 'price_slurry': 1.0,
            'price_fuel_gas': 1.0, 'price_lpg_saturates': 1.0,
            'reference_product': 'propylene',
            'allocation_method': 'economic',
        }
        if format == 'json':
            import json
            return json.dumps(template, indent=2)
        return template

    @staticmethod
    def list_parameters():
        """Quick list of all parameter names."""
        return list(FCCProcess.get_parameter_template().keys())

    @staticmethod
    def list_price_regions():
        """List all available price regions."""
        print("=" * 70)
        print("AVAILABLE PRICE REGIONS")
        print("=" * 70)
        for code, data in REGIONAL_PRICES_FCC.items():
            print(f"  '{code}': {data['name']}")
            print(f"      {data['description']}")
        print("=" * 70)
        return list(REGIONAL_PRICES_FCC.keys())

    @staticmethod
    def get_regional_prices(region):
        """Get price dictionary for a specific region."""
        region = region.lower().replace(' ', '_').replace('-', '_')
        if region not in REGIONAL_PRICES_FCC:
            available = list(REGIONAL_PRICES_FCC.keys())
            raise ValueError(f"Unknown region '{region}'. Available: {available}")
        prices = REGIONAL_PRICES_FCC[region]['prices']
        return {f'price_{k}': v for k, v in prices.items()}

    @staticmethod
    def show_regional_prices(region=None):
        """Display prices for a specific region or all regions."""
        if region is None:
            print("=" * 110)
            print("REGIONAL COMMODITY PRICES - FCC PRODUCTS (USD/kg)")
            print("=" * 110)
            commodities = ['propylene', 'ethylene', 'butylenes', 'gasoline',
                           'lco', 'slurry', 'fuel_gas', 'lpg_saturates']
            regions = list(REGIONAL_PRICES_FCC.keys())
            header = f"{'Commodity':<16}"
            for reg in regions:
                header += f" {REGIONAL_PRICES_FCC[reg]['name'][:12]:>12}"
            print(header)
            print("-" * 110)
            for comm in commodities:
                row = f"{comm:<16}"
                for reg in regions:
                    price = REGIONAL_PRICES_FCC[reg]['prices'][comm]
                    row += f" {price:>11.2f}"
                print(row)
            print("=" * 110)
        else:
            region = region.lower().replace(' ', '_').replace('-', '_')
            if region not in REGIONAL_PRICES_FCC:
                raise ValueError(f"Unknown region '{region}'.")
            data = REGIONAL_PRICES_FCC[region]
            print("=" * 50)
            print(f"PRICES FOR: {data['name']}")
            print(f"  {data['description']}")
            print("=" * 50)
            for comm, price in data['prices'].items():
                print(f"  {comm:<16}: ${price:.2f}/kg")
            print("=" * 50)

    # =========================================================================
    # CONSTRUCTOR
    # =========================================================================

    def __init__(
        self,
        region=None,
        # --- Yield scalars (1.0 = baseline from Maadhah 2008 Table 8) ---
        Y_propylene: float = 1.0,
        Y_ethylene: float = 1.0,
        Y_butylenes: float = 1.0,
        # --- Operating parameters ---
        T_riser: float = 600.0,          # Riser outlet temp, C [Maadhah Table 4, p.22]
        T_regen: float = 720.0,          # Regenerator temp, C [Sadeghbeigi p.155]
        T_feed_preheat: float = 280.0,   # Feed preheat temp, C [Maadhah Table 4, p.22]
        f_excess_air: float = 0.15,      # 15% excess air [Sadeghbeigi p.142]
        f_zsm5: float = 0.08,            # ZSM-5 fraction [Maadhah Table 8: 8 wt%]
        # --- Steam parameters [Sadeghbeigi p.142, Table 7.2] ---
        f_steam_dispersion: float = 0.012,  # wt fraction of feed
        f_steam_stripping: float = 0.018,   # wt fraction of feed
        f_steam_dome: float = 0.002,        # wt fraction of feed
        # --- Catalyst & coke parameters ---
        r_cat_makeup: float = 0.0003,    # kg/kg VGO [Sadeghbeigi p.109]
        w_C_coke: float = 0.920,         # [Sadeghbeigi p.154]
        w_H_coke: float = 0.055,         # [Sadeghbeigi p.159]
        w_S_coke: float = 0.020,         # [Sadeghbeigi p.154]
        w_N_coke: float = 0.005,         # [Sadeghbeigi p.120]
        f_N_to_NOx: float = 0.07,        # [Sadeghbeigi p.120: 7% in full-burn]
        # --- Electricity parameters ---
        e_blower: float = 0.110,         # MJ/kg air [typical centrifugal blower]
        e_WGC: float = 0.150,            # MJ/kg gas [staged compression 1.5->15 bar]
        e_aux: float = 0.020,            # MJ/kg VGO [pumps, instruments, cooling]
        # --- Commodity prices (USD/kg) ---
        price_propylene=None, price_ethylene=None, price_butylenes=None,
        price_gasoline=None, price_lco=None, price_slurry=None,
        price_fuel_gas=None, price_lpg_saturates=None,
        # --- Allocation settings ---
        reference_product: str = 'propylene',
        allocation_method: str = 'economic',
    ):
        """
        Create an HS-FCC process model with autothermal heat balance
        and configurable allocation method.

        The model calculates:
        1. Mass balance from Maadhah (2008) yields with yield scaling
        2. Heat balance from Sadeghbeigi (2012) coke combustion thermodynamics
        3. Catalyst circulation from heat balance closure
        4. Electricity from air blower + wet gas compressor + auxiliaries
        5. Combustion emissions (CO2, SO2, NOx) from coke composition
        6. Non-combustion emissions (VOC, PM, CO) from GREET 2024 factors
        7. ISO 14044 allocation (economic or mass) to co-products
        """
        # =====================================================================
        # VALIDATION
        # =====================================================================
        if allocation_method not in ['economic', 'mass']:
            raise ValueError(f"allocation_method must be 'economic' or 'mass', got '{allocation_method}'")

        valid_products = ['propylene', 'ethylene', 'butylenes', 'lpg_saturates',
                          'gasoline', 'lco', 'slurry', 'fuel_gas']
        if reference_product not in valid_products:
            raise ValueError(f"reference_product must be one of {valid_products}")

        self.allocation_method = allocation_method
        self.reference_product = reference_product
        self.price_region = region

        # =====================================================================
        # STORE ALL PARAMETERS
        # =====================================================================
        self.Y_propylene = Y_propylene
        self.Y_ethylene = Y_ethylene
        self.Y_butylenes = Y_butylenes
        self.T_riser = T_riser
        self.T_regen = T_regen
        self.T_feed_preheat = T_feed_preheat
        self.f_excess_air = f_excess_air
        self.f_zsm5 = f_zsm5
        self.f_steam_dispersion = f_steam_dispersion
        self.f_steam_stripping = f_steam_stripping
        self.f_steam_dome = f_steam_dome
        self.r_cat_makeup = r_cat_makeup
        self.w_C_coke = w_C_coke
        self.w_H_coke = w_H_coke
        self.w_S_coke = w_S_coke
        self.w_N_coke = w_N_coke
        self.f_N_to_NOx = f_N_to_NOx
        self.e_blower = e_blower
        self.e_WGC = e_WGC
        self.e_aux = e_aux

        # =====================================================================
        # HANDLE REGIONAL PRICING
        # =====================================================================
        if region is not None:
            regional = FCCProcess.get_regional_prices(region)
        else:
            regional = {}

        def _price(explicit, key, default=1.0):
            if explicit is not None:
                return explicit
            return regional.get(key, default)

        self.price_propylene     = _price(price_propylene,     'price_propylene')
        self.price_ethylene      = _price(price_ethylene,      'price_ethylene')
        self.price_butylenes     = _price(price_butylenes,     'price_butylenes')
        self.price_gasoline      = _price(price_gasoline,      'price_gasoline')
        self.price_lco           = _price(price_lco,           'price_lco')
        self.price_slurry        = _price(price_slurry,        'price_slurry')
        self.price_fuel_gas      = _price(price_fuel_gas,      'price_fuel_gas')
        self.price_lpg_saturates = _price(price_lpg_saturates, 'price_lpg_saturates')

        # =====================================================================
        # BLOCK A: MASS BALANCE (Eqs 1-3)
        # Source: Maadhah (2008) Table 8, p.27
        # =====================================================================

        # --- Baseline yields ---
        BY = self.BASELINE_YIELDS
        y_prop_base = BY['propylene']
        y_eth_base  = BY['ethylene']
        y_but_base  = BY['butylenes']

        # --- Apply yield scalars to primary olefins ---
        self.y_propylene = y_prop_base * Y_propylene
        self.y_ethylene  = y_eth_base  * Y_ethylene
        self.y_butylenes = y_but_base  * Y_butylenes

        # --- Scale remaining products to conserve mass (Eq 2 extension) ---
        total_yield = sum(BY.values())  # Should be ~0.999
        olefins_base = y_prop_base + y_eth_base + y_but_base
        olefins_new  = self.y_propylene + self.y_ethylene + self.y_butylenes
        others_base  = total_yield - olefins_base
        others_new   = total_yield - olefins_new

        if others_base > 0 and others_new > 0:
            scale_others = others_new / others_base
        else:
            scale_others = 1.0

        self.y_fuel_gas      = BY['fuel_gas'] * scale_others
        self.y_lpg_saturates = BY['lpg_saturates'] * scale_others
        self.y_gasoline      = BY['gasoline'] * scale_others
        self.y_lco           = BY['lco'] * scale_others
        self.y_slurry        = BY['slurry'] * scale_others
        self.y_coke          = BY['coke'] * scale_others

        # Verify mass balance
        self.total_yield = (self.y_propylene + self.y_ethylene + self.y_butylenes +
                            self.y_fuel_gas + self.y_lpg_saturates + self.y_gasoline +
                            self.y_lco + self.y_slurry + self.y_coke)

        # --- Eq 1: VGO feed per kg propylene ---
        if self.y_propylene <= 0:
            raise ValueError("Propylene yield must be positive")
        self.m_vgo = 1.0 / self.y_propylene  # kg VGO per kg propylene

        # --- Eq 2: Co-product masses (per kg propylene basis) ---
        self.m_propylene     = 1.0  # Functional unit
        self.m_ethylene      = self.m_vgo * self.y_ethylene
        self.m_butylenes     = self.m_vgo * self.y_butylenes
        self.m_fuel_gas      = self.m_vgo * self.y_fuel_gas
        self.m_lpg_saturates = self.m_vgo * self.y_lpg_saturates
        self.m_gasoline      = self.m_vgo * self.y_gasoline
        self.m_lco           = self.m_vgo * self.y_lco
        self.m_slurry        = self.m_vgo * self.y_slurry
        self.m_coke          = self.m_vgo * self.y_coke

        # --- Eq 3: Coke elemental decomposition ---
        # Source: Sadeghbeigi (2012), p.154 (Example 7.4), p.159
        self.m_C_coke = self.m_coke * w_C_coke
        self.m_H_coke = self.m_coke * w_H_coke
        self.m_S_coke = self.m_coke * w_S_coke
        self.m_N_coke = self.m_coke * w_N_coke

        # =====================================================================
        # BLOCK B: REGENERATOR HEAT RELEASE (Eq 4)
        # Source: Sadeghbeigi (2012), p.154, Example 7.4
        # =====================================================================

        # Eq 4: Q_coke = sum of combustion heats
        self.Q_coke = (self.m_C_coke * self.DH_C_TO_CO2 +
                        self.m_H_coke * self.DH_H_TO_H2O +
                        self.m_S_coke * self.DH_S_TO_SO2)  # MJ per kg propylene basis

        # =====================================================================
        # BLOCK C: HEAT DEMANDS (Eqs 5-6)
        # Source: Sadeghbeigi (2012), p.134 (Table 6.4), p.156-157
        # =====================================================================

        # Eq 5: Total riser heat demand
        # Feed heating is split into liquid phase, vaporization, and vapor phase
        T_vap = self.T_VAP_VGO  # VGO average boiling point (~380C)

        self.Q_crack       = self.m_vgo * self.DH_CRACKING     # Endothermic cracking [p.156]
        self.Q_liquid_heat = self.m_vgo * self.CP_LIQUID * (T_vap - T_feed_preheat)  # Liquid heating
        self.Q_vap         = self.m_vgo * self.DH_VAP_VGO      # Feed vaporization
        self.Q_vapor_heat  = self.m_vgo * self.CP_VAPOR * (T_riser - T_vap)  # Vapor superheating

        # Steam superheating (steam enters at ~150C saturated, exits at T_riser)
        m_steam_total = self.m_vgo * (f_steam_dispersion + f_steam_stripping + f_steam_dome)
        self.m_steam = m_steam_total
        Cp_steam = 0.002  # MJ/(kg*C), superheated steam [~2.0 kJ/(kg*C)]
        self.Q_steam_superheat = m_steam_total * Cp_steam * (T_riser - 150.0)

        # Heat losses (radiation + mechanical)
        self.Q_loss = self.F_HEAT_LOSS * self.Q_coke

        self.Q_demand = (self.Q_crack + self.Q_liquid_heat + self.Q_vap +
                         self.Q_vapor_heat + self.Q_steam_superheat + self.Q_loss)

        # Eq 5b: Supplemental fuel for heat deficit
        # HS-FCC has very low coke yield (2.3%), so Q_coke may be < Q_demand.
        # The deficit is supplied by natural gas (torch oil or fired preheat).
        self.Q_deficit = max(0.0, self.Q_demand - self.Q_coke)
        self.m_NG_supplement = self.Q_deficit / (self.LHV_NG * self.ETA_FURNACE)  # kg NG
        self.CO2_from_NG = self.m_NG_supplement * 0.75 * (44.0 / 12.0)  # 75% C in NG -> CO2

        # Eq 6: Catalyst circulation from heat balance closure
        delta_T_cat = T_regen - T_riser  # Temperature drop across riser
        if delta_T_cat <= 0:
            raise ValueError("T_regen must be greater than T_riser")
        self.m_cat_circ = self.Q_demand / (self.CP_CAT * delta_T_cat)

        self.CTO = self.m_cat_circ / self.m_vgo  # Cat-to-oil ratio (calculated)

        # =====================================================================
        # BLOCK D: EXTERNAL ENERGY INPUTS (Eqs 7-9)
        # =====================================================================

        # Eq 7: Combustion air requirement
        # Stoichiometry: C + O2 -> CO2;  H + 0.25*O2 -> 0.5*H2O;  S + O2 -> SO2
        # Air is 23.3% O2 by mass
        O2_for_C = self.m_C_coke * (32.0 / 12.0)   # kg O2
        O2_for_H = self.m_H_coke * (16.0 / 4.0)    # kg O2
        O2_for_S = self.m_S_coke * (32.0 / 32.0)    # kg O2
        O2_stoich = O2_for_C + O2_for_H + O2_for_S
        self.m_air = O2_stoich / 0.233 * (1.0 + f_excess_air)  # kg air

        # Blower electricity
        self.E_blower = self.m_air * e_blower  # MJ

        # Eq 8: Wet gas compressor (all gaseous products C1-C4)
        m_gas_products = (self.m_fuel_gas + self.m_ethylene + self.m_propylene +
                          self.m_butylenes + self.m_lpg_saturates)
        self.E_WGC = m_gas_products * e_WGC  # MJ

        # Eq 9: Total electricity
        self.E_aux = self.m_vgo * e_aux  # MJ
        self.E_elec_MJ = self.E_blower + self.E_WGC + self.E_aux  # MJ total
        self.E_elec_kWh = self.E_elec_MJ / 3.6  # Convert to kWh

        # =====================================================================
        # BLOCK E: STEAM BALANCE (Eq 10)
        # Source: Sadeghbeigi (2012), p.142, Table 7.2
        # =====================================================================
        # m_steam already calculated above in heat demands section
        self.f_steam_total = f_steam_dispersion + f_steam_stripping + f_steam_dome

        # =====================================================================
        # BLOCK F: REGENERATOR COMBUSTION EMISSIONS (Eqs 11-13)
        # =====================================================================

        # Eq 11: CO2 from coke [Sadeghbeigi p.154; stoichiometry]
        self.m_CO2 = self.m_C_coke * (44.0 / 12.0)

        # Eq 12: SO2 from coke [Sadeghbeigi p.118: >95% is SO2]
        self.m_SO2 = self.m_S_coke * (64.0 / 32.0)

        # Eq 13: NOx from coke [Sadeghbeigi p.120: 7% of coke N in full-burn]
        self.m_NOx = self.m_N_coke * f_N_to_NOx * (46.0 / 14.0)

        # =====================================================================
        # BLOCK G: NON-COMBUSTION EMISSIONS (Eq 14)
        # Source: GREET 2024, Petroleum sheet, Column DT (Non-Combustion)
        # =====================================================================

        # Convert Q_coke from MJ to mmBtu for GREET factor application
        Q_coke_mmBtu = self.Q_coke / self.MJ_PER_MMBTU

        self.m_VOC_nc   = self.GREET_NON_COMBUSTION_EF['VOC']   * Q_coke_mmBtu / 1000.0  # kg
        self.m_CO_nc    = self.GREET_NON_COMBUSTION_EF['CO']     * Q_coke_mmBtu / 1000.0  # kg
        self.m_PM10_nc  = self.GREET_NON_COMBUSTION_EF['PM10']   * Q_coke_mmBtu / 1000.0  # kg
        self.m_PM25_nc  = self.GREET_NON_COMBUSTION_EF['PM2.5']  * Q_coke_mmBtu / 1000.0  # kg

        # =====================================================================
        # BLOCK H: CATALYST MAKEUP (Eq 15)
        # Source: Sadeghbeigi (2012), p.109
        # =====================================================================

        # Higher ZSM-5 fraction increases attrition (~50% more per unit ZSM-5)
        zsm5_attrition_factor = 1.0 + 0.5 * f_zsm5
        self.m_catalyst = r_cat_makeup * self.m_vgo * zsm5_attrition_factor

        # =====================================================================
        # BLOCK I: ALLOCATION (Eqs 16-17)
        # Source: ISO 14044 Section 4.3.4
        # =====================================================================

        # Product masses dict (sellable only; coke excluded)
        self.product_masses = {
            'propylene':     self.m_propylene,
            'ethylene':      self.m_ethylene,
            'butylenes':     self.m_butylenes,
            'lpg_saturates': self.m_lpg_saturates,
            'gasoline':      self.m_gasoline,
            'lco':           self.m_lco,
            'slurry':        self.m_slurry,
            'fuel_gas':      self.m_fuel_gas,
        }

        # Product prices dict
        self.product_prices = {
            'propylene':     self.price_propylene,
            'ethylene':      self.price_ethylene,
            'butylenes':     self.price_butylenes,
            'lpg_saturates': self.price_lpg_saturates,
            'gasoline':      self.price_gasoline,
            'lco':           self.price_lco,
            'slurry':        self.price_slurry,
            'fuel_gas':      self.price_fuel_gas,
        }

        # Eq 16: Allocation factors
        if allocation_method == 'economic':
            economic_values = {p: self.product_masses[p] * self.product_prices[p]
                               for p in self.product_masses}
            total_ev = sum(economic_values.values())
            self.allocation_factors = {p: ev / total_ev for p, ev in economic_values.items()}
            self.economic_values = economic_values
            self.total_economic_value = total_ev
        else:
            total_mass = sum(self.product_masses.values())
            self.allocation_factors = {p: m / total_mass for p, m in self.product_masses.items()}
            self.total_product_mass = total_mass

        # Reference product allocation factor and scaling
        self.AF_ref = self.allocation_factors[reference_product]
        self.m_ref  = self.product_masses[reference_product]
        self.SF_ref = 1.0 / self.m_ref  # Scale to 1 kg of reference product

        # Eq 17: Allocated LCI flows (per 1 kg of reference product)
        af_sf = self.AF_ref * self.SF_ref

        self.allocated_vgo        = self.m_vgo * af_sf
        self.allocated_steam      = self.m_steam * af_sf
        self.allocated_catalyst   = self.m_catalyst * af_sf
        self.allocated_elec_MJ    = self.E_elec_MJ * af_sf
        self.allocated_elec_kWh   = self.E_elec_kWh * af_sf
        self.allocated_air        = self.m_air * af_sf
        self.allocated_NG         = self.m_NG_supplement * af_sf

        # Heat from supplemental NG in MJ (for ecoinvent: heat flow, not mass)
        # Q_deficit is already in MJ; allocated the same way
        self.allocated_NG_heat_MJ = self.Q_deficit * af_sf

        self.allocated_CO2_coke = self.m_CO2 * af_sf
        self.allocated_CO2_NG   = self.CO2_from_NG * af_sf
        self.allocated_CO2_total = (self.m_CO2 + self.CO2_from_NG) * af_sf
        self.allocated_SO2  = self.m_SO2 * af_sf
        self.allocated_NOx  = self.m_NOx * af_sf
        self.allocated_VOC  = self.m_VOC_nc * af_sf
        self.allocated_CO   = self.m_CO_nc * af_sf
        self.allocated_PM10 = self.m_PM10_nc * af_sf
        self.allocated_PM25 = self.m_PM25_nc * af_sf

        # =====================================================================
        # LCI FLOW DICTIONARIES — ecoinvent-compatible names
        # =====================================================================
        # Technosphere input flows use ecoinvent v3.10 activity names.
        # Units: kg for materials, MJ for heat, kWh for electricity.
        # Combustion air is NOT included (elementary flow from nature, not
        # a technosphere input in ecoinvent).
        #
        # ecoinvent mapping justification:
        #   "heavy fuel oil"  — proxy for VGO (350-550°C boiling range,
        #                       LHV ~40 MJ/kg); ecoinvent: "heavy fuel oil
        #                       production, petroleum refinery operation"
        #   "heat, natural gas, at industrial furnace >100kW"
        #                     — supplemental NG heat for heat deficit;
        #                       expressed in MJ (= Q_deficit * AF * SF)
        #   "steam, in chemical industry"
        #                     — dispersion + stripping + dome steam; kg
        #   "zeolite, powder" — closest ecoinvent proxy for FCC catalyst
        #                       (USY zeolite + ZSM-5 additive)
        #   "electricity, medium voltage"
        #                     — grid electricity for blower + WGC + aux; kWh
        # =====================================================================

        self.input_flows = {
            "heavy fuel oil":                                    self.allocated_vgo,          # kg VGO
            "heat, natural gas, at industrial furnace >100kW":   self.allocated_NG_heat_MJ,   # MJ
            "steam, in chemical industry":                       self.allocated_steam,         # kg
            "zeolite, powder":                                   self.allocated_catalyst,      # kg
            "electricity, medium voltage":                       self.allocated_elec_kWh,      # kWh
        }

        self.output_flows = {reference_product: 1.0}  # kg

        # Elementary flows to air — ecoinvent nomenclature
        # CO2 is split into coke-origin and NG-origin for traceability,
        # plus total for convenience; all map to same ecoinvent flow.
        self.emission_flows = {
            "Carbon dioxide, fossil":                            self.allocated_CO2_total,     # kg (coke + NG)
            "Sulfur dioxide":                                    self.allocated_SO2,           # kg
            "Nitrogen oxides":                                   self.allocated_NOx,           # kg
            "NMVOC, non-methane volatile organic compounds, unspecified origin": self.allocated_VOC,  # kg
            "Carbon monoxide, fossil":                           self.allocated_CO,            # kg
            "Particulates, > 2.5 um and < 10um":                 self.allocated_PM10,          # kg
            "Particulates, < 2.5 um":                            self.allocated_PM25,          # kg
        }

        # Detailed CO2 breakdown (for reporting, not for ecoinvent linking)
        self.CO2_detail = {
            "CO2, fossil - coke combustion":   self.allocated_CO2_coke,   # kg
            "CO2, fossil - supplemental NG":   self.allocated_CO2_NG,     # kg
        }

    # =========================================================================
    # OUTPUT METHODS
    # =========================================================================

    def get_allocation_factors(self, method=None):
        """Get allocation factors (uses instance method if not specified)."""
        if method is None or method == self.allocation_method:
            return dict(self.allocation_factors)

        # Recalculate for requested method
        if method == 'economic':
            ev = {p: self.product_masses[p] * self.product_prices[p]
                  for p in self.product_masses}
            total = sum(ev.values())
            return {p: v / total for p, v in ev.items()}
        elif method == 'mass':
            total = sum(self.product_masses.values())
            return {p: m / total for p, m in self.product_masses.items()}
        else:
            raise ValueError(f"method must be 'economic' or 'mass'")

    def get_allocated_inputs_for_product(self, product):
        """
        Get allocated LCI flows for any product.

        Returns dict of allocated inputs and emissions per kg of that product.
        """
        af = self.allocation_factors.get(product, 0.0)
        mass = self.product_masses.get(product, 1.0)
        sf = 1.0 / mass if mass > 0 else 0.0
        af_sf = af * sf

        inputs = {
            "heavy fuel oil":                                    self.m_vgo * af_sf,
            "heat, natural gas, at industrial furnace >100kW":   self.Q_deficit * af_sf,
            "steam, in chemical industry":                       self.m_steam * af_sf,
            "zeolite, powder":                                   self.m_catalyst * af_sf,
            "electricity, medium voltage":                       self.E_elec_kWh * af_sf,
        }
        emissions = {
            "Carbon dioxide, fossil":            (self.m_CO2 + self.CO2_from_NG) * af_sf,
            "Sulfur dioxide":                    self.m_SO2 * af_sf,
            "Nitrogen oxides":                   self.m_NOx * af_sf,
            "NMVOC, non-methane volatile organic compounds, unspecified origin": self.m_VOC_nc * af_sf,
            "Carbon monoxide, fossil":           self.m_CO_nc * af_sf,
            "Particulates, > 2.5 um and < 10um": self.m_PM10_nc * af_sf,
            "Particulates, < 2.5 um":            self.m_PM25_nc * af_sf,
        }
        return {'inputs': inputs, 'emissions': emissions}

    def print_current_parameters(self):
        """Display complete model results."""
        print("=" * 80)
        print("HS-FCC PROCESS MODEL — ALLOCATION-BASED LCI (v4)")
        print("Data: Maadhah 2008 + Sadeghbeigi 2012 + GREET 2024")
        print("=" * 80)

        print("\n" + "-" * 80)
        print(" YIELD SCALARS (1.0 = Maadhah Table 8 baseline):")
        print("-" * 80)
        print(f"  Y_propylene  = {self.Y_propylene:.4f}")
        print(f"  Y_ethylene   = {self.Y_ethylene:.4f}")
        print(f"  Y_butylenes  = {self.Y_butylenes:.4f}")

        print("\n" + "-" * 80)
        print(" OPERATING PARAMETERS:")
        print("-" * 80)
        print(f"  T_riser          = {self.T_riser:.1f} C      [Maadhah Table 4, p.22]")
        print(f"  T_regen          = {self.T_regen:.1f} C      [Sadeghbeigi p.155]")
        print(f"  T_feed_preheat   = {self.T_feed_preheat:.1f} C      [Maadhah Table 4, p.22]")
        print(f"  f_excess_air     = {self.f_excess_air:.2f}         [Sadeghbeigi p.142]")
        print(f"  f_zsm5           = {self.f_zsm5:.2f}         [Maadhah Table 8, p.27]")

        print("\n" + "-" * 80)
        print(" CALCULATED YIELDS (kg/kg VGO) — mass balance closure: "
              f"{self.total_yield:.4f}")
        print("-" * 80)
        yields = [
            ('fuel_gas',      self.y_fuel_gas,      'H2+C1+C2 sat, derived'),
            ('ethylene',      self.y_ethylene,       'C2=, est. from Table 6'),
            ('propylene',     self.y_propylene,      'C3=, Table 8 p.27'),
            ('butylenes',     self.y_butylenes,      'C4=, Table 8 p.27'),
            ('lpg_saturates', self.y_lpg_saturates,  'C3+C4 sat, derived'),
            ('gasoline',      self.y_gasoline,        'C5+, Tables 8-9 p.27'),
            ('lco',           self.y_lco,             'Table 8 p.27'),
            ('slurry',        self.y_slurry,          'Table 8 p.27'),
            ('coke',          self.y_coke,            'Tables 8-9 p.27 (burned)'),
        ]
        for name, val, src in yields:
            flag = " (burned)" if name == 'coke' else ""
            print(f"  y_{name:16s} = {val:.4f}  [{src}]{flag}")

        print("\n" + "-" * 80)
        print(" MASS BALANCE (per 1 kg propylene basis):")
        print("-" * 80)
        print(f"  VGO feed required       = {self.m_vgo:.4f} kg")
        products = [
            ('propylene', self.m_propylene), ('ethylene', self.m_ethylene),
            ('butylenes', self.m_butylenes), ('lpg_saturates', self.m_lpg_saturates),
            ('gasoline', self.m_gasoline), ('lco', self.m_lco),
            ('slurry', self.m_slurry), ('fuel_gas', self.m_fuel_gas),
            ('coke (burned)', self.m_coke),
        ]
        for name, val in products:
            print(f"  m_{name:20s} = {val:.4f} kg")

        print("\n" + "-" * 80)
        print(" HEAT BALANCE (per 1 kg propylene basis) — Sadeghbeigi 2012:")
        print("-" * 80)
        print(f"  Q_coke (combustion heat) = {self.Q_coke:.4f} MJ   [Eq 4, p.154]")
        print(f"    m_C = {self.m_C_coke:.4f} kg * {self.DH_C_TO_CO2} MJ/kg = {self.m_C_coke*self.DH_C_TO_CO2:.4f} MJ")
        print(f"    m_H = {self.m_H_coke:.4f} kg * {self.DH_H_TO_H2O} MJ/kg = {self.m_H_coke*self.DH_H_TO_H2O:.4f} MJ")
        print(f"    m_S = {self.m_S_coke:.4f} kg * {self.DH_S_TO_SO2} MJ/kg  = {self.m_S_coke*self.DH_S_TO_SO2:.4f} MJ")
        print(f"  Q_demand (riser heat)    = {self.Q_demand:.4f} MJ   [Eq 5, p.156]")
        print(f"    Q_crack       = {self.Q_crack:.4f} MJ  (dH_crack = {self.DH_CRACKING} MJ/kg)")
        print(f"    Q_liquid_heat = {self.Q_liquid_heat:.4f} MJ  (liquid {self.T_feed_preheat:.0f}->{self.T_VAP_VGO:.0f}C)")
        print(f"    Q_vap         = {self.Q_vap:.4f} MJ  (dH_vap = {self.DH_VAP_VGO} MJ/kg)")
        print(f"    Q_vapor_heat  = {self.Q_vapor_heat:.4f} MJ  (vapor {self.T_VAP_VGO:.0f}->{self.T_riser:.0f}C)")
        print(f"    Q_steam       = {self.Q_steam_superheat:.4f} MJ")
        print(f"    Q_loss        = {self.Q_loss:.4f} MJ  ({self.F_HEAT_LOSS*100:.0f}% of Q_coke)")
        if self.Q_deficit > 0:
            print(f"  ** Heat DEFICIT           = {self.Q_deficit:.4f} MJ  (Q_coke < Q_demand)")
            print(f"  ** Supplemental NG        = {self.m_NG_supplement:.4f} kg  [Eq 5b]")
            print(f"  ** CO2 from NG            = {self.CO2_from_NG:.4f} kg")
        else:
            print(f"  Heat surplus (Q_coke - Q_demand) = {self.Q_coke - self.Q_demand:.4f} MJ")
        print(f"  Catalyst circulation     = {self.m_cat_circ:.4f} kg  [Eq 6, p.155]")
        print(f"  Cat/Oil ratio (calc.)    = {self.CTO:.2f}          [p.155]")

        print("\n" + "-" * 80)
        print(" ENERGY & UTILITIES (per 1 kg propylene basis, before allocation):")
        print("-" * 80)
        print(f"  Electricity (total)      = {self.E_elec_kWh:.4f} kWh = {self.E_elec_MJ:.4f} MJ")
        print(f"    E_blower (air)         = {self.E_blower:.4f} MJ   [Eq 7]")
        print(f"    E_WGC (gas compress)   = {self.E_WGC:.4f} MJ   [Eq 8]")
        print(f"    E_aux (pumps etc.)     = {self.E_aux:.4f} MJ   [Eq 9]")
        print(f"  Steam input              = {self.m_steam:.4f} kg    [Eq 10, p.142]")
        print(f"    ({self.f_steam_total*100:.1f} wt% of feed: disp {self.f_steam_dispersion*100:.1f}% + "
              f"strip {self.f_steam_stripping*100:.1f}% + dome {self.f_steam_dome*100:.1f}%)")
        print(f"  Combustion air           = {self.m_air:.4f} kg    [Eq 7]")
        print(f"  Natural gas (supplement) = {self.m_NG_supplement:.4f} kg    [Eq 5b]")
        print(f"  Catalyst makeup          = {self.m_catalyst:.6f} kg  [Eq 15, p.109]")

        print("\n" + "-" * 80)
        print(" EMISSIONS (per 1 kg propylene basis, before allocation):")
        print("-" * 80)
        print("  Combustion (from coke burning in regenerator):")
        print(f"    CO2  = {self.m_CO2:.6f} kg   [Eq 11, Sadeghbeigi p.154]")
        print(f"    SO2  = {self.m_SO2:.6f} kg   [Eq 12, Sadeghbeigi p.118]")
        print(f"    NOx  = {self.m_NOx:.6f} kg   [Eq 13, Sadeghbeigi p.120]")
        if self.CO2_from_NG > 0:
            print("  Combustion (from supplemental NG):")
            print(f"    CO2  = {self.CO2_from_NG:.6f} kg   [Eq 5b]")
        print("  Non-combustion (GREET 2024, Petroleum sheet, Col DT):")
        print(f"    VOC  = {self.m_VOC_nc:.6f} kg   [Eq 14, GREET row 131]")
        print(f"    CO   = {self.m_CO_nc:.6f} kg   [Eq 14, GREET row 132]")
        print(f"    PM10 = {self.m_PM10_nc:.6f} kg   [Eq 14, GREET row 134]")
        print(f"    PM2.5= {self.m_PM25_nc:.6f} kg   [Eq 14, GREET row 135]")

        print("\n" + "-" * 80)
        method_name = "ECONOMIC" if self.allocation_method == 'economic' else "MASS"
        print(f" {method_name} ALLOCATION (ISO 14044 Section 4.3.4):")
        print("-" * 80)
        print(f"  {'Product':<16} {'Mass (kg)':>10} {'AF':>10} {'Price':>10}")
        print(f"  {'-'*16} {'-'*10} {'-'*10} {'-'*10}")
        for product in self.product_masses:
            m = self.product_masses[product]
            af = self.allocation_factors[product]
            p = self.product_prices[product]
            print(f"  {product:<16} {m:>10.4f} {af:>10.4f} {p:>10.2f}")
        print(f"  {'SUM':<16} {sum(self.product_masses.values()):>10.4f} "
              f"{sum(self.allocation_factors.values()):>10.4f}")

        print("\n" + "-" * 80)
        print(f" ALLOCATED LCI FLOWS (per 1 kg {self.reference_product}):")
        print(f" ecoinvent-compatible flow names")
        print("-" * 80)
        print("  TECHNOSPHERE INPUTS:")
        units_map = {
            "heavy fuel oil": "kg",
            "heat, natural gas, at industrial furnace >100kW": "MJ",
            "steam, in chemical industry": "kg",
            "zeolite, powder": "kg",
            "electricity, medium voltage": "kWh",
        }
        for name, val in self.input_flows.items():
            unit = units_map.get(name, "")
            print(f"    {name:55s} = {val:.6f} {unit}")
        print("  PRODUCT OUTPUT:")
        for name, val in self.output_flows.items():
            print(f"    {name:55s} = {val:.6f} kg")
        print("  ELEMENTARY FLOWS (emissions to air):")
        for name, val in self.emission_flows.items():
            print(f"    {name:55s} = {val:.6f} kg")
        print("  CO2 DETAIL (for traceability):")
        for name, val in self.CO2_detail.items():
            print(f"    {name:55s} = {val:.6f} kg")
        print("=" * 80)

    def to_dict(self):
        """Export complete parameter set and flows for LCA integration."""
        return {
            'parameters': {
                'yield_scalars': {
                    'Y_propylene': self.Y_propylene,
                    'Y_ethylene': self.Y_ethylene,
                    'Y_butylenes': self.Y_butylenes,
                },
                'operating': {
                    'T_riser': self.T_riser,
                    'T_regen': self.T_regen,
                    'T_feed_preheat': self.T_feed_preheat,
                    'f_excess_air': self.f_excess_air,
                    'f_zsm5': self.f_zsm5,
                },
                'coke_composition': {
                    'w_C': self.w_C_coke, 'w_H': self.w_H_coke,
                    'w_S': self.w_S_coke, 'w_N': self.w_N_coke,
                },
                'steam': {
                    'f_dispersion': self.f_steam_dispersion,
                    'f_stripping': self.f_steam_stripping,
                    'f_dome': self.f_steam_dome,
                },
                'reference_product': self.reference_product,
                'allocation_method': self.allocation_method,
            },
            'calculated_yields': {
                'y_propylene': self.y_propylene, 'y_ethylene': self.y_ethylene,
                'y_butylenes': self.y_butylenes, 'y_fuel_gas': self.y_fuel_gas,
                'y_lpg_saturates': self.y_lpg_saturates, 'y_gasoline': self.y_gasoline,
                'y_lco': self.y_lco, 'y_slurry': self.y_slurry, 'y_coke': self.y_coke,
                'total': self.total_yield,
            },
            'heat_balance': {
                'Q_coke_MJ': self.Q_coke,
                'Q_demand_MJ': self.Q_demand,
                'Q_surplus_MJ': self.Q_coke - self.Q_demand,
                'CTO_calculated': self.CTO,
                'm_cat_circ_kg': self.m_cat_circ,
            },
            'energy': {
                'E_elec_kWh': self.E_elec_kWh,
                'E_blower_MJ': self.E_blower,
                'E_WGC_MJ': self.E_WGC,
                'E_aux_MJ': self.E_aux,
                'm_steam_kg': self.m_steam,
                'm_air_kg': self.m_air,
                'm_catalyst_kg': self.m_catalyst,
            },
            'unallocated_emissions': {
                'CO2_coke_kg': self.m_CO2, 'CO2_NG_kg': self.CO2_from_NG,
                'CO2_total_kg': self.m_CO2 + self.CO2_from_NG,
                'SO2_kg': self.m_SO2, 'NOx_kg': self.m_NOx,
                'VOC_nc_kg': self.m_VOC_nc, 'CO_nc_kg': self.m_CO_nc,
                'PM10_nc_kg': self.m_PM10_nc, 'PM25_nc_kg': self.m_PM25_nc,
            },
            'allocation_factors': self.allocation_factors,
            'product_masses': self.product_masses,
            'input_flows': self.input_flows,
            'output_flows': self.output_flows,
            'emission_flows': self.emission_flows,
            'CO2_detail': self.CO2_detail,
        }
