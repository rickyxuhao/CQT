"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def before_filter(df):
    """
    :param df: 原始数据
    :return: 过滤后的数据
    """
    # 过去8个小时内，主动买入成交额占比超过40%
    df = df[(df['TakerBuy_[8]'] > 0.4)]

    # 过去13个小时内，单个小时最大涨跌幅要在 -20% ~ 20% 之间，可以过滤掉一部分妖币（Luna暴跌）
    # df = df[(df['ZhangDieFuAbsMax_[13]'] < 0.2)]

    # 前置过滤在选币之前，可能会造成当周期内空仓或多空不平衡的问题
    # 计算截面数据：
    # 特别注意：截面数据的计算需要在过滤条件之前全部计算完毕，否则会影响最终选币
    # 计算过去55个小时内，成交量的排名百分比
    # df['成交量排名'] = df.groupby('candle_begin_time')['Volume_[55]'].rank(ascending=True, pct=True)
    # 计算过去55个小时内成交量的排名百分比超过50%
    # df = df[df['成交量排名'] > 0.5]

    return df