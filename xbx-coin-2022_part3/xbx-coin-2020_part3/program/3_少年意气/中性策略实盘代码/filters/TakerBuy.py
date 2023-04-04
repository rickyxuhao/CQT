def signal(*args):
    # TakerBuy
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    df[factor_name] = df['taker_buy_quote_asset_volume'].rolling(n, min_periods=1).sum() / df['quote_volume'].rolling(n, min_periods=1).sum()

    return df


def get_parameter():
    param_list = []
    n_list = [3, 5, 8, 13, 21, 34, 55, 89]
    for n in n_list:
        param_list.append([n])

    return param_list
