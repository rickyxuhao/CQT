"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
"""
MA金叉事件策略
"""
# 事件需要的因子
factors = ['Ma']
# 事件的名称名
strategy_name = 'MaCross'  # 名称和程序文件名相同，不能含有_


def batch_parameters():
    """
    生成该策略需要被遍历的参数
    :return:
    """
    parameters_list = []
    for short in [2, 3, 5, 8, 13, 21, 34, 55, 89]:
        for long in [2, 3, 5, 8, 13, 21, 34, 55, 89]:
            if short < long:
                parameters_list.append([short, long])

    return parameters_list


def event_strategy(df, params, **kwargs):
    """
    计算事件
    :param df: 数据
    :param params:
    :return:
    """
    short, long = params
    event_name = strategy_name + '_' + str(params)  # 策略名称

    # 条件1 ： 短期均线 > 长期均线
    con1 = df['Ma_%s' % short] > df['Ma_%s' % long]

    # 计算上个周期的均线
    df['Ma_shift_%s' % short] = df.groupby('symbol')['Ma_%s' % short].shift()
    df['Ma_shift_%s' % long] = df.groupby('symbol')['Ma_%s' % long].shift()
    # 条件2 ： 短期均线 > 长期均线
    con2 = df['Ma_shift_%s' % short] < df['Ma_shift_%s' % long]

    df.loc[con1 & con2, event_name] = 1

    return df
