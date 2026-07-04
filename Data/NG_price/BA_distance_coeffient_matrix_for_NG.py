# -*- coding: utf-8 -*-
"""
Create BA-to-NG-price-source distance coefficient matrix.

This version uses BAs_reference_table.xlsx to map:
    Name_geometry = BA name used in Control_Areas.shp
    Name_EIA      = BA name used in BAs_full.csv

Distances are calculated using geometry names.
The output matrix uses EIA names as index/columns.
"""

import pandas as pd
import numpy as np
import geopandas as gpd


# ============================================================
# 1. File paths
# ============================================================

control_area_shp = "../reduced_network/Control_Areas.shp"
ba_full_file = "../Interconnections/BAs_full.csv"
ba_reference_file = "../Interconnections/BAs_reference_table.xlsx"

output_file = "BA_NG_Price_Coeff_Matrix.csv"


# ============================================================
# 2. Read BA shapefile
# ============================================================

BAs_gdf = gpd.read_file(control_area_shp)
BAs_gdf = BAs_gdf.to_crs(epsg=2163)

# Clean shapefile name column
BAs_gdf["NAME"] = BAs_gdf["NAME"].astype(str).str.strip()


# ============================================================
# 3. Read BA full table and reference table
# ============================================================

BAs = pd.read_csv(ba_full_file, header=0)
BAs_ref = pd.read_excel(ba_reference_file)

# Clean relevant columns
BAs["Name"] = BAs["Name"].astype(str).str.strip()
BAs["Abbreviation"] = BAs["Abbreviation"].astype(str).str.strip()

BAs_ref["Name_EIA"] = BAs_ref["Name_EIA"].astype(str).str.strip()
BAs_ref["Name_geometry"] = BAs_ref["Name_geometry"].astype(str).str.strip()

# Drop duplicated mapping rows if any
BAs_ref = BAs_ref[["Name_EIA", "Name_geometry"]].drop_duplicates()


# ============================================================
# 4. Attach geometry names to BAs_full
# ============================================================

BAs_mapped = BAs.merge(
    BAs_ref,
    left_on="Name",
    right_on="Name_EIA",
    how="left"
)

# Report BAs without mapping
missing_mapping = BAs_mapped.loc[
    BAs_mapped["Name_geometry"].isna(),
    ["Abbreviation", "Name"]
]

if not missing_mapping.empty:
    print("Warning: These BAs in BAs_full.csv have no mapping in BAs_reference_table.xlsx:")
    print(missing_mapping)


# Keep only BAs with valid geometry mapping
BAs_mapped = BAs_mapped.dropna(subset=["Name_geometry"]).copy()


# ============================================================
# 5. Filter shapefile using Name_geometry
# ============================================================

geometry_names_needed = BAs_mapped["Name_geometry"].unique()

BAs_filtered = BAs_gdf.loc[
    BAs_gdf["NAME"].isin(geometry_names_needed)
].copy()

BAs_filtered_final = BAs_filtered[["NAME", "geometry"]].copy()
BAs_filtered_final["Center"] = BAs_filtered_final.geometry.centroid

available_geometry_names = set(BAs_filtered_final["NAME"])


# Report mapped BAs that still cannot be found in shapefile
missing_geometry = BAs_mapped.loc[
    ~BAs_mapped["Name_geometry"].isin(available_geometry_names),
    ["Abbreviation", "Name", "Name_geometry"]
]

if not missing_geometry.empty:
    print("Warning: These mapped geometry names are not found in Control_Areas.shp:")
    print(missing_geometry)


# Keep only BAs that actually exist in the shapefile
BAs_mapped = BAs_mapped.loc[
    BAs_mapped["Name_geometry"].isin(available_geometry_names)
].copy()


# ============================================================
# 6. Define BAs with direct NG data
# ============================================================

BAs_with_NG_data_abb = ["SOCO", "PJM", "ISNE", "MISO"]

BAs_with_NG_data = BAs_mapped.loc[
    BAs_mapped["Abbreviation"].isin(BAs_with_NG_data_abb)
].copy()

if BAs_with_NG_data.empty:
    raise ValueError(
        "No BAs with NG data were found after mapping. "
        "Please check BAs_with_NG_data_abb and BAs_reference_table.xlsx."
    )

# BAs without direct NG data
BAs_without_NG_data = BAs_mapped.loc[
    ~BAs_mapped["Abbreviation"].isin(BAs_with_NG_data_abb)
].copy()


# ============================================================
# 7. Prepare matrix labels
# ============================================================

# Use EIA names for output matrix
rows_eia = list(BAs_without_NG_data["Name"])
cols_eia = list(BAs_with_NG_data["Name"])

# Use geometry names for distance calculation
rows_geometry = list(BAs_without_NG_data["Name_geometry"])
cols_geometry = list(BAs_with_NG_data["Name_geometry"])

row_no = len(rows_eia)
column_no = len(cols_eia)

print(f"Number of BAs in BAs_full with valid geometry: {len(BAs_mapped)}")
print(f"Number of BAs with NG data: {column_no}")
print(f"Number of BAs without NG data: {row_no}")

if row_no < 0 or column_no <= 0:
    raise ValueError("Invalid matrix dimensions. Please check BA mapping and NG-data BA list.")


# ============================================================
# 8. Create centroid dictionary
# ============================================================

center_dict = dict(
    zip(BAs_filtered_final["NAME"], BAs_filtered_final["Center"])
)


# ============================================================
# 9. Calculate distance matrix
# ============================================================

BAs_distance_matrix = pd.DataFrame(
    np.zeros((row_no, column_no)),
    columns=cols_eia,
    index=rows_eia
)

for row_eia, row_geom in zip(rows_eia, rows_geometry):

    BA_point_1 = center_dict[row_geom]

    for col_eia, col_geom in zip(cols_eia, cols_geometry):

        BA_point_2 = center_dict[col_geom]

        distance_B1_B2 = BA_point_1.distance(BA_point_2)

        BAs_distance_matrix.loc[row_eia, col_eia] = float(distance_B1_B2)


# ============================================================
# 10. Convert distances to inverse-distance coefficients
# ============================================================

BAs_NG_dist_coeff_matrix = pd.DataFrame(
    np.zeros((row_no, column_no)),
    columns=cols_eia,
    index=rows_eia
)

for index, row in BAs_distance_matrix.iterrows():

    # If distance is zero, assign equal weight to zero-distance BA(s)
    if (row == 0).any():
        weights = pd.Series(0.0, index=row.index)
        weights[row == 0] = 1.0 / (row == 0).sum()
    else:
        inverse_distance = 1 / row
        weights = inverse_distance / inverse_distance.sum()

    BAs_NG_dist_coeff_matrix.loc[index, :] = weights


# ============================================================
# 11. Save output
# ============================================================

BAs_NG_dist_coeff_matrix.to_csv(output_file)

print(f"Saved: {output_file}")
