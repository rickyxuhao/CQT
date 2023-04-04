"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
from dingtalkchatbot.chatbot import DingtalkChatbot
from datetime import datetime
from config import webhook, secret


# 将指定好的文本信息发送钉钉
def send_dingding_msg(text):
    try:
        ding = DingtalkChatbot(webhook=webhook, secret=secret)
        msg = text + "\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ding.send_text(msg=f"{msg}\n\n", is_at_all=True)
        print('发送钉钉成功')
    except BaseException as e:
        print('钉钉发送信息出错了, ', str(e))


def send_dingding_msg_for_position(equity, position_df):
    """
    发送持仓信息到钉钉
    """

    dingding_msg = f'账户净值： {equity:8.2f}\n'

    if not position_df.empty:
        dingding_msg += f'当前持仓未实现盈亏: {position_df["持仓盈亏"].sum():8.2f}\n'
        dingding_msg += '策略持仓\n\n'
        for index, row in position_df.reset_index().iterrows():
            dingding_msg += row[['symbol', '当前持仓量', '均价', '持仓盈亏']].to_string()
            dingding_msg += '\n\n'

    send_dingding_msg(dingding_msg)


def send_dingding_msg_for_order(order_param, order_res):
    """
    发送下单信息到钉钉
    """
    dingding_msg = ''
    for _ in range(len(order_param)):
        dingding_msg += f'币种:{order_param[_]["symbol"]}\n'
        dingding_msg += f'方向:{"做多" if order_param[_]["side"] == "BUY" else "做空"}\n'
        dingding_msg += f'价格:{order_param[_]["price"]}\n'
        dingding_msg += f'数量:{order_param[_]["quantity"]}\n'

        if 'msg' in order_res[_].keys():
            dingding_msg += f'下单结果:{order_res[_]["msg"]}'
        else:
            dingding_msg += f'下单结果: 下单成功'

        dingding_msg += '\n' * 2

    send_dingding_msg(dingding_msg)
