"""
《邢不行-2020新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx3636
本程序作者: 邢不行

# 课程内容
币安期现套利
"""
import ccxt
from Function import *
print(ccxt.__version__)  # 检查ccxt版本，需要最新版本，1.44.21以上


# ===参数设定
coin = 'ltc'.upper()  # 要套利的币种
future_date = '210625'  # 要套利的合约到期时间
coin_precision = 2  # 去行情页面上，看下这个币种合约的价格是小数点后几位。如果小数点后有3位，那么coin_precision就是3
execute_amount = 0.1  # 每次交易的币的数量，不能太大，影响波动。在运行程序之前，需要保证币币账户中有execute_amount数量的币
max_execute_num = 1  # 最大建仓次数。建仓这些次数之后程序就会停止。
r_threshold = 0.8  # 高于利差就开始入金，0.05代表5%


spot_fee_rate = 1 / 1000  # 根据自己的手续费进行修改。如果是bnb支付，可以修改为0。
future_fee_rate = 4 / 10000  # 根据自己的手续费进行修改。如果是bnb支付，可以修改为0。
contact_size = {
    'BTC': 100,  # 一张合约代表100美金
    'EOS': 10,  # 一张合约代表10美金
    'DOT': 10,
    'LTC': 10,
    'ETH': 10,
}  # 你套利的币种一定要在这个dict里面

# ===创建交易所
exchange = ccxt.binance()
exchange.apiKey = ''
exchange.secret = ''

balance = exchange.fetch_balance()
num = balance['USDT']['free']
print('现货账户usdt的数量：', num)

# ===开始平仓
spot_symbol_name = {'type1': coin + 'USDT', 'type2': coin + '/USDT'}
future_symbol_name = {'type1': coin + 'USD_' + future_date}

# 获取币币账户币的数量
balance = exchange.fetch_balance()
num = balance[coin]['free']
print('现货账户币的数量：', num)
if num < execute_amount:
    print('请确保现货账户中的币的数量足够')
    exit()


def main():
    now_execute_num = 0
    print(now_execute_num)

    while True:
        # ===计算价差
        # 获取现货买一数据。因为现货是卖出，取买一。
        spot_price = exchange.publicGetTickerBookTicker(params={'symbol': spot_symbol_name['type1']})['bidPrice']
        spot_price = float(spot_price)
        # 获取期货卖一数据。因为期货是，买入，取卖一。
        future_price = exchange.dapiPublicGetTickerBookTicker(params={'symbol': future_symbol_name['type1']})[0]['askPrice']
        future_price = float(future_price)

        # 计算价差
        r = future_price / spot_price - 1
        print('现货价格：%.4f，期货价格：%.4f，价差：%.4f%%' % (spot_price, future_price, r * 100))

        # ===判断价差是否满足要求
        if r > r_threshold:
            print('利差大于目标阀值，不出金')
        else:
            print('利差小于目标阀值，开始出金')

            # 计算永续合约平空数量
            contract_num = int(future_price * execute_amount / contact_size[coin])  # 计算合约张数。
            contract_num_coin_amount = contract_num * contact_size[coin] / future_price  # 合约张数对应的币的数量
            contract_fee = contract_num_coin_amount * future_fee_rate  # 合约扣除的手续费的数量

            # 计算卖出现货数量
            spot_amount = contract_num_coin_amount - contract_fee  # 币币交易卖出币的数量 = 合约平空币的数量 - 合约平空手续费
            # spot_amount = round(spot_amount, 3)
            print('平空合约张数：', contract_num, '对应币的数量：', contract_num_coin_amount, '合约手续费', contract_fee, '现货卖出数量：',
                  spot_amount)

            # 在合约交易中平空币
            price = future_price * 1.02
            price = round(price, coin_precision)
            future_order_info = binance_future_place_order(exchange=exchange, symbol=future_symbol_name['type1'],
                                                           long_or_short='平空', price=price, amount=contract_num)

            # 卖币
            price = spot_price * 0.98
            spot_order_info = binance_spot_place_order(exchange=exchange, symbol=spot_symbol_name['type2'],
                                                       long_or_short='卖出', price=price, amount=spot_amount)

            # 将合约账户的币转到币币账户，以备下次卖出
            time.sleep(2)
            binance_account_transfer(exchange=exchange, currency=coin, amount=num, from_account='合约',
                                     to_account='币币')

            # 计数
            now_execute_num = now_execute_num + 1

            print(spot_order_info['average'])
            print(future_order_info)

        # ===循环结束
        print('执行次数：', now_execute_num)
        print('*' * 20, '本次循环结束，暂停', '*' * 20, '\n')
        time.sleep(2)

        if now_execute_num >= max_execute_num:
            print('达到最大下单次数，完成建仓计划，退出程序')
            exit()


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print('系统出错，10s之后重新运行，出错原因：' + str(e))
            print(e)
            time.sleep(2)
