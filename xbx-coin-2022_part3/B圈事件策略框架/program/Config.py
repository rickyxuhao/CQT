"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
import os

# =====回测相关参数
date_start = '2020-01-01'  # 回测开始时间
date_end = '2022-02-01'  # 回测结束时间
c_rate = 2.5 / 10000  # 手续费
candle_type = 'swap'  # 指定回测使用的数据，现货是spot，永续合约是swap
rul_type = '12H'  # 使用的k线的周期

# ===== 事件相关参数
event = 'MaCross_[8, 55]'  # 指定使用的事件

hold_period = 2  # 持有周期数
max_cap_num = hold_period  # 将资金分成多少份，大小不可以超过持有周期
filters = {'symbol': ['BTCDOM-USDT', 'DEFI-USDT']}  # 需要过滤的币种信息，这些币不参与选择

symbol_num_limit = None  # 选币数，None为都买
rank_factor = None  # 当超过count_limit时，以什么为基准买入,None表示不需要排序因子
ascending = False  # rank_factor的排序方式，TRUE代表升序，FALSE代表降序
margin_rate = 0.05  # 保证金率
leverage = 1  # 杠杆倍数

# =====文件目录
_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
root_path = os.path.abspath(os.path.join(_, '../'))  # 返回根目录文件夹

# 原始K线数据路径，可以是现货数据（spot_candle）也可以是合约数据(swap_candle)
# 现货数据链接：https://www.quantclass.cn/data/coin/coin-binance-candle-csv-1h
# 合约数据链接：https://www.quantclass.cn/data/coin/coin-binance-swap-candle-csv-1h
candle_path = '/Users/xbx/Desktop/B圈课程/事件策略/data/Coin/%s_candle/'
