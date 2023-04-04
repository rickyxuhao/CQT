"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def signal(*args):
    # Cci因子魔改的第三个版本，参考自《中性5期船队因子库》: https://bbs.quantclass.cn/thread/13472
    df = args[0]
    n = args[1][0]
    factor_name = args[2]

    oma = df['open'].ewm(span=n, adjust=False).mean()
    hma = df['high'].ewm(span=n, adjust=False).mean()
    lma = df['low'].ewm(span=n, adjust=False).mean()
    cma = df['close'].ewm(span=n, adjust=False).mean()
    tp = (oma + hma + lma + cma) / 4
    ma = tp.ewm(span=n, adjust=False).mean()
    md = (cma - ma).abs().ewm(span=n, adjust=False).mean()
    df[factor_name] = (tp - ma) / md

    return df
