# -*- coding: utf-8 -*-
"""
Created on Sat Apr  8 14:30:44 2023

@author: ASUS
"""

import pandas as pd
import ccxt
import time
import os
from datetime import timedelta

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行


# =====设定参数
exchange = ccxt.binance({'proxies':{
    'http': '127.0.0.1:10809',
    'https': '127.0.0.1:10809',
}})  # huobipro, binance, okex5，使用huobi需要增加limit=2000，XRP-USDT-200327
# okex = ccxt.okex5()
symbol = 'BTCUSDT'
time_interval = '1h'  # 其他可以尝试的值：'1m', '5m', '15m', '30m', '1H', '2H', '1D', '1W', '1M', '1Y'

# =====抓取数据开始结束时间
start_time = '2021-04-01 00:00:00'
end_time = '2023-04-01 00:00:00'
# end_time = pd.to_datetime(start_time) + timedelta(days=1)



# =====开始循环抓取数据
df_list = []
start_time_since = exchange.parse8601(start_time)
end_time_since = exchange.parse8601(end_time)


# 循环获取历史数据
all_kline_data = []


df_list = []
start_time_since = exchange.parse8601(start_time)
while True:

    # 获取数据
    df = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, since=start_time_since, limit=2000)

    # 整理数据
    df = pd.DataFrame(df, dtype=float)  # 将数据转换为dataframe
    df['candle_begin_time'] = pd.to_datetime(df[0], unit='ms')  # 整理时间
    print(df)

    # 合并数据
    df_list.append(df)

    # 新的since
    t = pd.to_datetime(df.iloc[-1][0], unit='ms')
    print(t)
    new_start_time = pd.to_datetime(t) + timedelta(days=1)
    start_time_since = exchange.parse8601(str(new_start_time))

    # 判断是否挑出循环
    # print(t) 
    # print(type(t))
    # print(end_time) 
    # print(type(end_time))
    if (str(t) >= end_time) or (df.shape[0] <= 1):
        print('抓取完所需数据，或抓取至最新数据，完成抓取任务，退出循环')
        break

    # 抓取间隔需要暂停2s，防止抓取过于频繁
    time.sleep(2)
    
# =====合并整理数据
df = pd.concat(df_list, ignore_index=True)

df.rename(columns={0: 'MTS', 1: 'open', 2: 'high',
                   3: 'low', 4: 'close', 5: 'volume'}, inplace=True)  # 重命名
df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')  # 整理时间
df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]  # 整理列的顺序

# 选取数据时间段
# df = df[df['candle_begin_time'].dt.date == pd.to_datetime(start_time).date()]

# 去重、排序
df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True)
df.sort_values('candle_begin_time', inplace=True)
df.reset_index(drop=True, inplace=True)



# =====保存数据到文件
if df.shape[0] > 0:
    # 根目录，确保该路径存在

    path = r'.\data\history_candle_data'
    
    # 创建交易所文件夹
    path = os.path.join(path, exchange.id)
    if os.path.exists(path) is False:
        os.mkdir(path)
    # 创建spot文件夹
    path = os.path.join(path, 'spot')
    if os.path.exists(path) is False:
        os.mkdir(path)
    # 创建日期文件夹
    path = os.path.join(path, str(pd.to_datetime(start_time).date()))
    if os.path.exists(path) is False:
        os.mkdir(path)
    
    # 拼接文件目录
    file_name = '_'.join([symbol.replace('/', '-'), time_interval]) + '.csv'
    path = os.path.join(path, file_name)
    print(path)
    
    df.to_csv(path, index=False)
