"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
"""
事件的介绍,方便之后查看
"""
# 事件需要的因子
factors = []
# 事件的中文名
strategy_name = ''


def batch_parameters():
    """
    生成该策略需要被遍历的参数
    :return:
    """
    return [[3, 6], [6, 8]]


def event_strategy(df, params, **kwargs):
    """
    计算事件
    :param df: 数据
    :param params:
    :return:
    """

    return df
