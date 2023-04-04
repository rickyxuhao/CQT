"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def signal(*args):
    # Bias
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    df['ma'] = df['close'].rolling(n, min_periods=1).mean()
    df[factor_name] = (df['close'] / df['ma'] - 1)

    del df['ma']

    return df
