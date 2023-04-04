"""
《邢不行-2022新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx9025
本程序作者: 邢不行

# 课程内容
BN常用函数汇总
"""

import ccxt
import pandas as pd
import time

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# 初始化交易所变量
BINANCE_CONFIG = {'enableRateLimit': False,
                  # 'proxies': {'http': 'http://127.0.0.1:7890', 'https': 'https://127.0.0.1:7890'}
                  }
exchange = ccxt.binance(BINANCE_CONFIG)

# 1.获取交易规则和交易对
# GET /fapi/v1/exchangeInfo
# https://binance-docs.github.io/apidocs/futures/cn/#0f3f2d5ee7
response = exchange.fapiPublicGetExchangeinfo()['symbols']
info = pd.DataFrame(response)
print('获取交易规则和交易对\n', info.tail(), '\n')

# 2.获取最新价格
# GET /fapi/v1/ticker/price
# https://binance-docs.github.io/apidocs/futures/cn/#8ff46b58de
response = exchange.fapiPublicGetTickerPrice()
price = pd.DataFrame(response)
print('获取最新价格\n', price.tail(), '\n')

# 3.K线数据
# GET /fapi/v1/klines
# https://binance-docs.github.io/apidocs/futures/cn/#k
params = {'symbol': 'BTCUSDT',  # 交易币对
          'interval': '15m'}
response = exchange.fapiPublicGetKlines(params=params)
k_lines = pd.DataFrame(response)
print('K线数据\n', k_lines.tail(), '\n')
# rename,pd.to_datetime(unit='ms')

# 4.最新标记价格和资金费率
# GET /fapi/v1/premiumIndex
# https://binance-docs.github.io/apidocs/futures/cn/#69f9b0b2f3
params = {'symbol': 'BTCUSDT'}  # 交易币对
response = exchange.fapiPublicGetPremiumIndex(params=params)
premium_index = pd.DataFrame(response, index=[0])
print('最新标记价格和资金费率\n', premium_index.tail(), '\n')
