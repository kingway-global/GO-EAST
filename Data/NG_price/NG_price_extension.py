# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 22:16:34 2022

@author: jkern
"""

import os
import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# Settings
# -------------------------------------------------------------------
years = [2016, 2017, 2018, 2019]   # add or remove years as needed

predicted_template = "Predicted_{year}.csv"
coeff_file = "BA_NG_Price_Coeff_Matrix.csv"
output_template = "Average_NG_prices_BAs_{year}.csv"

# -------------------------------------------------------------------
# Read coefficient matrix once
# -------------------------------------------------------------------
df_corr = pd.read_csv(coeff_file, header=0, index_col=0)
BAs = list(df_corr.index)

# Anchor BA / hub mapping used in the original script
anchor_map = {
    "Algonquin Citygates": "ISO New England",
    "Chicago Citygates": "Midcontinent Independent System Operator, Inc.",
    "TETCO-M3": "PJM Interconnection, LLC",
    "Henry": "Southern Company Services, Inc. - Trans",
}

for year in years:
    input_file = predicted_template.format(year=year)
    output_file = output_template.format(year=year)

    if not os.path.exists(input_file):
        print(f"Skipping {year}: {input_file} not found.")
        continue

    df = pd.read_csv(input_file, header=0, index_col=0)
    n_days = len(df)

    # Create BA price estimates for BAs not directly represented by anchor hubs
    for b in BAs:
        new = np.zeros((n_days, 1))

        for i in range(n_days):
            new[i] = (
                df.loc[df.index[i], "Algonquin Citygates"] * df_corr.loc[b, anchor_map["Algonquin Citygates"]]
                + df.loc[df.index[i], "Chicago Citygates"] * df_corr.loc[b, anchor_map["Chicago Citygates"]]
                + df.loc[df.index[i], "TETCO-M3"] * df_corr.loc[b, anchor_map["TETCO-M3"]]
                + df.loc[df.index[i], "Henry"] * df_corr.loc[b, anchor_map["Henry"]]
            )

        df[b] = new

    # Rename the original hub columns to BA names
    df = df.rename(columns=anchor_map)

    # Replace original time/date index with day index 0–364
    df.index = range(n_days)
    df.index.name = None

    df.to_csv(output_file)
    print(f"Saved: {output_file}")