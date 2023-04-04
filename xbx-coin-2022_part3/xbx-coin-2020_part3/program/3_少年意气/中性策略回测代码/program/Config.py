"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import os

_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
root_path = os.path.abspath(os.path.join(_, '..'))  # 返回根目录文件夹

# 币安永续合约历史1小时数据-币对分类  下载地址:https://www.quantclass.cn/data/coin/coin-binance-swap-candle-csv-1h
# k线数据路径(注意最后需要保留一个 '/' )
kline_path = root_path + r'/data/k线数据/'

# 回测信息配置
start_date = '2021-01-01'  # 回测开始时间
end_date = '2023-01-01'  # 回测结束时间
select_coin_num = 1  # 选币数量。1 表示做多一个币，同时做空一个币
c_rate = 4 / 10000  # 手续费
min_kline_num = 99  # 最小k线限制。如果币种k线少于 min_kline_num ，就不交易该币种。与实盘 get_kline_num 对应
hold_period = '6H'  # 持仓周期
leverage = 1  # 资金杠杆。举例：本金100元，其中50元作为保证金，开多价值50元的币。另外50元作为保证金，开空价值50元的币。
margin_rate = 0.05  # 维持保证金率，净值低于这个比例会爆仓。这个比例是交易所定的
black_list = ['BTCDOM-USDT', 'DEFI-USDT']  # 黑名单。不参与交易的币种

# 需要使用的选币因子
factor_class_list = ['Bias', 'Cci', 'Cci_v3', 'Volume']

# 需要使用的过滤因子
filter_class_list = ['ZhangDieFuAbsMax', 'TakerBuy']
