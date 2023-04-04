"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
import time
from config import *
import json
from utils.commons import retry_wrapper
from utils.dingding import *


# 下单
def place_order(exchange, symbol_order, symbol_last_price, min_qty, price_precision, min_notional):
    """
    根据计算好的下单数据，进行下单

    :param exchange:            交易所对象
    :param symbol_order:        计算好的币种下单数据
    :param symbol_last_price:   所有币种最新ticker价格
    :param min_qty:             币种最小下单精度
    :param price_precision:     币种最小价格精度
    :param min_notional:        币种最小下单金额
    """
    # 遍历symbol_order，构建每个币种的下单参数
    order_param_list = []
    for symbol, row in symbol_order.iterrows():
        # ===若当前币种没有最小下单精度、或最小价格精度，报错
        if (symbol not in min_qty) or (symbol not in price_precision):
            # 报错
            raise Exception('当前币种没有最小下单精度、或最小价格精度，币种信息异常')

        # ===计算下单量、方向、价格
        quantity = row['实际下单量']
        quantity = round(quantity, min_qty[symbol])  # 按照最小下单量四舍五入
        # 计算下单方向、价格，并增加一定的滑点
        if quantity > 0:
            side = 'BUY'
            price = symbol_last_price[symbol] * 1.015
        else:
            side = 'SELL'
            price = symbol_last_price[symbol] * 0.985
        # 下单量取绝对值
        quantity = abs(quantity)
        # 通过最小价格精度对下单价格进行四舍五入
        price = round(price, price_precision[symbol])

        # ===判断是否是清仓交易
        reduce_only = True if row['交易模式'] == '清仓' else False

        # ===判断交易金额是否小于最小下单金额（一般是5元），小于的跳过
        if quantity * price < min_notional.get(symbol, 5):
            if not reduce_only:  # 清仓状态不跳过
                print(symbol, '交易金额是小于最小下单金额（一般是5元），跳过该笔交易')
                print('下单量：', quantity, '价格：', price)
                continue

        # ===构建下单参数
        order_params = {'symbol': symbol, 'side': side, 'type': 'LIMIT', 'price': str(price), 'quantity': str(quantity),
                        'newClientOrderId': str(time.time()), 'timeInForce': 'GTC', 'reduceOnly': str(bool(reduce_only))}
        order_param_list.append(order_params)

    print('每个币种的下单参数：', order_param_list)

    # 批量下单，每5个订单打包执行
    for i in range(0, len(order_param_list), 5):
        order_info = order_param_list[i: i + 5]
        try:
            # 批量下单
            oder_res = retry_wrapper(exchange.fapiPrivate_post_batchorders,
                                     params={'batchOrders': json.dumps(order_info)},
                                     func_name='fapiPrivate_post_batchorders')
            print('批量下单完成，批量下单信息结果：', oder_res)
        except Exception as e:
            print(e)
            continue
        # 发送下单结果到钉钉
        send_dingding_msg_for_order(order_info, oder_res)
