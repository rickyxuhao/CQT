"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
from program.Function import *
from program.Config import *
from program.Evaluate import *
from datetime import datetime

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# =====读取数据
all_symbol_data = pd.read_pickle(root_path + '/data/数据整理/all_symbol_data_%s.pkl' % rul_type)
all_symbol_data = filter_events(all_symbol_data, filters)
all_symbol_data = all_symbol_data[abs(all_symbol_data[event]) == 1]  # 只保留选中的事件

# 读取BTC数据用作指数数据：并且会对btc数据的空缺值进行补全。
benchmark_df = import_benchmark_data(candle_path % candle_type + '/BTC-USDT.csv', rul_type, start=date_start,
                                     end=date_end)

# 统计事件的频率
freq_res = frequency_statistics(all_symbol_data, benchmark_df, event)
print(freq_res)

# =====当一个周期有多个币种的时候，按照排序规则，保留指定数量的币种
if rank_factor:
    if symbol_num_limit:
        pct = False if symbol_num_limit > 1 else True
        # 排序方法可以有很多很多：甚至所有的选股策略都可以作为此处的排序方法。
        all_symbol_data['factor_rank'] = all_symbol_data.groupby('candle_begin_time')[rank_factor].rank(method='first',
                                                                                                    ascending=ascending,
                                                                                                    pct=pct)
        all_symbol_data = all_symbol_data[all_symbol_data['factor_rank'] <= symbol_num_limit]
        del all_symbol_data['factor_rank']
# 在symbol中加入交易方向，方便查找问题。例如做多BTC-USDT在处理后就变成了BTC-USDT（1）
all_symbol_data['symbol'] = all_symbol_data[['symbol', event]].apply(lambda x: '%s(%s)' % (x['symbol'], x[event]),
                                                                     axis=1)
# print(all_symbol_data)
# exit()
# 将涨跌幅转为净值，净值 = 涨跌幅 x 交易方向 x 杠杆倍数 +1，除此之外还需要计算一下爆仓
all_symbol_data['未来N周期净值'] = all_symbol_data.apply(lambda x: cal_net_value(x, margin_rate, event, leverage), axis=1)

# =====将一个周期的多个币种，转换到一行中。
all_symbol_data['symbol'] += ' '
group = all_symbol_data.groupby('candle_begin_time')
period_event_df = pd.DataFrame()
period_event_df['币种数量'] = group['symbol'].size()
period_event_df['买入币种'] = group['symbol'].sum()

# =====计算买入当周期所有触发事件币种后的资金曲线
# 每周期资金曲线
period_event_df['持仓每周期净值'] = group['未来N周期净值'].apply(cal_toperiod_symbol_cap_line, hold_period=hold_period, ret_len=30)
# 扣除买入手续费
period_event_df['持仓每周期净值'] = period_event_df['持仓每周期净值'].apply(lambda x: np.array(x) * (1 - c_rate))
# 扣除卖出手续费
period_event_df['持仓每周期净值'] = period_event_df['持仓每周期净值'].apply(lambda x: list(x[:-1]) + [x[-1] * (1 - c_rate)])

# =====创建df来记录持仓信息、资金曲线
df = pd.DataFrame()
df['candle_begin_time'] = sorted(benchmark_df['candle_begin_time'].tolist())[1:]  # 补全后BTC的所有交易日期
df[['总资金', '可用资金', '在投份数']] = None
df['投出资金'] = 0

# 给每份资金创建对应的列
cap_num_cols = []  # 用于循环，记录资金曲线的列
left_period_cols = []  # 用于循环，记录持仓时间的列
for i in range(1, max_cap_num + 1):
    df[['%s_资金' % i, '%s_余数' % i]] = 0
    df['%s_币种' % i] = None
    cap_num_cols.append('%s_资金' % i)
    left_period_cols.append('%s_余数' % i)

# =====每个循环每个周期
start_time = datetime.now()
print('=' * 20, '开始循环每个周期', '=' * 20)
for i in df.index:

    # ===获取当周期的发生的事件
    date = df.at[i, 'candle_begin_time']
    current_period_event = period_event_df[period_event_df.index == date].copy()
    tag = '无事件；' if current_period_event.empty else '有事件；'

    # ===计算当前周期结束投资的资金编号、用于投资的资金编号，
    due_cap_num, next_cap_num, due_cap_num_list = None, None, []  # 当前周期结束投资的资金编号、用于投资的资金编号
    left_period_list = list(df.loc[i, left_period_cols])
    if 0 in left_period_list:  # 如果有可投资资金资金
        next_cap_num = left_period_list.index(0) + 1
        tag += '%d资金待使用；' % next_cap_num
    print(i, date, tag, left_period_list)

    # ===处理第一个周期的特殊情况:
    if i == 0:
        # 如果第一个周期有开仓
        if not current_period_event.empty:
            # 更新资金曲线
            df.loc[i, '投出资金'] = 1
            _df = update_df(current_period_event, start_index=i, cap_num=1, cap=1)
            df.update(_df)
            # 更新当前周期资金
            df.loc[i, '在投份数'] = 1
            df.loc[i, '可用资金'] = float(max_cap_num) - 1
            df.loc[i, '总资金'] = df.loc[i, cap_num_cols + ['可用资金']].sum()
            left_period_list = list(df.loc[i, left_period_cols])  # 记录每份资金的剩余情况
            if 1 in left_period_list:  # 如果有资金到期
                due_cap_num = left_period_list.index(1) + 1  # 第一个周期不可能有>=2份资金到期
                print(i, date, '到期资金份数:', due_cap_num)
            if due_cap_num:  # 如果当周期有到期资金：当周期是最后1个持仓周期
                # 在投份数 = 本周期在投份数 - 1（到期份数）
                df.loc[i, '在投份数'] = df.loc[i, '在投份数'] - 1
                # 可用资金 = 上本周期可用资金 + 本周期到期资金
                df.loc[i, '可用资金'] = df.loc[i, '可用资金'] + df.loc[i, '%s_资金' % due_cap_num]
                # 总资金
                df.loc[i, '总资金'] = df.loc[i, cap_num_cols + ['可用资金']].sum()
                df.loc[i, '总资金'] -= df.loc[i, '%s_资金' % due_cap_num]  # 减去本周期到期资金（重复计算了一次，已经并入了可用资金）
        else:
            # 更新当前周期资金
            df.loc[i, '在投份数'] = 0
            df.loc[i, '总资金'] = float(max_cap_num)
            df.loc[i, '可用资金'] = float(max_cap_num)

    # ===非第一个周期的情况
    if i != 0:
        # 如果有资金开仓
        if (df.loc[i - 1, '在投份数'] < max_cap_num) & (not current_period_event.empty):
            # 计算当前每份投出多少钱 = min(总资金/资金分数，可用资金/可投份数）
            cap1 = df.loc[i - 1, '总资金'] / max_cap_num
            cap2 = df.loc[i - 1, '可用资金'] / (max_cap_num - df.loc[i - 1, '在投份数'])
            cap = min(cap1, cap2)
            df.loc[i, '投出资金'] = cap
            # 更新资金曲线
            update_info = update_df(current_period_event, start_index=i, cap_num=next_cap_num, cap=cap)
            df.update(update_info)

        left_period_list = list(df.loc[i, left_period_cols])  # 记录每份资金的剩余情况
        if 1 in left_period_list:  # 如果有资金到期
            due_cap_num_list = ['%s_资金' % (i + 1) for i, x in enumerate(left_period_list) if x == 1]
            print(i, date, '到期资金份数:', due_cap_num_list)
        # 更新当前周期资金
        if due_cap_num_list:  # 如果当周期有到期资金：当周期是最后1个持仓周期
            # 在投份数 = 上周期在投份数 - 1（到期份数） + 0或1（当周期投出份数）
            # df.loc[i, '在投份数'] = df.loc[i - 1, '在投份数'] - 1 + (df.loc[i, '投出资金'] > 0)
            df.loc[i, '在投份数'] = df.loc[i - 1, '在投份数'] - len(due_cap_num_list) + (df.loc[i, '投出资金'] > 0)
            due_to_money = df.loc[i, due_cap_num_list].sum()
            # 可用资金 = 上周期可用资金 + 本周期到期资金 - 本周期投出资金
            df.loc[i, '可用资金'] = df.loc[i - 1, '可用资金'] + due_to_money - df.loc[i, '投出资金']
            # 总资金
            df.loc[i, '总资金'] = df.loc[i, cap_num_cols + ['可用资金']].sum()
            df.loc[i, '总资金'] -= due_to_money  # 减去本周期到期资金（重复计算了一次，已经并入了可用资金）
        else:  # 如果当周期没有有到期资金
            # 在投份数 = 上周期在投份数 + 0或1（当周期投出份数）
            df.loc[i, '在投份数'] = df.loc[i - 1, '在投份数'] + (df.loc[i, '投出资金'] > 0)
            # 可用资金 = 上周期可用资金 - 本周期投出资金
            df.loc[i, '可用资金'] = df.loc[i - 1, '可用资金'] - df.loc[i, '投出资金']
            # 总资金
            df.loc[i, '总资金'] = df.loc[i, cap_num_cols + ['可用资金']].sum()

print('耗时:', datetime.now() - start_time)

# ===== 评估策略
# 1、评估前的准备
# 计算净值 = 总资金 / 资金分数
df['净值'] = df['总资金'] / max_cap_num
# 计算基准的净值
df['基准净值'] = (benchmark_df['基准涨跌幅'] + 1).cumprod()
# 计算资金使用率 = 每份资金的总额 / 总资金
df['资金使用率'] = (df[cap_num_cols].sum(axis=1) / df['总资金']).apply(float)

# 2、计算资金曲线的各项评估指标(result) & 每年（月、季）的超额收益（excess return）
res, etn = evaluate_investment_for_event_driven(df, period_event_df, date_col='candle_begin_time', rule_type='Q')
print(res)
print(etn)

back_test_path = root_path + '/data/回测结果/回测详情/回测结果_%s_%s_%s_%s_%s.csv' % (
    event, hold_period, max_cap_num, symbol_num_limit, leverage)
df.to_csv(back_test_path, encoding='gbk', index=False)

# 3、绘制资金曲线
pic_title = '事件：%s 持有期：%s 资金份数：%s 选币数:%s' % (event, hold_period, max_cap_num, symbol_num_limit)
# draw_equity_curve_mat(df, date_col='candle_begin_time', data_dict={'策略表现': '净值', 'BTC净值': '基准净值'},
#                       right_axis={'资金使用率': '资金使用率'}, title=pic_title)
# 如果上面的函数不能画图，就用下面的画图
draw_equity_curve_plotly(df, date_col='candle_begin_time', data_dict={'策略表现': '净值', 'BTC净值': '基准净值'},
                         right_axis={'资金使用率': '资金使用率'}, title=pic_title)

# 4、计算资金曲线的盈利（亏损）最大的交易
profit_max, loss_max = get_max_trade(all_symbol_data, df, hold_period, coin_num=10)
print(profit_max)
print(loss_max)
