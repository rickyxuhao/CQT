"""
2022  币圈基础事件策略 | 邢不行
author: 邢不行
微信: xbx9585
"""

import pandas as pd
import os
import numpy as np
from program.Config import root_path, rul_type, candle_type
from glob import glob

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数


# region 文件交互
def get_code_list_in_one_dir(path, end_with='csv'):
    """
    从指定文件夹下，导入所有数字货币数据
    :param path:
    :param end_with:
    :return:
    """
    symbol_list = []

    # 系统自带函数os.walk，用于遍历文件夹中的所有文件
    for root, dirs, files in os.walk(path):
        if files:  # 当files不为空的时候
            for f in files:
                if f.endswith(end_with):
                    symbol_list.append(os.path.join(root, f))

    return sorted(symbol_list)


def read_factor(df, factor_list):
    """
    读取需要的因子数据
    :param df:
    :param factor_list:
    :param candle_type:
    :return:
    """
    # 根据strategy_config_list内设置的因子读取
    for factor in factor_list:

        # 遍历所有需要的因子文件
        path_list = glob(root_path + '/data/数据整理/因子数据/%s/%s/*_%s.pkl' % (factor, rul_type, candle_type))
        if len(path_list) == 0:
            print('未获取到因子的数据，请检查因子%s是否存在！！' % factor)
            exit()

        # 遍历文件
        for path in path_list:
            # 读取因子数据
            df_ = pd.read_pickle(path)
            if df.shape[0] != df_.shape[0]:
                print('base数据与因子数据长度不一致，请检查数据是否有误')
                exit()
            # 遍历所有列并合并
            for f in df_.columns:
                df[f] = df_[f]  # 直接根据index合并即可

    return df


def load_rank_factor(df, factor):
    base_df = pd.read_pickle(root_path + '/data/数据整理/因子数据/base_%s_%s.pkl' % (rul_type, candle_type))
    base_df = read_factor(base_df, [factor])
    factor_cols = [col for col in base_df.columns if factor in col]
    base_df = base_df[['candle_begin_time', 'symbol'] + factor_cols]
    # 使用上一个周期的因子数据排名
    base_df[factor_cols] = base_df.groupby('symbol')[factor_cols].shift()
    df = pd.merge(left=df, right=base_df, on=['candle_begin_time', 'symbol'], how='left')
    return df


def cal_net_value(data, margin_rate, event, lvg):
    """
    1、将涨跌幅转为净值
    2、处理爆仓的数据，发生爆仓后，净值为0，由于此处净值为计算交易费用，所以建议适当提高一点维持保证金比例
    :param data: 输入的数据
    :param margin_rate: 保证金率
    :param event: 事件，1表示做多，-1表示做空
    :param lvg: 杠杆倍数。
    :return:
    """
    if data[event] > 0:
        net_value = np.cumprod((np.array(data['未来N周期涨跌幅']) * lvg) + 1)
    elif data[event] < 0:
        net_value = 1 + (1 - np.cumprod(1 + (np.array(data['未来N周期涨跌幅'])))) * lvg
    inx = np.argwhere(np.array(net_value) < margin_rate)
    if len(inx) > 0:
        first_inx = inx[0][0]
        net_value[first_inx:] = 0
    return list(net_value)


# 导入BTC
def import_benchmark_data(path, rul_type, start, end):
    """
    导入原始一小时数据并转换数据周期，如果是一小时的数据不进行数据周期转换
    :param rul_type: 时间周期
    :param start: 回测开始时间
    :param end: 回测结束时间
    :param path:
    :return:
    """
    # 导入业绩比较基准 （币种）
    benchmark_coin = pd.read_csv(path, encoding='gbk', parse_dates=['candle_begin_time'], skiprows=1)

    # 转换数据到指定的周期。可能会从1小时转为1小时，不影响结果。
    agg_dict = {'open': 'first', 'close': 'last', 'quote_volume': 'sum'}
    benchmark_coin = benchmark_coin.resample(rul_type, on='candle_begin_time').agg(agg_dict)

    # 生成指定时间周期的完整时间序列
    benchmark = pd.DataFrame(pd.date_range(start=start, end=end, freq=rul_type), columns=['candle_begin_time'])

    # 将业绩比较基准与时间序列合并
    benchmark = pd.merge(left=benchmark, right=benchmark_coin, on='candle_begin_time', how='left', sort=True)

    # 填充空值
    benchmark['close'].fillna(method='ffill', inplace=True)
    benchmark['open'].fillna(value=benchmark['close'], inplace=True)
    benchmark['quote_volume'].fillna(value=0, inplace=True)
    benchmark['基准涨跌幅'] = benchmark['close'].pct_change()
    benchmark['基准涨跌幅'].fillna(value=benchmark['close'] / benchmark['open'] - 1, inplace=True)  # 第一天的涨跌幅
    benchmark.rename(columns={'quote_volume': '基准成交量'}, inplace=True)

    # 只保留需要的数据
    benchmark = benchmark[['candle_begin_time', '基准涨跌幅', '基准成交量']]
    benchmark.reset_index(inplace=True, drop=True)

    return benchmark


# 将现货数据和BTC数据合并
def merge_with_benchmark(df, benchmark):
    """
    防止数字货币有停牌，选择BTC去补充
    :param df: 币种数据
    :param benchmark: BTC数据
    :return:
    """

    end = df['candle_begin_time'].max()  # 币种k线结束事件

    # ===将现货数据和benchmark数据合并，并且排序
    df = pd.merge(left=df, right=benchmark, on='candle_begin_time', how='right', sort=True, indicator=True)

    # ===对开、高、收、低、前收盘价价格进行补全处理
    # 用前一个周期的收盘价，补全收盘价的空值
    df['close'].fillna(method='ffill', inplace=True)
    # 用收盘价补全开盘价、最高价、最低价的空值
    df['open'].fillna(value=df['close'], inplace=True)
    df['high'].fillna(value=df['close'], inplace=True)
    df['low'].fillna(value=df['close'], inplace=True)

    # ===将停盘时间的某些列，数据填补为0
    fill_0_list = ['quote_volume']
    df.loc[:, fill_0_list] = df[fill_0_list].fillna(value=0)

    # ===用前一个周期的数据，补全其余空值
    df.fillna(method='ffill', inplace=True)

    # ===删除该币种还未上市的日期
    df.dropna(subset=['symbol'], inplace=True)

    # ===判断计算当前周期是否交易
    df['是否交易'] = 1
    df.loc[df['_merge'] == 'right_only', '是否交易'] = 0

    # 删除币种退市之后的数据
    df = df[df['candle_begin_time'] <= end]

    # 删除不需要的字段
    df.drop(labels=['_merge', '基准涨跌幅', '基准成交量'], axis=1, inplace=True)

    df.reset_index(drop=True, inplace=True)

    return df


# endregion


# endregion

def cal_toperiod_symbol_cap_line(data, hold_period, ret_len=30):
    """
    当前周期买入若干个币种，计算买入这些币种之后的资金曲线
    :param data:
    :param hold_period:
    :param ret_len:
    :return:
    """

    # 补全净值不足的币种
    for i in data.index:
        _len = len(data[i])
        if _len < ret_len:
            data[i] = data[i] + [data[i][-1]] * (ret_len - _len)
        elif _len > ret_len:
            data[i] = data[i][:ret_len]

    # 将涨跌幅数据转换成numpy的array格式
    array = np.array(data.tolist(), dtype=object)
    # 获取持仓周期数
    future_period = len(array[0])
    hold_period = min(hold_period, future_period)
    # 截取涨跌幅数据
    array = array[:, :hold_period]  # 行全选，列只选取前hold_period列
    # 计算整体资金曲线
    array = array.mean(axis=0)
    # 判断是否存在0的情况，即爆仓
    ins = np.argwhere(array == 0)
    # 判断如果有爆仓的情况，只取到爆仓的周期
    if len(ins) != 0:
        array = array[:ins[0][0] + 1]

    return list(array)


def update_df(toperiod_event, start_index, cap_num, cap):
    """
    :param toperiod_event:  当前周期的事件数据
    :param start_index:  开始的index，为update使用
    :param cap_num:  使用哪一份资金进行投资
    :param cap:  投资金额是多少
    :return:
    """
    # 获取持仓每周期净值
    value_list = toperiod_event.iloc[0]['持仓每周期净值']

    # 创建用来更新的df
    index = range(start_index, start_index + len(value_list))
    df = pd.DataFrame(index=index)

    # 给更新的df赋值
    df['%s_资金' % cap_num] = value_list
    df['%s_资金' % cap_num] *= cap

    # 判断投入资金是否为0，如果是0证明没钱买入，就全部赋值为空
    if cap == 0:
        df['%s_币种' % cap_num] = None
        df['%s_余数' % cap_num] = 0
    else:
        df['%s_币种' % cap_num] = toperiod_event.iloc[0]['买入币种']
        df['%s_余数' % cap_num] = range(len(value_list), 0, -1)

    return df


def filter_events(df, filter_info):
    """
    根据规则删除不交易的币种
    :param df:
    :param filter_info:
    :return:
    """
    df['keep'] = True
    for k, v in filter_info.items():
        for i in v:
            df.loc[df[k].str.contains(i), 'keep'] = False

    # 只保留需要保留的数据
    df = df[df['keep'] == True]
    del df['keep']
    return df
