from datetime import datetime as dt

import pandas as pd
from hurst import compute_Hc

import paper_engine_strategy.strategy.portfolio_optimization.helpers.indicators as indicator
import paper_engine_strategy.strategy.portfolio_optimization.helpers.data_models as dm

"""

File with all the functions necessary to filter data, according to the Hurst
exponent, momentum etc..

"""


def get_data_analysis(
    close_df,
    rebalancing_period: dm.Rebalancing_Period,
    hurst_exponents_period: int,
    mean_rev_type: dm.Mean_Rev_Type,
    momentum_type: dm.Momentum_Type,
    functional_constraints: dm.Functional_Constraints,
    momentum_days_period: int,
    live_analysis=False,
):
    """
    Analyze data by calculating Hurst exponents, Bollinger Bands, momentum, and close prices for selected periods.

    Parameters:
        close_df (pd.DataFrame): DataFrame with adjusted close prices for different assets.
        rebalancing_period (dm.Rebalancing_Period): Rebalancing period for the analysis.
        hurst_exponents_period (int): Period for Hurst exponent calculations (in days).
        mean_rev_type (dm.Mean_Rev_Type): Type of mean reversion indicator to use.
        momentum_type (dm.Momentum_Type): Type of momentum indicator to use.
        functional_constraints (dm.Functional_Constraints): Functional constraints (see data_models.py).
        momentum_days_period (int): Period for momentum calculations (in days).
        live_analysis (bool): Flag to indicate if the analysis is for live trading.

    Returns:
        dict: Dictionary containing the Rebalancing Dates, Hurst exponents, Bollinger Bands, RSI, Cumulative Returns, MACD values, and close prices.
    """
    if live_analysis:
        H = [
            compute_Hc(close_df[col].values, kind="price", simplified=False)[0]
            for col in close_df.columns.to_list()
        ]

        if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands:
            bollinger_bands = indicator.calculate_bollinger_bands(close_df)
        elif mean_rev_type == dm.Mean_Rev_Type.RSI:
            RSI = indicator.calculate_RSI(
                close_df, window=functional_constraints.get_rsi_window()
            )

        if momentum_type == dm.Momentum_Type.Cumulative_Returns:
            # Mudar para o MACD real, por enquanto é o cumrets
            momentum_cumrets = indicator.momentum_n_days(
                close_df, momentum_n_days=momentum_days_period
            )

        elif momentum_type == dm.Momentum_Type.MACD:
            macd_df = indicator.calculate_macd(
                close_df,
                functional_constraints.get_macd_short_window(),
                functional_constraints.get_macd_long_window(),
                signal_window=9,
            )

        return {
            "hurst_exponents": list(zip(close_df.columns, H)),
            "bollinger_bands": (
                list(zip(close_df.columns, bollinger_bands.values))
                if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands
                else None
            ),
            "RSI": (
                list(zip(close_df.columns, RSI.iloc[-1]))
                if mean_rev_type == dm.Mean_Rev_Type.RSI
                else None
            ),
            "momentum_cumrets": (
                list(zip(close_df.columns, momentum_cumrets))
                if momentum_type == dm.Momentum_Type.Cumulative_Returns
                else None
            ),
            "macd_values": (
                [
                    (
                        key,
                        macd_df.loc["macd", key],
                        macd_df.loc["signal_line", key],
                        macd_df.loc["histogram", key],
                        macd_df.loc["hist_diff", key],
                        macd_df.loc["lower_threshold", key],
                        macd_df.loc["upper_threshold", key],
                        macd_df.loc["trend", key],
                    )
                    for key in macd_df.columns
                ]
                if momentum_type == dm.Momentum_Type.MACD
                else None
            ),
            "close_price": list(zip(close_df.columns, close_df.iloc[-1].values)),
        }

    rebalances = range(hurst_exponents_period, len(close_df), rebalancing_period)

    print(rebalances)

    result_dict = {}

    for i in rebalances:
        # Select data for Hurst and Bollinger Bands calculation
        temp = close_df.iloc[i - hurst_exponents_period : i].copy()
        ###### Missing: Use the future data to test through: ######
        # temp_forward = close_df.iloc[i:i+30].copy()
        temp = temp.dropna(axis=1)
        keys = temp.keys()

        # Calculate Hurst Exponents
        H = [
            compute_Hc(temp[col].values, kind="price", simplified=False)[0]
            for col in temp.columns.to_list()
        ]

        # result_dict[i] = list(zip(keys, H))
        # Calculate cumulative return for the last 30 days before rebalance
        # Calculate Bollinger Bands for the 180 days before rebalance

        if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands:
            bollinger_bands = indicator.calculate_bollinger_bands(temp)

        elif mean_rev_type == dm.Mean_Rev_Type.RSI:
            rsi = indicator.calculate_RSI(
                temp, window=functional_constraints.get_rsi_window()
            )

        if momentum_type == dm.Momentum_Type.Cumulative_Returns:
            # Mudar para o MACD real, por enquanto é o cumrets
            momentum_cumrets = indicator.momentum_n_days(temp, momentum_days_period)

        elif momentum_type == dm.Momentum_Type.MACD:
            macd_df = indicator.calculate_macd(
                temp,
                functional_constraints.get_macd_short_window(),
                functional_constraints.get_macd_long_window(),
                signal_window=9,
            )
            print(macd_df)

        result_dict[i] = {
            "rebalance-dates": [close_df.index[i], close_df.index[i]],
            "hurst_exponents": list(zip(keys, H)),
            "bollinger_bands": (
                list(zip(keys, bollinger_bands.values))
                if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands
                else []
            ),
            "RSI": (
                list(
                    zip(
                        keys,
                        rsi.loc[
                            rsi.index[
                                rsi.index.get_indexer(
                                    [close_df.index[i]], method="ffill"
                                )
                            ][0],
                            keys,
                        ],
                    )
                )
                if mean_rev_type == dm.Mean_Rev_Type.RSI
                else []
            ),
            "momentum_cumrets": (
                list(zip(keys, momentum_cumrets))
                if momentum_type == dm.Momentum_Type.Cumulative_Returns
                else []
            ),
            "macd_values": (
                [
                    (
                        key,
                        macd_df.loc["macd", key],
                        macd_df.loc["signal_line", key],
                        macd_df.loc["histogram", key],
                        macd_df.loc["hist_diff", key],
                        macd_df.loc["lower_threshold", key],
                        macd_df.loc["upper_threshold", key],
                        macd_df.loc["trend", key],
                    )
                    for key in macd_df.columns
                ]
                if momentum_type == dm.Momentum_Type.MACD
                else []
            ),
            "close_price": list(zip(keys, temp.iloc[-1].values)),
        }

    return result_dict


def get_rebalancing_period_days(rebalancing_period: dm.Rebalancing_Period) -> int:
    """
    Convert the rebalancing period to the number of days.

    Parameters:
        rebalancing_period (dm.Rebalancing_Period): The rebalancing period.

    Returns:
        int: The number of days in the rebalancing period.
    """
    period_value = rebalancing_period.value[:-1]  # Extract the value (7, 30, 90)
    unit = rebalancing_period.value[-1]  # Extract the unit ('d', 'w', 'm')

    if unit == "d":  # Days
        return int(period_value)
    elif unit == "w":  # Weeks
        return int(period_value) * 7
    elif unit == "m":  # Months
        return int(period_value) * 30
    else:
        raise ValueError(f"Unknown rebalancing period unit: {unit}")

def filter_data(
    dict_to_filter,
    hurst_thresholds=dm.HurstFilter.STANDARD,
    mean_rev_type=dm.Mean_Rev_Type.RSI,
    momentum_type=dm.Momentum_Type.MACD,
    live_analysis=False,
):
    """
    Filters and organizes data based on Hurst exponent values.

    Parameters:
        dict_to_filter (dict): The input dictionary containing data to filter. (which is the output of get_data_analysis)
                               Expected keys in each item: 'rebalance-dates', 'hurst_exponents', 'bollinger_bands',
                               'RSI', 'momentum_cumrets', 'macd_values', 'close_price'.
        hurst_thresholds (tuple): A tuple containing the lower and upper thresholds for the Hurst exponent.
                                  Default is (0.45, 0.55).
        mean_rev_type (dm.Mean_Rev_Type): The type of mean reversion indicator to use.
        momentum_type (dm.Momentum_Type): The type of momentum indicator to use.
        live_analysis (bool): Flag to indicate if the analysis is for live trading.

    Returns:
        dict: A dictionary containing filtered data grouped into 'trendy_assets' and
              'mean_reverting_assets' categories, along with close prices and rebalance dates.
        pd.DataFrame: DataFrame containing trendy assets and their rebalance dates.
        pd.DataFrame: DataFrame containing mean reverting assets and their rebalance dates.
    """
    filtered_result_dict = {}
    lower_threshold, upper_threshold = hurst_thresholds

    # Save trendy and mean reverting assets per date
    df_trendy_assets = pd.DataFrame()
    df_mean_reverting_assets = pd.DataFrame()

    print(f"Lower Threshold: {lower_threshold}, Upper Threshold: {upper_threshold}")

    if live_analysis:
        keys, H = zip(*dict_to_filter["hurst_exponents"])

        trendy_assets = [key for key, h in zip(keys, H) if h > upper_threshold]
        df_trendy_assets = pd.concat(
            [
                df_trendy_assets,
                pd.DataFrame(trendy_assets, columns=["asset"]).assign(date=0),
            ],
            ignore_index=True,
        )

        mean_reverting_assets = [key for key, h in zip(keys, H) if h < lower_threshold]
        df_mean_reverting_assets = pd.concat(
            [
                df_mean_reverting_assets,
                pd.DataFrame(mean_reverting_assets, columns=["asset"]).assign(date=0),
            ],
            ignore_index=True,
        )

        if momentum_type == dm.Momentum_Type.Cumulative_Returns:
            trendy_assets_list = [
                (key, mom[1])
                for key, mom in zip(keys, dict_to_filter["momentum_cumrets"])
                if key in trendy_assets
            ]
        elif momentum_type == dm.Momentum_Type.MACD:
            trendy_assets_list = [
                (key, macd)
                for key, macd in zip(keys, dict_to_filter["macd_values"])
                if key in trendy_assets
            ]
        else:
            raise ValueError(f"Momentum Type {momentum_type} not supported")

        if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands:
            mean_reverting_assets_list = [
                (key, bol[1])
                for key, bol in zip(keys, dict_to_filter["bollinger_bands"])
                if key in mean_reverting_assets
            ]
        elif mean_rev_type == dm.Mean_Rev_Type.RSI:
            mean_reverting_assets_list = [
                (key, rsi)
                for key, rsi in dict_to_filter["RSI"]
                if key in mean_reverting_assets
            ]
        else:
            raise ValueError(f"Mean Reversion Type {mean_rev_type} not supported")

        assets_filtered = {
            "date": dt.today(),
            "trendy_assets": trendy_assets_list,
            "mean_reverting_assets": mean_reverting_assets_list,
            "close_price": [
                cp
                for key, cp in zip(keys, dict_to_filter["close_price"])
                if key in keys
            ],
        }

        filtered_result_dict[0] = assets_filtered

        return filtered_result_dict, df_trendy_assets, df_mean_reverting_assets

    for i, data in dict_to_filter.items():
        # Extract the Hurst exponents and their associated keys
        keys, H = zip(*data["hurst_exponents"])

        # Filter out keys where H is between 0.45 and 0.55
        filtered_keys = [
            key
            for key, h in zip(keys, H)
            if not (lower_threshold < h < upper_threshold)
        ]

        # If there are still keys left after filtering, create a new entry in the filtered_result_dict
        if filtered_keys:

            filtered_data = {
                "date": data["rebalance-dates"],
                "hurst_exponents": [
                    (key, h) for key, h in zip(keys, H) if key in filtered_keys
                ],
                "bollinger_bands": (
                    [
                        (key, bb)
                        for key, bb in data["bollinger_bands"]
                        if key in filtered_keys
                        and mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands
                    ]
                    if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands
                    else []
                ),
                "RSI": (
                    [
                        (key, rsi)
                        for key, rsi in data["RSI"]
                        if key in filtered_keys
                        and mean_rev_type == dm.Mean_Rev_Type.RSI
                    ]
                    if mean_rev_type == dm.Mean_Rev_Type.RSI
                    else []
                ),
                "momentum_cumrets": (
                    [
                        (key, mom)
                        for key, mom in data["momentum_cumrets"]
                        if key in filtered_keys
                        and momentum_type == dm.Momentum_Type.Cumulative_Returns
                    ]
                    if momentum_type == dm.Momentum_Type.Cumulative_Returns
                    else []
                ),
                "macd_values": (
                    [
                        (
                            key,
                            macd,
                            signal_line,
                            histogram,
                            hist_diff,
                            lower_threshold,
                            upper_threshold,
                            trend,
                        )
                        for key, macd, signal_line, histogram, hist_diff, lower_threshold, upper_threshold, trend in data[
                            "macd_values"
                        ]
                        if key in filtered_keys
                        and momentum_type == dm.Momentum_Type.MACD
                    ]
                    if momentum_type == dm.Momentum_Type.MACD
                    else []
                ),
                "close_price": [
                    (key, cp)
                    for key, cp in zip(keys, data["close_price"])
                    if key in filtered_keys
                ],
            }
            filtered_result_dict[i] = filtered_data

        trendy_assets = [key for key, h in zip(keys, H) if h > upper_threshold]
        df_trendy_assets = pd.concat(
            [
                df_trendy_assets,
                pd.DataFrame(trendy_assets, columns=["asset"]).assign(date=i),
            ],
            ignore_index=True,
        )

        mean_reverting_assets = [key for key, h in zip(keys, H) if h < lower_threshold]
        df_mean_reverting_assets = pd.concat(
            [
                df_mean_reverting_assets,
                pd.DataFrame(mean_reverting_assets, columns=["asset"]).assign(date=i),
            ],
            ignore_index=True,
        )

        if momentum_type == dm.Momentum_Type.Cumulative_Returns:
            trendy_assets_list = [
                (key, mom[1])
                for key, mom in zip(keys, data["momentum_cumrets"])
                if key in trendy_assets
            ]
        elif momentum_type == dm.Momentum_Type.MACD:
            trendy_assets_list = [
                (key, macd)
                for key, macd in zip(keys, data["macd_values"])
                if key in trendy_assets
            ]
        else:
            raise ValueError(f"Momentum Type {momentum_type} not supported")

        if mean_rev_type == dm.Mean_Rev_Type.Bollinger_Bands:
            mean_reverting_assets_list = [
                (key, bol[1])
                for key, bol in zip(keys, data["bollinger_bands"])
                if key in mean_reverting_assets
            ]
        elif mean_rev_type == dm.Mean_Rev_Type.RSI:
            mean_reverting_assets_list = [
                (key, rsi) for key, rsi in data["RSI"] if key in mean_reverting_assets
            ]
        else:
            raise ValueError(f"Mean Reversion Type {mean_rev_type} not supported")

        assets_filtered = {
            "date": data["rebalance-dates"],
            "trendy_assets": trendy_assets_list,
            "mean_reverting_assets": mean_reverting_assets_list,
            "close_price": [
                cp for key, cp in zip(keys, data["close_price"]) if key in keys
            ],
        }

        filtered_result_dict[i] = assets_filtered

    return filtered_result_dict, df_trendy_assets, df_mean_reverting_assets


def extract_assets(signals_dict, date):
    """Extract the assets to buy and sell for a given date.

    Parameters:
    signals_dict (dict): The signals dictionary
    date (int): The date to extract the assets

    Returns:
    list: The assets to buy
    list: The assets to sell
    """
    assets_to_buy = signals_dict.get(date, {}).get("buy", [])
    assets_to_sell = signals_dict.get(date, {}).get("sell", [])
    return assets_to_buy, assets_to_sell


def filter_assets_data(
    close_df,
    date,
    rebalancing_periods,
    assets_selected,
    all_assets,
    first_returns=False,
):
    """Filter the close prices data for the selected assets in the given range.

    Parameters:
    close_df (pd.DataFrame): The close prices of the assets
    date (int): The date to filter the assets data
    rebalancing_periods (dm.Rebalancing_Period): The rebalancing periods.
    assets_selected (list): The assets selected (e.g. assets to buy)
    all_assets (list): All the assets available
    first_returns (bool): Flag to return the first returns

    Returns:
    pd.DataFrame: The close prices for all assets in the given period
    pd.DataFrame: The returns for all assets in the given period
    pd.DataFrame: The returns for the selected assets in the given preiod
    """

    if not first_returns:
        filtered_closes = close_df.iloc[date - 1 : date + rebalancing_periods]
    else:
        filtered_closes = close_df.iloc[date : date + rebalancing_periods]

    filtered_returns = filtered_closes[all_assets].pct_change()
    selected_returns = filtered_closes[assets_selected].pct_change()
    return filtered_closes, filtered_returns, selected_returns