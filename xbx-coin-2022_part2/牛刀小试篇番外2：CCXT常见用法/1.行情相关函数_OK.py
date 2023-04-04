"""
《邢不行-2022新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx9025
本程序作者: 邢不行

# 课程内容
okx常用函数汇总
"""

import ccxt
import pandas as pd
import time

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

OKEX_CONFIG = {'enableRateLimit': False,
               # 'proxies': {'http': 'http://127.0.0.1:7890', 'https': 'https://127.0.0.1:7890'}
               }

exchange = ccxt.okx(OKEX_CONFIG)

# 1.获取所有可交易产品的信息列表
# GET /api/v5/public/instruments
# https://www.okx.com/docs-v5/zh/#rest-api-public-data-get-instruments
para = {'instType': 'FUTURES'}
response = exchange.publicGetPublicInstruments(params=para)['data']
instruments = pd.DataFrame(response)
print('获取所有可交易产品的信息列表\n', instruments.tail(), '\n')

# 2.获取所有产品行情信息
# GET /api/v5/market/tickers
# https://www.okx.com/docs-v5/zh/#rest-api-market-data-get-tickers
para = {'instType': 'SPOT'}
response = exchange.publicGetMarketTickers(params=para)['data']
tickers = pd.DataFrame(response)
print('获取所有情信息\n', tickers.tail(), '\n')

# 3.获取交易产品K线数据
# GET /api/v5/market/candles
# https://www.okx.com/docs-v5/zh/#rest-api-market-data-get-candlesticks
para = {'instId': 'KINE-USDT'}
response = exchange.publicGetMarketCandles(params=para)['data']
candles = pd.DataFrame(response)
print('获取交易产品K线数据\n', candles.tail(), '\n')

# 4.获取永续合约历史资金费率
# GET /api/v5/public/funding-rate-history
# https://www.okx.com/docs-v5/zh/#rest-api-public-data-get-funding-rate-history
para = {'instId': 'BTC-USD-SWAP'}
response = exchange.publicGetPublicFundingRateHistory(params=para)['data']
funding_rate = pd.DataFrame(response)
print('获取永续合约历史资金费率\n', funding_rate.tail(), '\n')
