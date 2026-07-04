# -*- coding: utf-8 -*-
"""
Rewrite of NG_price_correlations_2019.py

Main fixes
----------
1) Fixes the pandas error:
       TypeError: Passing a set as an indexer is not supported.
   by avoiding set-based .loc indexing entirely.

2) Replaces the fragile Henry Hub missing-value loop with a safer fill method:
   use 2018_hh.xlsx as a buffer, then interpolate/fill 2019 Henry Hub prices.

3) Removes the extra-row workaround and uses merged training pairs by trade date.

Expected files
--------------
- ice_natgas-2015final.xlsx
- ice_natgas-2016final.xlsx
- ice_natgas-2017final.xlsx
- 2018_hh.xlsx
- 2019_hh.xlsx
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


ICE_FILES = [
    'ice_natgas-2015final.xlsx',
    'ice_natgas-2016final.xlsx',
    'ice_natgas-2017final.xlsx',
]

HENRY_2018_FILE = '2018_hh.xlsx'
HENRY_2019_FILE = '2019_hh.xlsx'

EIC_HUBS = ['Algonquin Citygates', 'Chicago Citygates', 'TETCO-M3']

OUTPUT_PREDICTED = 'Predicted_2019.csv'
#OUTPUT_FILLED_HH = '2019_hh_filled.xlsx'


def load_ice_history(file_list):
    frames = [pd.read_excel(f, header=0) for f in file_list]
    df = pd.concat(frames, ignore_index=True)
    df['Trade date'] = pd.to_datetime(df['Trade date'])
    df = df.drop_duplicates()
    return df


def load_and_fill_henry_2019(file_2018_hh, file_2019_hh, buffer_days=5):
    df_2018_hh = pd.read_excel(file_2018_hh, header=0)[['Date', 'Price']].copy()
    df_2019_hh = pd.read_excel(file_2019_hh, header=0)[['Date', 'Price']].copy()

    df_2018_hh['Date'] = pd.to_datetime(df_2018_hh['Date'])
    df_2019_hh['Date'] = pd.to_datetime(df_2019_hh['Date'])

    df_2018_hh = df_2018_hh.sort_values('Date').reset_index(drop=True)
    df_2019_hh = df_2019_hh.sort_values('Date').reset_index(drop=True)

    buffer_2018 = df_2018_hh.dropna(subset=['Price']).tail(buffer_days).copy()

    hh_combined = pd.concat([buffer_2018, df_2019_hh], ignore_index=True)
    hh_combined = hh_combined.sort_values('Date').reset_index(drop=True)

    hh_combined['Price'] = hh_combined['Price'].interpolate(
        method='linear',
        limit_direction='both'
    )
    hh_combined['Price'] = hh_combined['Price'].ffill().bfill()

    df_2019_filled = hh_combined[hh_combined['Date'].dt.year == 2019].copy()
    df_2019_filled = df_2019_filled.reset_index(drop=True)
    return df_2019_filled


def build_training_pairs(df_all, hub_name):
    henry = df_all[df_all['Price hub'] == 'Henry'][['Trade date', 'High price $/MMBtu']].copy()
    target = df_all[df_all['Price hub'] == hub_name][['Trade date', 'High price $/MMBtu']].copy()

    henry = henry.rename(columns={'High price $/MMBtu': 'Henry'})
    target = target.rename(columns={'High price $/MMBtu': hub_name})

    henry = henry.sort_values('Trade date').drop_duplicates(subset='Trade date', keep='last')
    target = target.sort_values('Trade date').drop_duplicates(subset='Trade date', keep='last')

    combined = pd.merge(henry, target, on='Trade date', how='inner')
    combined = combined.dropna(subset=['Henry', hub_name]).sort_values('Trade date').reset_index(drop=True)
    return combined


def fit_and_predict(training_df, df_2019_hh, hub_name, make_plot=True):
    reg = LinearRegression()

    X = training_df[['Henry']].to_numpy()
    y = training_df[[hub_name]].to_numpy()
    reg.fit(X, y)

    X_new = df_2019_hh[['Price']].to_numpy()
    if np.isnan(X_new).any():
        raise ValueError(f'2019 Henry Hub still contains NaN after filling for hub: {hub_name}')

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


def main():
    df_hist = load_ice_history(ICE_FILES)
    df_2019_hh = load_and_fill_henry_2019(HENRY_2018_FILE, HENRY_2019_FILE, buffer_days=5)
    #df_2019_hh.to_excel(OUTPUT_FILLED_HH, index=False)

    df_predicted = pd.DataFrame()
    df_predicted['Date'] = df_2019_hh['Date']
    df_predicted['Henry'] = df_2019_hh['Price']

    print('Training summary:')
    for hub in EIC_HUBS:
        training_df = build_training_pairs(df_hist, hub)
        if training_df.empty:
            raise ValueError(f'No overlapping training data found for hub: {hub}')

        predicted, reg = fit_and_predict(training_df, df_2019_hh, hub, make_plot=True)
        df_predicted[hub] = predicted

        print(
            f'{hub}: n_train={len(training_df)}, '
            f'intercept={float(reg.intercept_.ravel()[0]):.6f}, '
            f'slope={float(reg.coef_.ravel()[0]):.6f}'
        )

    df_predicted.to_csv(OUTPUT_PREDICTED, index=False)
    print(f'Saved predictions to: {OUTPUT_PREDICTED}')
    #print(f'Saved filled Henry Hub series to: {OUTPUT_FILLED_HH}')
    plt.show()


if __name__ == '__main__':
    main()
