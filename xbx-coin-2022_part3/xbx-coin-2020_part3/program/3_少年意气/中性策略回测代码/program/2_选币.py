"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
from program.Functions import *
from program.Evaluate import *
from program.Filter import *


# ===策略参数的确认
# 确认offset
offset = 0
# 确认选币因子及其参数
factor_list = [
    ('Cci_v3', False, [55], 0.5),
    ('Volume', True, [3], 0.5),
]
# 构建df中参与选币的因子信息
factor_column_list = []
for factor_name, if_reverse, parameter_list, weight in factor_list:
    factor_column_list.append(f'{factor_name}_{str(parameter_list)}')

# 确认过滤因子及其参数
filter_list = [
    ('ZhangDieFuAbsMax', [13]),
    ('TakerBuy', [8]),
    ('Volume', [55])
]
# 构建df中参与过滤的因子信息
filter_column_list = []
for factor_name, parameter_list in filter_list:
    filter_column_list.append(f'{factor_name}_{str(parameter_list)}')

# 后续计算需要保留的字段信息
factor_filter_column_list = list(set(factor_column_list + filter_column_list))

# ===读取并整理数据
# 读取数据
df = pd.read_pickle(root_path + f'/data/数据整理/all_coin_factor_data_{hold_period}.pkl')
# 删除某些数据
df = df[df['offset'] == offset]  # 选取指定的offset
df = df[~df['symbol'].isin(black_list)]  # 去除黑名单中的币种
df = df[df['volume'] > 0]  # 该周期不交易的币种
df.dropna(subset=['下个周期_avg_price'], inplace=True)  # 最后几行数据，下个周期_avg_price为空
# 筛选日期范围
df = df[df['candle_begin_time'] >= pd.to_datetime(start_date)]
df = df[df['candle_begin_time'] <= pd.to_datetime(end_date)]
# 计算下个周期的收益率
df['ret_next'] = df['下个周期_avg_price'] / df['avg_price'] - 1
# 保留指定字段，减少计算时间
df = df[['candle_begin_time', 'symbol', 'ret_next'] + factor_filter_column_list]
# 删除选币因子或过滤因子为空的数据。所以前面的计算得保证因子数据不能为空。
df.dropna(subset=factor_filter_column_list, inplace=True)  # 任意因子数据为空，删除整行数据
# 排序
df.sort_values(by=['candle_begin_time', 'symbol'], inplace=True)
df.reset_index(drop=True, inplace=True)
print('数据处理完毕!!!')
print(df.head(10))

# ===计算因子组合，并且进行排名。和实盘代码一模一样。
df['因子'] = 0
for factor_name, if_reverse, parameter_list, weight in factor_list:
    col_name = f'{factor_name}_{str(parameter_list)}'
    # 计算单个因子的排名
    df[col_name] = df.groupby('candle_begin_time')[col_name].rank(ascending=if_reverse)
    # 将因子按照权重累加
    df['因子'] += (df[col_name] * weight)
df = df[['candle_begin_time', 'symbol', 'ret_next', '因子'] + filter_column_list]  # 只保留需要的字段

# ===过滤
# df = before_filter(df)

# ===选币
select_coin = select_long_and_short_coin(df, select_coin_num)

# 过滤可能造成出现当周期不足选出同时做多和做空币种的时候，这里将这些数据过滤掉，当周期内直接空仓
select_coin['总币数'] = select_coin.groupby('candle_begin_time')['symbol'].transform('nunique')
select_coin = select_coin[select_coin['总币数'] >= select_coin_num * 2]  # 去除选币数量不足的数据

# 保留指定字段
select_coin = select_coin[['candle_begin_time', 'symbol', 'ret_next', '方向']]
select_coin.sort_values(by='candle_begin_time', inplace=True)
select_coin.reset_index(drop=True, inplace=True)
print('选币处理完毕!!!')
print(select_coin.head(6))

# ===计算资金曲线
equity = cal_equity(select_coin, c_rate, select_coin_num)
equity['资金曲线'] = (equity['本周期多空涨跌幅'] + 1).cumprod()
equity.loc[equity['资金曲线'] < margin_rate, '是否爆仓'] = 1
equity['是否爆仓'].fillna(method='ffill', inplace=True)
equity.loc[equity['是否爆仓'] == 1, '资金曲线'] = 0

# ===策略评价
rtn = strategy_evaluate(equity)
print(rtn)

# ===画图
draw_equity_curve_mat(equity, data_dict={'策略资金曲线': '资金曲线'}, date_col='candle_begin_time')
# 如果上面的函数不能画图，就用下面的画图
# draw_equity_curve_plotly(equity, data_dict={'策略资金曲线': '资金曲线'}, date_col='candle_begin_time')
