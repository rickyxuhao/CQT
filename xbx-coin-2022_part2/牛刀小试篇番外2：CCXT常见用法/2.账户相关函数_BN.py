"""
《邢不行-2022新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx9025
本程序作者: 邢不行

# 课程内容
binance常用函数汇总
"""

import ccxt
import pandas as pd
import time

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

BINANCE_CONFIG = {
    'apiKey': '',
    'secret': '',
    'rateLimit': 10,
    'verbose': False,
    'enableRateLimit': False,
    # 'proxies': {'http': 'http://127.0.0.1:7890', 'https': 'https://127.0.0.1:7890'}
}
exchange = ccxt.binance(BINANCE_CONFIG)

# 1.账户信息V2 (USER_DATA)
# GET /fapi/v2/account (HMAC SHA256)
# https://binance-docs.github.io/apidocs/futures/cn/#v2-user_data-2
response = exchange.fapiPrivateGetAccount()['assets']
account = pd.DataFrame(response)
print('账户信息\n', account.tail(), '\n')

# 2.调整开仓杠杆 (TRADE)
# POST /fapi/v1/leverage (HMAC SHA256)
# https://binance-docs.github.io/apidocs/futures/cn/#trade-10
params = {'symbol': 'BTCUSDT',  # 交易币对
          'leverage': 15,
          'timestamp': int(time.time() * 1000)}
leverage = exchange.fapiPrivatePostLeverage(params=params)
print('调整开仓杠杆\n', leverage, '\n')

# 3.下单 (TRADE)
# POST /fapi/v1/order (HMAC SHA256)
# https://binance-docs.github.io/apidocs/futures/cn/#trade-3
params = {'side': 'BUY',
          'symbol': 'BTCUSDT',  # 交易币对
          'type': 'LIMIT',
          'price': 23600,  # 下单价格,在限价单的时候启用，将type换成LIMIT
          'quantity': 0.001,  # 下单数量
          'timestamp': int(time.time() * 1000),
          'timeInForce': 'GTC'}
response = exchange.fapiPrivatePostOrder(params=params)
order_info = pd.DataFrame(response, index=['symbol'])
order_id = order_info['orderId'].iloc[0]
print('下单\n', order_info, '\n')
# 4.查询订单 (USER_DATA)
# GET /fapi/v1/order (HMAC SHA256)
# https://binance-docs.github.io/apidocs/futures/cn/#user_data-3
params = {'symbol': 'BTCUSDT',  # 交易币对
          'timestamp': int(time.time() * 1000),
          'orderId': order_id}  # 至少需要发送 orderId 与 origClientOrderId中的一个
response = exchange.fapiPrivateGetOrder(params=params)
order = pd.DataFrame(response, index=[0])
print('查询订单\n', order, '\n')

# 5.撤销订单 (TRADE)
# DELETE /fapi/v1/order (HMAC SHA256)
# https://binance-docs.github.io/apidocs/futures/cn/#trade-6
params = {'symbol': 'BTCUSDT',  # 交易币对
          'timestamp': int(time.time() * 1000),
          'orderId': order_id}  # 至少需要发送 orderId 与 origClientOrderId中的一个
response = exchange.fapiPrivateDeleteOrder(params=params)
delete = pd.DataFrame(response, index=[0])
print('撤销订单\n', delete, '\n')
