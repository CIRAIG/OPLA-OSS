import pandas as pd
import os

OUTPUT_PATH = "./outputs"

FILES = [
    {
        "input": "inputs/ingredients.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "ingredients_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INGREDIENTS_MIDPOINTS",
        },
        "endpoints": {
            "output": "ingredients_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INGREDIENTS_ENDPOINTS",
        },
        "contributions": {
            "output": "ingredients_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INGREDIENTS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/materials.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "materials_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "MATERIALS_MIDPOINTS",
        },
        "endpoints": {
            "output": "materials_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "MATERIALS_ENDPOINTS",
        },
        "contributions": {
            "output": "materials_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "MATERIALS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/processing-methods.csv",
        "enableProductAndActivityNameMerge": False,
        "midpoints": {
            "output": "processing_methods_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PROCESSING_METHODS_MIDPOINTS",
        },
        "endpoints": {
            "output": "processing_methods_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PROCESSING_METHODS_ENDPOINTS",
        },
        "contributions": {
            "output": "processing_methods_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PROCESSING_METHODS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/eol.csv",
        "enableProductAndActivityNameMerge": False,
        "midpoints": {
            "output": "eol_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "EOL_MIDPOINTS",
        },
        "endpoints": {
            "output": "eol_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "EOL_ENDPOINTS",
        },
        "contributions": {
            "output": "eol_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "EOL_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/energies.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "energies_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "ENERGIES_MIDPOINTS",
        },
        "endpoints": {
            "output": "energies_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "ENERGIES_ENDPOINTS",
        },
        "contributions": {
            "output": "energies_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "ENERGIES_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/direct-emissions.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "direct_emissions_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "DIRECT_EMISSIONS_MIDPOINTS",
        },
        "endpoints": {
            "output": "direct_emissions_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "DIRECT_EMISSIONS_ENDPOINTS",
        },
        "contributions": {
            "output": "direct_emissions_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "DIRECT_EMISSIONS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/other-requirements.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "other_requirements_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "OTHER_REQUIREMENTS_MIDPOINTS",
        },
        "endpoints": {
            "output": "other_requirements_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "OTHER_REQUIREMENTS_ENDPOINTS",
        },
        "contributions": {
            "output": "other_requirements_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "OTHER_REQUIREMENTS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/internals.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "internals_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INTERNALS_MIDPOINTS",
        },
        "endpoints": {
            "output": "internals_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INTERNALS_ENDPOINTS",
        },
        "contributions": {
            "output": "internals_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "INTERNALS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/greens.csv",
        "enableProductAndActivityNameMerge": True,
        "midpoints": {
            "output": "greens_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "GREENS_MIDPOINTS",
        },
        "endpoints": {
            "output": "greens_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "GREENS_ENDPOINTS",
        },
        "contributions": {
            "output": "greens_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "GREENS_CONTRIBUTIONS",
        },
    },
    {
        "input": "inputs/purples.csv",
        "enableProductAndActivityNameMerge": False,
        "midpoints": {
            "output": "purples_midpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PURPLES_MIDPOINTS",
        },
        "endpoints": {
            "output": "purples_endpoints.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PURPLES_ENDPOINTS",
        },
        "contributions": {
            "output": "purples_contributions.csv",
            "base_cols": ["sub-category", "name", "unit", "comment", "location"],
            "var_name": "PURPLES_CONTRIBUTIONS",
        },
    }
]


# Input and output file names

def generate_generic_file(input_file, output_file, type_of_export, base_cols, enableProductAndActivityNameMerge=False):
    
    if type_of_export not in ["midpoint", "endpoint", "contribution"]:
        raise ValueError("type_of_export must be either 'midpoint', 'endpoint' or 'contribution'")
    
    # Load the CSV
    df = pd.read_csv(input_file)

    # Detect related columns based on export type
    related_columns = []
    if type_of_export == "midpoint":
        # Detect columns that we want (their name contains the keyword)
        related_columns = [col for col in df.columns if "IMPACT World+ Midpoint 2.1" in str(col) and "Total" not in str(col)]
    elif type_of_export == "endpoint":
        # Detect columns that we want (their name contains the keyword)
        related_columns = [col for col in df.columns if "IMPACT World+ Damage 2.1" in str(col) and "Total" in str(col)]
    else:
        # Detect columns that are EcoInvent (their name contains the word "Midpoint")
        ecoinvent_cols = [col for col in df.columns if "IMPACT World+ Damage 2.1" in str(col)]
    
        # Take only contribution columns (exclude Midpoint and Total)
        for col in ecoinvent_cols:
            is_blacklisted = False
            for keyword in ["Midpoint", "Total"]:
                if keyword in str(col):        
                    is_blacklisted = True
                    break
                    
            if not is_blacklisted:
                related_columns.append(col)

    # Build final column list (keeping order as in original dataframe)
    final_cols = [c for c in df.columns if c in base_cols or c in related_columns] + ['original_name']

    # Create a mapping for renaming
    if type_of_export in ["midpoint", "endpoint"]:
        col_map = {col: minimize_col(col, [2]) for col in final_cols}    
    else:
        col_map = {col: minimize_col(col, [1,2]) for col in final_cols}
    
    # If the data of the 'name' column contains "market for", then remove it and add "(market mix)" at the end
    if 'name' in df.columns:
        df['original_name'] = df['name']

        is_market = df['name'].apply(lambda x: isinstance(x, str) and "market for" in x)

        new_name = df['name'].apply(
            lambda x: x.replace("market for", "").strip() + " (market mix)"
            if isinstance(x, str) and "market for" in x else x
        )

        if enableProductAndActivityNameMerge:
            df['name'] = new_name  # default

            # appliquer le merge SEULEMENT si ce n’est PAS un market
            mask = ~is_market
            df.loc[mask, 'name'] = (
                df.loc[mask, "reference product"].astype(str)
                + " from "
                + new_name.loc[mask].astype(str)
            )
        else:
            df['name'] = new_name

    # Append the content of the 'location' column at the end of each value in the 'name' column
    if 'location' in df.columns:
        df['name'] = df.apply(lambda row: f"{row['name']} | {row['location']}", axis=1)
        
    if 'sub-category' in df.columns:
        df['sub-category'] = df['sub-category'].fillna('Uncategorized')

    # Create the new dataframe and save it
    df_out = df[final_cols].rename(columns=col_map)
    
    # Ensure the output directory for CSV files exists
    os.makedirs(f'{OUTPUT_PATH}/csv', exist_ok=True)
    
    df_out.to_csv(f'{OUTPUT_PATH}/csv/{output_file}', index=False)

    print(f"\nNew file saved as: {OUTPUT_PATH}/csv/{output_file}")

def minimize_col(col, indexesToKeep):
    isRecycledPrefixed = False
    isSubsititutedPrefixed = False

    if col.startswith("Recycled - "):
        isRecycledPrefixed = True
        col = col.replace("Recycled - ", "")
    if col.startswith("Substituted - "):
        isSubsititutedPrefixed = True
        col = col.replace("Substituted - ", "")

    # Rename columns: if column name looks like a tuple string, keep only 2nd and 3rd elements
    if isinstance(col, str) and col.startswith("(") and col.endswith(")"):
        parts = eval(col)  # Convert string tuple to actual tuple
        result = ""
        
        for index in indexesToKeep:
            if index < len(parts):
                if result:
                    result += "|"
                result += str(parts[index])
                
        if isRecycledPrefixed:
            result = "Recycled - " + result
        if isSubsititutedPrefixed:
            result = "Substituted - " + result

        return result

    return col

def csv_to_js(csv_file, var_name="data"):
    # Ensure the output directory for JS files exists
    os.makedirs(f'{OUTPUT_PATH}/js', exist_ok=True)

    df = pd.read_csv(f'{OUTPUT_PATH}/csv/{csv_file}')
    json_file = f'{OUTPUT_PATH}/js/{csv_file}'.replace('.csv', '.js')
    
    # Hyphenate column names
    df.columns = [col.replace(' ', '-') for col in df.columns]
    
    # Remove commas in column names
    df.columns = [col.replace(',', '') for col in df.columns]
    
    df.to_json(json_file, orient='records', indent=4)
    
    with open(json_file, 'r') as f:
        json_content = f.read()
    with open(json_file, 'w') as f:
        f.write(f"window.{var_name} = {json_content}")
    
    print(f"\nConverted {csv_file} to {json_file}")

if __name__ == "__main__":
    
    for file in FILES:
        generate_generic_file(
            file["input"],
            file["midpoints"]["output"],
            type_of_export="midpoint",
            base_cols=file["midpoints"]["base_cols"],
            enableProductAndActivityNameMerge=file["enableProductAndActivityNameMerge"]
        )
        
        generate_generic_file(
            file["input"],
            file["endpoints"]["output"],
            type_of_export="endpoint",
            base_cols=file["endpoints"]["base_cols"],
            enableProductAndActivityNameMerge=file["enableProductAndActivityNameMerge"]
        )
        
        generate_generic_file(
            file["input"],
            file["contributions"]["output"],
            type_of_export="contribution",
            base_cols=file["contributions"]["base_cols"],
            enableProductAndActivityNameMerge=file["enableProductAndActivityNameMerge"]
        )

        csv_to_js(file["midpoints"]["output"], var_name=file["midpoints"]["var_name"])
        csv_to_js(file["endpoints"]["output"], var_name=file["endpoints"]["var_name"])
        csv_to_js(file["contributions"]["output"], var_name=file["contributions"]["var_name"])
