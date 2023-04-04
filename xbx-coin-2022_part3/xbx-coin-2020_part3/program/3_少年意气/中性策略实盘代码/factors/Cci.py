"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def signal(*args):
    # Cci 最常用的T指标
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['ma'] = df['tp'].rolling(window=n, min_periods=1).mean()
    df['md'] = abs(df['ma'] - df['close']).rolling(window=n, min_periods=1).mean()
    df[factor_name] = (df['tp'] - df['ma']) / df['md'] / 0.015

    del df['tp']
    del df['ma']
    del df['md']

    return df
