"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import ccxt


# =====总资金杠杆数(一定要小于页面杠杆)
leverage = 1

# =====每次请求接口获取的k线数量(如果k线不足，该币种不参与交易)
get_kline_num = 199

# =====币种黑名单(不参与交易)
black_list = ['BTCDOMUSDT', 'DEFIUSDT']

# =====策略配置
strategy = {
    "factor_name": "basic",
    "hold_period": "6H",
    "factors": [
        ('Bias', False, [21], 0.5),
        ('Cci', False, [34], 0.5)
    ],
    "filter_list": [
        ('TakerBuy', [8])
    ],
    "select_coin_num": 1,
    "offset_list": [0, 1, 2, 3, 4, 5]
}
# 将策略配置的因子信息，转换成统一格式，方便后续df操作
_feature_list = set()
for factor_name, if_reverse, parameter_list, weight in strategy['factors']:
    _feature_list.add(f'{factor_name}_{str(parameter_list)}')
# 将set转成list
feature_list = list(_feature_list)

# 将策略配置的过滤信息，转换成统一格式，方便后续df操作
_filter_list = set()
for factor_name, parameter_list in strategy['filter_list']:
    _filter_list.add(f'{factor_name}_{str(parameter_list)}')
# 将set转成list
filter_list = list(_filter_list)

# =====交易所配置
# 如果使用代理 注意替换IP和Port
proxy = {}
# proxy = {'http': 'http://192.168.31.10:7890', 'https': 'http://192.168.31.10:7890'}
# 创建交易所
exchange = ccxt.binance({
    'apiKey': "",
    'secret': "",
    'timeout': 30000,
    'rateLimit': 10,
    'enableRateLimit': False,
    'options': {
        'adjustForTimeDifference': True,
        'recvWindow': 10000,
    },
    'proxies': proxy
})


# =====钉钉配置
webhook = ''  # 钉钉机器人的webhook
secret = ''  # 钉钉机器人的密钥

