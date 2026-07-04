# -*- coding: utf-8 -*-
"""
Predict 2017 daily hub prices from Henry Hub using historical ICE data.

Expected files in the same folder
---------------------------------
- ice_natgas-2015final.xlsx
- ice_natgas-2016final.xlsx
- ice_natgas-2017final.xlsx
- 2016_hh.xlsx
- 2017_hh.xlsx

Outputs
-------
- Predicted_2017.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


# ---------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------
ICE_FILES = [
    'ice_natgas-2015final.xlsx',
    'ice_natgas-2016final.xlsx',
    'ice_natgas-2017final.xlsx',
]

HENRY_PREV_FILE = '2016_hh.xlsx'
HENRY_TARGET_FILE = '2017_hh.xlsx'

TARGET_YEAR = 2017
EIC_HUBS = ['Algonquin Citygates', 'Chicago Citygates', 'TETCO-M3']

OUTPUT_PREDICTED = 'Predicted_2017.csv'


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def load_ice_history(file_list):
    """Read and combine ICE hub price history."""
    frames = [pd.read_excel(f, header=0) for f in file_list]
    df = pd.concat(frames, ignore_index=True)

    df['Trade date'] = pd.to_datetime(df['Trade date'])
    df = df.drop_duplicates()

    return df


def load_and_fill_henry_target(file_prev_hh, file_target_hh, target_year, buffer_days=5):
    """
    Read previous-year and target-year Henry Hub files, use the last few valid
    previous-year prices as a buffer, and interpolate missing target-year values.
    """
    df_prev = pd.read_excel(file_prev_hh, header=0)
    df_target = pd.read_excel(file_target_hh, header=0)

    df_prev = df_prev[['Date', 'Price']].copy()
    df_target = df_target[['Date', 'Price']].copy()

    df_prev['Date'] = pd.to_datetime(df_prev['Date'])
    df_target['Date'] = pd.to_datetime(df_target['Date'])

    df_prev = df_prev.sort_values('Date').reset_index(drop=True)
    df_target = df_target.sort_values('Date').reset_index(drop=True)

    buffer_prev = df_prev.dropna(subset=['Price']).tail(buffer_days).copy()

    hh_combined = pd.concat([buffer_prev, df_target], ignore_index=True)
    hh_combined = hh_combined.sort_values('Date').reset_index(drop=True)

    hh_combined['Price'] = hh_combined['Price'].interpolate(
        method='linear',
        limit_direction='both'
    )
    hh_combined['Price'] = hh_combined['Price'].ffill().bfill()

    df_target_filled = hh_combined[hh_combined['Date'].dt.year == target_year].copy()
    df_target_filled = df_target_filled.reset_index(drop=True)

    return df_target_filled


def build_training_pairs(df_all, hub_name):
    """Build matched Henry-vs-target training pairs on common trade dates."""
    henry = df_all[df_all['Price hub'] == 'Henry'][['Trade date', 'High price $/MMBtu']].copy()
    target = df_all[df_all['Price hub'] == hub_name][['Trade date', 'High price $/MMBtu']].copy()

    henry = henry.rename(columns={'High price $/MMBtu': 'Henry'})
    target = target.rename(columns={'High price $/MMBtu': hub_name})

    henry = henry.sort_values('Trade date').drop_duplicates(subset='Trade date', keep='last')
    target = target.sort_values('Trade date').drop_duplicates(subset='Trade date', keep='last')

    combined = pd.merge(henry, target, on='Trade date', how='inner')
    combined = combined.dropna(subset=['Henry', hub_name]).sort_values('Trade date').reset_index(drop=True)

    return combined


def fit_and_predict(training_df, df_target_hh, hub_name, make_plot=True):
    """Fit linear regression target_hub ~ Henry and predict for target-year Henry Hub prices."""
    reg = LinearRegression()

    X = training_df[['Henry']].to_numpy()
    y = training_df[[hub_name]].to_numpy()

    reg.fit(X, y)

    X_new = df_target_hh[['Price']].to_numpy()

    if np.isnan(X_new).any():
        raise ValueError(f'Target Henry Hub still contains NaN after filling for hub: {hub_name}')

    y_pred = reg.predict(X_new).ravel()

    if make_plot:
        plt.figure()
        plt.plot(training_df['Trade date'], training_df['Henry'].to_numpy())
        plt.plot(training_df['Trade date'], training_df[hub_name].to_numpy())
        plt.legend(['Henry Hub', hub_name])
        plt.title(f'Historical price comparison: Henry vs {hub_name}')
        plt.xticks(rotation=45)
        plt.tight_layout()

    return y_pred, reg


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    df_hist = load_ice_history(ICE_FILES)

    df_target_hh = load_and_fill_henry_target(
        HENRY_PREV_FILE,
        HENRY_TARGET_FILE,
        TARGET_YEAR,
        buffer_days=5
    )

    df_predicted = pd.DataFrame()
    df_predicted['Date'] = df_target_hh['Date']
    df_predicted['Henry'] = df_target_hh['Price']

    print('Training summary:')
    for hub in EIC_HUBS:
        training_df = build_training_pairs(df_hist, hub)

        if training_df.empty:
            raise ValueError(f'No overlapping training data found for hub: {hub}')

        predicted, reg = fit_and_predict(training_df, df_target_hh, hub, make_plot=True)

        df_predicted[hub] = predicted

        print(
            f'{hub}: n_train={len(training_df)}, '
            f'intercept={float(reg.intercept_.ravel()[0]):.6f}, '
            f'slope={float(reg.coef_.ravel()[0]):.6f}'
        )

    df_predicted.to_csv(OUTPUT_PREDICTED, index=False)
    print(f'Saved predictions to: {OUTPUT_PREDICTED}')

    plt.show()


if __name__ == '__main__':
    main()