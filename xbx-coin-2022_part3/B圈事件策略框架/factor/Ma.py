"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
factor_name = 'Ma'


def special_data(candle_df, symbol, agg_dict, **kwargs):
    """
    导入额外的数据
    :param candle_df:   基础数据
    :param symbol:  币种名
    :param agg_dict:   转换周期的字典
    :return:
    """

    return candle_df, agg_dict


def batch_parameters():
    """
    生成遍历的参数
    :return:
    """

    parameters_list = [2, 3, 5, 8, 13, 21, 34, 55, 89]

    return parameters_list


def calculate(df, parameters, **kwargs):
    """
    计算单个币种的因子
    这边坚决不能进行去重或者删除空值等删除某行的操作
    :param df:  需要计算的币种数据
    :param parameters:  参数
    :param kwargs:    额外的参数
    :return:
    """
    # 计算均线
    df['%s_%s' % (factor_name, parameters)] = df['close'].rolling(parameters, min_periods=1).mean()

    return df


def cross_section_calculate(df, parameters, **kwargs):
    """
    计算截面因子的函数
    :param df:  所有币种的数据
    :param parameters:  参数
    :param kwargs:    额外的参数
    :return:
    """

    df['%s_%s_排名' % (factor_name, parameters)] = df.groupby('candle_begin_time')['%s_%s' % (factor_name, parameters)].\
        rank(ascending=False, method='first')

    return df
