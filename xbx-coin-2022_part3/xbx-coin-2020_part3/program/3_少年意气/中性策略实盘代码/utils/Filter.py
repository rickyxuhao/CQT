"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""


def before_filter(df):
    """
    前置过滤
        在选币之前，可能会造成当周期内空仓或多空不平衡的问题
    :param df: 原始数据
    :return: 过滤后的数据
    """
    # 过去8个小时内，主动买入成交额占比超过45%
    df = df[(df['TakerBuy_[8]'] > 0.45)]

    # 过去13个小时内，单个小时最大涨跌幅要在 -20% ~ 20% 之间
    # df = df[(df['ZhangDieFuAbsMax_[13]'] < 0.2)]

    return df
