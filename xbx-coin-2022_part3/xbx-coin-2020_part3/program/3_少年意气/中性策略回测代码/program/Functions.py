"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import pandas as pd
from program.Config import *
import warnings
warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行


def calc_factors_for_filename(df, factor_list, filename=''):
    """
    使用文件夹下的因子脚本进行计算因子
    :param df: 原始k线数据
    :param factor_list: 需要计算的因子列表
    :param filename: 指定因子文件夹名称
    :return:
    """
    column_list = []
    # 根据config中设置的因子列表，逐个计算每个因子的数据
    for factor in factor_list:
        _cls = __import__('%s.%s' % (filename, factor), fromlist=('',))
        # 获取当前因子下的所有参数
        param_list = getattr(_cls, 'get_parameter')()
        # 遍历参数，计算每个参数对应的因子值
        for n in param_list:
            factor_name = f'{factor}_{str(n)}'
            # 计算因子
            df = getattr(_cls, 'signal')(df, n, factor_name)
            # 为了跟实盘保持一致，所有因子信息在下个周期生效。这行代码要充分理解。
            df[factor_name] = df[factor_name].shift(1)
            # 保存因子列名
            column_list.append(factor_name)
    return df, column_list


def trans_period_for_period(df, period, exg_dict=None):
    """
    周期转换函数
    :param df: K线数据
    :param period: 数据转换周期
    :param exg_dict: 转换规则
    """
    df.set_index('candle_begin_time', inplace=True)

    # 必备字段
    agg_dict = {
        'symbol': 'first',
        'volume': 'sum',
    }
    # 如果有其他字段，这里进行扩展
    if exg_dict:
        agg_dict = dict(agg_dict, **exg_dict)

    period_df_list = []
    # 根据换仓周期，循环转换每一个offset周期
    for offset in range(int(period[:-1])):
        period_df = df.resample(period, base=offset).agg(agg_dict)
        period_df['offset'] = offset
        period_df.reset_index(inplace=True)
        # 数据存放到list中
        period_df_list.append(period_df)

    # 将不同offset的数据，合并到一张表
    period_df = pd.concat(period_df_list, ignore_index=True)
    period_df.sort_values(by='candle_begin_time', inplace=True)
    period_df.reset_index(drop=True, inplace=True)

    return period_df


def cal_equity(df, c_rate, select_coin_num):
    """
    计算本周期涨跌幅
    :param df: 选币数据
    :param c_rate: 手续费率
    :param select_coin_num: 选币数量
    """
    # 本周期涨跌幅字段的含义：假设我给每个币分配1元的保证金，最终的盈亏是多少元
    df['本周期涨跌幅'] = 1 * (1 + df['ret_next'] * df['方向'] * leverage) * (1 - c_rate) - (1 * c_rate * leverage) - 1
    # 净值 = 1 + ret_net * 方向 * l
    # 扣卖出手续费净值 = (1 + ret_net * 方向 * l) * (1 - c_rate)
    # 扣买入手续费净值 = (1 + ret_net * 方向 * l) * (1 - c_rate) - (1 * c_rate * l)
    # 扣除成本后当周期收益 = (1 + ret_net * 方向 * l) * (1 - c_rate) - (1 * c_rate * l) - 1

    equity = pd.DataFrame()
    equity['本周期多空涨跌幅'] = df.groupby('candle_begin_time')['本周期涨跌幅'].sum() / (select_coin_num * 2)  # 所有币的盈亏 / 总共投入的钱
    equity.reset_index(inplace=True)

    return equity


def select_long_and_short_coin(df, select_coin_num):
    """
    选币
    :param df: 数据集
    :param select_coin_num: 选币数量
    """
    # 对因子进行排名
    df['rank'] = df.groupby('candle_begin_time')['因子'].rank(method='first')
    # 根据时间和因子排名
    df.sort_values(by=['candle_begin_time', 'rank'], inplace=True)

    # 做多排名靠前的币种
    long_df = df.groupby('candle_begin_time').head(select_coin_num)
    long_df['方向'] = 1

    # 做空排名靠后的币种
    short_df = df.groupby('candle_begin_time').tail(select_coin_num)
    short_df['方向'] = -1

    # 整理数据
    df = pd.concat([long_df, short_df], ignore_index=True)   # 将做多和做空的币种数据合并
    df.sort_values(by=['candle_begin_time', '方向'], ascending=[True, False], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
