"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import pandas as pd
import time
from datetime import timedelta
from config import feature_list, filter_list
from utils.Filter import before_filter


def select_long_and_short_coin(df, select_coin_num):
    """
    选币
    :param df:                  数据集
    :param select_coin_num:     选币数量
    :return:
    """
    # 计算因子的分组排名
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
    df = pd.concat([long_df, short_df], ignore_index=True)  # 将做多和做空的币种数据合并
    df = df[['candle_begin_time', 'symbol', 'close', '方向']]  # 保留需要的列
    df.sort_values(by=['candle_begin_time', '方向'], ascending=[True, False], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def cal_multi_factor_rank(df, factor_list, factor_tag='因子'):
    """
    计算多因子组合成复合因子
    :param df:              数据集
    :param factor_list:     配置的信息
    :param factor_tag:      复合因子的因子名称
    :return:
    """
    # 这里根据配置因子是否反转信息和因子权重信息，进行权重求和
    df[factor_tag] = 0
    for factor_name, if_reverse, parameter_list, weight in factor_list:
        reverse = -1 if if_reverse else 1
        df[factor_tag] += (df[f'{factor_name}_{str(parameter_list)}'] * reverse * weight)

    return df


def cal_factors(df, all_factor_list, run_time, hold_period, all_filter_list=[]):
    # 解析出选币因子的信息，并进行计算
    for factor, if_reverse, parameter_list, weight in all_factor_list:
        factor_name = f'{factor}_{str(parameter_list)}'
        _cls = __import__('factors.%s' % factor, fromlist=('',))
        df = getattr(_cls, 'signal')(df, parameter_list, factor_name)

    # 如果配置了过滤因子，解析出过滤因子的信息，并进行计算
    if len(all_filter_list) > 0:
        for factor, parameter_list in all_filter_list:
            factor_name = f'{factor}_{str(parameter_list)}'
            _cls = __import__('filters.%s' % factor, fromlist=('',))
            df = getattr(_cls, 'signal')(df, parameter_list, factor_name)

    # 只保留最近的数据
    df = df[df['candle_begin_time'] >= (run_time - timedelta(hours=hold_period))]
    # 只保留需要的字段
    df = df[['candle_begin_time', 'symbol', 'close'] + feature_list + filter_list]

    return df


# =====策略相关函数
# 选币数据整理 & 选币
def cal_factor_and_select_coin(symbol_candle_data, strategy, run_time, kline_size=99):
    """
    选币数据整理 & 选币
    :param symbol_candle_data:      1h的k线数据
    :param strategy:                策略信息
    :param run_time:                当前运行的时间
    :param kline_size:              币种所需的k线数量，不满足不交易这个币种
    :return:

         candle_begin_time    symbol  close  方向  offset
    0  2022-10-28 09:00:00   EOSUSDT  1.140   1       3
    1  2022-10-28 09:00:00  LINKUSDT  6.940  -1       3
    2  2022-10-28 10:00:00   EOSUSDT  1.127   1       4
    3  2022-10-28 10:00:00  LINKUSDT  6.861  -1       4
    4  2022-10-28 11:00:00   EOSUSDT  1.136   1       5
    5  2022-10-28 11:00:00  LINKUSDT  6.893  -1       5
    6  2022-10-28 12:00:00   EOSUSDT  1.142   1       0
    7  2022-10-28 12:00:00  LINKUSDT  6.899  -1       0
    8  2022-10-28 13:00:00   EOSUSDT  1.139   1       1
    9  2022-10-28 13:00:00  LINKUSDT  6.918  -1       1
    10 2022-10-28 14:00:00   EOSUSDT  1.142   1       2
    11 2022-10-28 14:00:00  LINKUSDT  6.926  -1       2
    """
    # ===删除成交量为0的线数据、k线数不足的币种
    symbol_list = list(symbol_candle_data.keys())
    for symbol in symbol_list:
        # 删除该币种成交量=0的k线
        symbol_candle_data[symbol] = symbol_candle_data[symbol][symbol_candle_data[symbol]['volume'] > 0]
        # 若该币种的k线数量太少，不满足要求，直接删除这个币种的数据
        if len(symbol_candle_data[symbol]) < kline_size:
            del symbol_candle_data[symbol]

    # ===因子计算
    # hold_period的作用是计算完因子之后，获取最近 hold_period 个小时内的数据信息，同时用于offset字段计算使用
    hold_period = int(strategy['hold_period'][:-1])
    # 遍历每个币种，计算相关因子数据
    all_df_list = []
    for df in symbol_candle_data.values():
        df = cal_factors(df, strategy['factors'], run_time, hold_period, all_filter_list=strategy['filter_list'])
        if df is not None and not df.empty:
            all_df_list.append(df)

    # ===合并并整理所有K线
    all_df = pd.concat(all_df_list, ignore_index=True)
    all_df.dropna(subset=feature_list + filter_list, inplace=True)  # 删除选币因子为空的数据
    all_df.sort_values(by=['candle_begin_time', 'symbol'], inplace=True)
    all_df.reset_index(drop=True, inplace=True)

    # ===对因子进行排名
    all_df['因子'] = 0
    for factor_name, if_reverse, parameter_list, weight in strategy['factors']:
        col_name = f'{factor_name}_{str(parameter_list)}'
        # 计算单个因子的排名
        all_df[col_name] = all_df.groupby('candle_begin_time')[col_name].rank(ascending=if_reverse)
        # 将因子按照权重累加
        all_df['因子'] += (all_df[col_name] * weight)
    all_df = all_df[['candle_begin_time', 'symbol', 'close', '因子'] + filter_list]  # 只保留需要的字段

    # ===前置过滤
    # all_df = before_filter(all_df)

    # ===选币
    all_df = select_long_and_short_coin(all_df, strategy['select_coin_num'])

    # 过滤可能造成出现当周期不足选出同时做多和做空币种的时候，这里将这些数据过滤掉，当周期内直接空仓
    all_df['总币数'] = all_df.groupby('candle_begin_time')['symbol'].transform('nunique')
    all_df = all_df[all_df['总币数'] >= strategy['select_coin_num'] * 2]  # 去除选币数量不足的数据

    # ===筛选合适的offset
    utc_offset = int(time.localtime().tm_gmtoff / 60 / 60)  # 获取服务器所在的当前时区
    all_df['utc_offset'] = (all_df['candle_begin_time'] - pd.Timedelta(hours=utc_offset)).dt.hour % hold_period  # 计算每个周期属于的offset
    all_df = all_df[all_df['utc_offset'].isin(strategy['offset_list'])]  # 保留配置中的offset数据

    # ===返回选币结果
    return all_df


# =====计算实际下单量
def cal_order_amount(position_df, select_coin, strategy, equity, leverage):
    """
    计算实际下单量

    :param position_df:             持仓信息
    :param select_coin:             选币结果
    :param strategy:                策略信息
    :param equity:                  账号交易金额
    :param leverage:                杠杆
    :return:

               当前持仓量   目标持仓量  目标下单份数   实际下单量 交易模式
    AUDIOUSDT         0.0 -2891.524948          -3.0 -2891.524948     建仓
    BANDUSDT        241.1     0.000000           NaN  -241.100000     清仓
    C98USDT        -583.0     0.000000           NaN   583.000000     清仓
    ENJUSDT           0.0  1335.871133           3.0  1335.871133     建仓
    WAVESUSDT        68.4     0.000000           NaN   -68.400000     清仓
    KAVAUSDT       -181.8     0.000000           NaN   181.800000     清仓

    """
    # ===计算目标持仓量
    strategy_trade_usdt = equity * leverage / len(strategy['offset_list']) / strategy['select_coin_num'] / 2  # 计算每个offset、每个币分配的资金
    select_coin['目标持仓量'] = strategy_trade_usdt / select_coin['close'] * select_coin['方向']  # 计算每个币种的目标持仓量

    # ===创建symbol_order，用来记录要下单的币种的信息
    # =创建一个空的symbol_order，里面有select_coin（选中的币）、position_df（当前持仓）中的币种
    symbol_order = pd.DataFrame(index=list(set(select_coin['symbol']) | set(position_df.index)), columns=['当前持仓量'])
    # =symbol_order中更新当前持仓量
    symbol_order['当前持仓量'] = position_df['当前持仓量']
    symbol_order['当前持仓量'].fillna(value=0, inplace=True)

    # =目前持仓量当中，可能可以多空合并
    symbol_order['目标持仓量'] = select_coin.groupby('symbol')[['目标持仓量']].sum()
    symbol_order['目标持仓量'].fillna(value=0, inplace=True)

    # ===计算实际下单量和实际下单资金
    symbol_order['实际下单量'] = symbol_order['目标持仓量'] - symbol_order['当前持仓量']

    # ===计算下单的模式，清仓、建仓、调仓等
    symbol_order = symbol_order[symbol_order['实际下单量'] != 0]  # 过滤掉实际下当量为0的数据
    symbol_order.loc[symbol_order['目标持仓量'] == 0, '交易模式'] = '清仓'
    symbol_order.loc[symbol_order['当前持仓量'] == 0, '交易模式'] = '建仓'
    symbol_order['交易模式'].fillna(value='调仓', inplace=True)  # 增加或者减少原有的持仓，不会降为0

    return symbol_order
