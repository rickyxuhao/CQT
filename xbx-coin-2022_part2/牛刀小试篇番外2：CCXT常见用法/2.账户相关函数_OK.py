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

# =交易所配置
OKEX_CONFIG = {
    'apiKey': '',
    'secret': '',
    'password': '',
    'rateLimit': 10,
    # 'hostname': 'okex.com',  # 无法fq的时候启用
    'enableRateLimit': False,
    # 'proxies': {'http': 'http://127.0.0.1:7890', 'https': 'https://127.0.0.1:7890'}
}
exchange = ccxt.okx(OKEX_CONFIG)

# 1.获取资金账户余额
# GET /api/v5/account/balance
# https://www.okx.com/docs-v5/zh/#rest-api-account-get-balance
para = {'ccy': 'USDT'}
response = exchange.privateGetAccountBalance(params=para)['data']
balances = pd.DataFrame(response)
print('获取资金账户余额\n', balances, '\n')

# 2.设置杠杆倍数
# POST /api/v5/account/set-leverage
# https://www.okx.com/docs-v5/zh/#rest-api-account-get-leverage
para = {'instId': 'BTC-USDT-SWAP',
        'lever': '10',
        'mgnMode': 'cross'}
leverage = exchange.privatePostAccountSetLeverage(params=para)
print('设置杠杆倍数\n', leverage, '\n')

# 3.下单
# POST /api/v5/trade/order
# https://www.okx.com/docs-v5/zh/#rest-api-trade-place-order
para = {'instId': 'BTC-USDT-SWAP',  # 合约代码
        'tdMode': 'cross',  # 设置为全仓,可以调整    isolated：逐仓    cross：全仓   cash：非保证金
        'ordType': 'limit',  # 设置为市价单
        'side': 'buy',  # 买卖方向
        'sz': '1',  # 下单数量
        'px': '23600'}
order_info = exchange.privatePostTradeOrder(params=para)
print('下单\n', order_info, '\n')
order_id = order_info['data'][0]['ordId']

# 4.获取订单信息
# GET /api/v5/trade/order
# https://www.okx.com/docs-v5/zh/#rest-api-trade-get-order-details
para = {'instId': 'BTC-USDT-SWAP',  # 合约代码
        'ordId': order_id}  # ordId和clOrdId必须传一个，若传两个，以ordId为主
order_info = exchange.privateGetTradeOrder(params=para)
print('获取订单信息\n', order_info, '\n')

# 5.撤单
# POST /api/v5/trade/cancel-order
# https://www.okx.com/docs-v5/zh/#rest-api-trade-cancel-order
para = {'instId': 'BTC-USDT-SWAP',  # 合约代码
        'ordId': order_id}  # ordId和clOrdId必须传一个，若传两个，以ordId为主
order_info = exchange.privatePostTradeCancelOrder(params=para)
print('撤单\n', order_info, '\n')
