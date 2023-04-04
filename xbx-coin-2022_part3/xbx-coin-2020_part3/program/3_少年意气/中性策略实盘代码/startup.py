"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.unicode.ambiguous_as_wide', True)  # 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.east_asian_width', True)
from api.market import *
from api.position import *
from api.trade import *
from utils.functions import *
from utils.commons import *
from utils.dingding import *
from config import *


def run():
    while True:
        # ===加载各个交易对的信息
        symbol_list, min_qty, price_precision, min_notional = load_market(exchange, black_list)
        # symbol_list = symbol_list[:10]  # 测试用

        # ===获取U本位合约账户净值(不包含未实现盈亏)
        equity = retry_wrapper(exchange.fapiPrivate_get_account, func_name='fapiPrivate_get_account')  # 获取账户净值
        equity = pd.DataFrame(equity['assets'])
        equity = float(equity[equity['asset'] == 'USDT']['walletBalance'])
        print('账户金额:', equity)
        if equity <=0:
            print('账户USDT金额小于等于0， 无法进行交议，退出程序')
            exit()

        # ===获取账户的实际持仓
        position_df = get_position_df(exchange)

        # ===发送钉钉
        send_dingding_msg_for_position(equity, position_df)

        # ===sleep直到下一个整点小时
        run_time = sleep_until_run_time('1h', if_sleep=True, cheat_seconds=0)
        # run_time = datetime.strptime('2023-02-02 16:18:00', "%Y-%m-%d %H:%M:%S")

        # ===获取所有币种的1小时K线
        s_time = datetime.now()
        symbol_candle_data = fetch_all_binance_swap_candle_data(exchange, symbol_list, run_time, get_kline_num)
        print('获取所有币种K线数据完成，花费时间：', datetime.now() - s_time)

        # =====选币数据整理 & 选币
        s_time = datetime.now()
        select_coin = cal_factor_and_select_coin(symbol_candle_data, strategy, run_time, get_kline_num)
        print('完成选币数据整理 & 选币，花费时间：', datetime.now() - s_time)
        print('选币结果：\n', select_coin)

        # =====开始计算具体下单信息
        symbol_order = cal_order_amount(position_df, select_coin, strategy, equity, leverage)
        print('下单信息：\n', symbol_order)

        # =====下单
        symbol_last_price = fetch_binance_ticker_data(exchange)  # 获取币种的最新价格
        place_order(exchange, symbol_order, symbol_last_price, min_qty, price_precision, min_notional)

        # =====清理数据
        del symbol_candle_data, select_coin, symbol_order
        # 本次循环结束
        print('-' * 20, '本次循环结束，%f秒后进入下一次循环' % 20, '-' * 20)
        print('\n')
        time.sleep(20)


if __name__ == '__main__':
    # ===设置一下页面最大杠杆
    reset_leverage(exchange, 3)
    while True:
        try:
            run()
        except Exception as err:
            msg = '系统出错，10s之后重新运行，出错原因: ' + str(err)
            print(msg)
            print(traceback.format_exc())
            send_dingding_msg(msg)
            time.sleep(10)
