"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import math
import time
import traceback
import pandas as pd
from datetime import timedelta, datetime
from utils.commons import retry_wrapper


# =====获取数据
# 获取单个币种的1小时数据
def fetch_binance_swap_candle_data(exchange, symbol, run_time, limit=1500):

    # ===获取K线数据
    # 计算获取k线的开始时间
    start_time_dt = run_time - timedelta(hours=limit)
    params = {
        'symbol': symbol,   # 获取币种
        'interval': '1h',   # 获取k线周期
        'limit': limit,     # 获取多少根
        'startTime': int(time.mktime(start_time_dt.timetuple())) * 1000  # 获取币种开始时间
    }
    # 获取指定币种的k线数据
    try:
        kline = retry_wrapper(exchange.fapiPublic_get_klines, params=params, func_name='fapiPublic_get_klines')
    except Exception as e:
        print(traceback.format_exc())
        # 如果获取k线重试出错，直接返回，当前币种不参与交易
        return pd.DataFrame()

    # ===整理数据
    # 将数据转换为DataFrame
    df = pd.DataFrame(kline, dtype='float')
    # 对字段进行重命名，字段对应数据可以查询文档（https://binance-docs.github.io/apidocs/futures/cn/#k）
    columns = {0: 'candle_begin_time', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume', 6: 'close_time', 7: 'quote_volume',
               8: 'trade_num', 9: 'taker_buy_base_asset_volume', 10: 'taker_buy_quote_asset_volume', 11: 'ignore'}
    df.rename(columns=columns, inplace=True)

    df['symbol'] = symbol  # 添加symbol列
    df.sort_values(by=['candle_begin_time'], inplace=True)  # 排序
    df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True) # 去重

    # 转换数据时区
    utc_offset = int(time.localtime().tm_gmtoff / 60 / 60)  # 获取服务器所在的当前时区
    df['candle_begin_time'] = pd.to_datetime(df['candle_begin_time'], unit='ms') + pd.Timedelta(hours=utc_offset)

    # 删除runtime那根未走完的k线数据（交易所有时候会返回这条数据）
    df = df[df['candle_begin_time'] < run_time]
    df.reset_index(drop=True, inplace=True)

    return df


# 获取所有币种永续合约数据的1小时K线数据
def fetch_all_binance_swap_candle_data(exchange, symbol_list, run_time, limit):
    """
    获取所有币种永续合约数据的1小时K线数据

    :param exchange:    交易所对象，用于获取数据
    :param symbol_list: 币种泪飙
    :param run_time:    当前运行时间
    :return:

    {
    'BTCUSDT':
                            symbol  ... taker_buy_quote_asset_volume
            0     BTCUSDT  ...                 1.451404e+08
            1     BTCUSDT  ...                 1.492456e+08
            2     BTCUSDT  ...                 1.200780e+08
            3     BTCUSDT  ...                 9.680288e+07
            4     BTCUSDT  ...                 6.867702e+08
            ...       ...  ...                          ...
            1495  BTCUSDT  ...                 1.858995e+08
            1496  BTCUSDT  ...                 1.151737e+08
            1497  BTCUSDT  ...                 8.091855e+07
            1498  BTCUSDT  ...                 1.037028e+08
            1499  BTCUSDT  ...                 1.111743e+07,

    'ETHUSDT':
            symbol  ... taker_buy_quote_asset_volume
            0     ETHUSDT  ...                 2.023519e+08
            1     ETHUSDT  ...                 1.813869e+08
            2     ETHUSDT  ...                 1.298206e+08
            3     ETHUSDT  ...                 1.544976e+08
            4     ETHUSDT  ...                 6.494550e+08
            ...       ...  ...                          ...
            1495  ETHUSDT  ...                 2.792866e+08
            1496  ETHUSDT  ...                 1.220917e+08
            1497  ETHUSDT  ...                 7.935349e+07
            1498  ETHUSDT  ...                 1.557781e+08
            1499  ETHUSDT  ...                 2.241793e+07,
    ......
    }
    """
    # 这里用dict存储，方便后面数据处理操作
    result = {}
    for symbol in symbol_list:
        # 获取k线数据
        df = fetch_binance_swap_candle_data(exchange, symbol, run_time, limit)
        # 返回None或者空的df，不放到result里
        if df is None or df.empty:
            continue
        # 将数据添加到result中
        result[symbol] = df

    return result


# 获取币安的ticker数据
def fetch_binance_ticker_data(exchange):
    # 获取所有币种的ticker数据
    tickers = retry_wrapper(exchange.fapiPublic_get_ticker_price, func_name='fapiPublic_get_ticker_price')
    tickers = pd.DataFrame(tickers, dtype=float)
    tickers.set_index('symbol', inplace=True)

    return tickers['price']


def load_market(exchange, black_list):
    """
    加载市场数据

    :param exchange:    交易所对象，用于获取数据
    :param black_list:  黑名单
    :return:

    symbol_list     币种列表
        ['BTCUSDT', 'ETHUSDT', 'BCHUSDT', ......]
    min_qty         最小下单精度    例： 3 代表 0.001
        {'BTCUSDT': 3, 'ETHUSDT': 3, 'BCHUSDT': ,....}3
    price_precision 币种价格精     例： 2 代表 0.01
        {'BTCUSDT': 1, 'ETHUSDT': 2, 'BCHUSDT': 2, 'XRPUSDT': 4,...}
    min_notional    最小下单金额    例： 5.0 代表 最小下单金额是5U
        {'BTCUSDT': 5.0, 'ETHUSDT': 5.0, 'BCHUSDT': 5.0, 'XRPUSDT': 5.0...}
    """
    # ===获取交易对的信息
    exchange_info = retry_wrapper(exchange.fapiPublic_get_exchangeinfo, func_name='fapiPublic_get_exchangeinfo')

    # ===挑选出所有的交易对
    now_ms = datetime.now().timestamp() * 1000
    symbol_dict_list = list(filter(lambda s: ((now_ms - int(s['onboardDate'])) / 1000 / 86400) >= 3  # 挑选上架时间超过3天的交易对
                                         and s['status'] == 'TRADING'  # 挑选交易状态的交易对
                                         and s['quoteAsset'] == 'USDT'  # 挑选U本位结算的交易对
                                         and s['contractType'] == 'PERPETUAL', exchange_info['symbols']))
    symbol_list = [x['symbol'] for x in symbol_dict_list]  # 获取所有的交易对名称

    # 删除在黑名单中的币种
    symbol_list = set(symbol_list) - set(black_list)  # 使用set集合操作
    symbol_list = list(symbol_list)

    # ===获取各个交易对的精度、下单量等信息
    min_qty = {}  # 最小下单精度，例如bnb，一次最少买入0.001个
    price_precision = {}  # 币种价格精，例如bnb，价格是158.887，不能是158.8869
    min_notional = {}  # 最小下单金额，例如bnb，一次下单至少买入金额是5usdt
    # 遍历获得想要的数据
    for info in exchange_info['symbols']:
        symbol = info['symbol']
        for _filter in info['filters']:
            if _filter['filterType'] == 'PRICE_FILTER':
                price_precision[symbol] = int(math.log(float(_filter['tickSize']), 0.1))
            elif _filter['filterType'] == 'LOT_SIZE':
                min_qty[symbol] = int(math.log(float(_filter['minQty']), 0.1))
            elif _filter['filterType'] == 'MIN_NOTIONAL':
                min_notional[symbol] = float(_filter['notional'])

    return symbol_list, min_qty, price_precision, min_notional


# 重置一下页面最大杠杆
def reset_leverage(exchange, max_leverage=3):
    """
    重置一下页面最大杠杆
    :param exchange:        交易所对象，用于获取数据
    :param max_leverage:    设置页面最大杠杆
    """
    # 获取账户持仓风险（这里有杠杆数据）
    position_risk = retry_wrapper(exchange.fapiPrivate_get_positionrisk, func_name='fapiPrivate_get_positionrisk')
    position_risk = pd.DataFrame(position_risk)  # 将数据转成DataFrame
    position_risk.set_index('symbol', inplace=True)  # 将symbol设为index

    # 遍历每一个可以持仓的币种，修改页面最大杠杆
    for symbol, row in position_risk.iterrows():
        if row['leverage'] != max_leverage:
            # 设置杠杆
            retry_wrapper(exchange.fapiPrivate_post_leverage,
                          params={'symbol': symbol, 'leverage': max_leverage},
                          func_name='fapiPrivate_post_leverage')

    print('修改页面最大杠杆操作完成')
