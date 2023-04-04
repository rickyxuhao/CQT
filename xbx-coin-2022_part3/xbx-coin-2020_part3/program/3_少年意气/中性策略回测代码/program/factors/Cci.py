"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
"""
计算因子重要提醒：
1. 注意填充空值。因子数据不能为空，否则影响后面的选币计算。
2. 注意因子可能会无穷大或无穷小（在除数为0的情况下）。此时需要额外处理，否则影响后面的选币计算。
"""


def signal(*args):
    # Cci
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['ma'] = df['tp'].rolling(window=n, min_periods=1).mean()
    df['md'] = abs(df['close'] - df['ma']).rolling(window=n, min_periods=1).mean()
    df[factor_name] = (df['tp'] - df['ma']) / df['md'] / 0.015

    del df['tp']
    del df['ma']
    del df['md']

    return df


def get_parameter():
    param_list = []
    n_list = [3, 5, 8, 13, 21, 34, 55, 89]
    for n in n_list:
        param_list.append([n])

    return param_list
