"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import pandas as pd
from utils.commons import retry_wrapper


# =====获取持仓
# 获取币安账户的实际持仓
def get_position_df(exchange):
    """
    获取币安账户的实际持仓

    :param exchange:        交易所对象，用于获取数据
    :return:

              当前持仓量   均价  持仓盈亏
    symbol
    RUNEUSDT       -82.0  1.208 -0.328000
    FTMUSDT        523.0  0.189  1.208156

    """
    # 获取原始数据
    position_df = retry_wrapper(exchange.fapiPrivate_get_positionrisk, func_name='fapiPrivate_get_positionrisk')
    position_df = pd.DataFrame(position_df, dtype='float')    # 将原始数据转化为dataframe

    # 整理数据
    columns = {'positionAmt': '当前持仓量', 'entryPrice': '均价', 'unRealizedProfit': '持仓盈亏'}
    position_df.rename(columns=columns, inplace=True)
    position_df = position_df[position_df['当前持仓量'] != 0]  # 只保留有仓位的币种
    position_df.set_index('symbol', inplace=True)  # 将symbol设置为index

    # 保留指定字段
    position_df = position_df[['当前持仓量', '均价', '持仓盈亏']]

    return position_df
