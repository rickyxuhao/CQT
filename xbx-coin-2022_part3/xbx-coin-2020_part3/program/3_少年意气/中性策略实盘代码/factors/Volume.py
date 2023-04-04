"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def signal(*args):
    # Volume
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    df[factor_name] = df['quote_volume'].rolling(n, min_periods=1).sum()

    return df
