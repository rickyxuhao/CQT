"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
from joblib import Parallel, delayed
from program.Functions import *
from program.Config import *
from program.Evaluate import *
from program.Filter import *

# 需要回测的因子
factor_list = [
    'Bias', 'Cci'
]

# ===整理数据
df = pd.read_pickle(root_path + f'/data/数据整理/all_coin_factor_data_{hold_period}.pkl')
# 从df中获取已经计算好的所有因子的列名信息
all_factor_column_list = set()
# 遍历因子
for factor_name in factor_list:
    # 遍历df中的列名
    for col in df.columns:
        # df列名中存在该因子，就添加到all_factor_column_list中
        if factor_name in col:
            all_factor_column_list.add(col)

all_factor_column_list = list(all_factor_column_list)

# 确认过滤因子及其参数
filter_list = [
    ('ZhangDieFuAbsMax', [13]),
    ('TakerBuy', [8]),
]
# 构建df中参与过滤的因子信息
filter_column_list = []
for factor_name, parameter_list in filter_list:
    filter_column_list.append(f'{factor_name}_{str(parameter_list)}')

# 删除某些行数据
df = df[~df['symbol'].isin(black_list)]  # 去除黑名单中的币种
df = df[df['volume'] > 0]  # 该周期不交易的币种
df.dropna(subset=['下个周期_avg_price'], inplace=True)  # 最后几行数据，下个周期_avg_price为空
# 筛选日期范围
df = df[df['candle_begin_time'] >= pd.to_datetime(start_date)]
df = df[df['candle_begin_time'] <= pd.to_datetime(end_date)]
# 计算下个周期的收益率
df['ret_next'] = df['下个周期_avg_price'] / df['avg_price'] - 1
df = df[['candle_begin_time', 'symbol', 'ret_next', 'offset'] + list(set(all_factor_column_list + filter_column_list))]
df.sort_values(by=['candle_begin_time', 'symbol'], inplace=True)
df.reset_index(drop=True, inplace=True)
print('数据处理完毕!!!\n')


# 计算单因子的策略评价信息
def cal_factor_rtn(df, factor_para_dict):
    print(factor_para_dict)
    _df = df[['candle_begin_time', 'symbol', 'ret_next', 'offset'] + list(set(list(factor_para_dict.keys()) + filter_column_list))].copy()
    # 删除选币因子或者过滤因子为空的数据
    _df.dropna(subset=list(set(list(factor_para_dict.keys()) + filter_column_list)), inplace=True)
    if _df.empty:
        return

    # ===对因子进行排名
    _df['因子'] = 0
    for key in factor_para_dict.keys():
        _df[key] = _df.groupby('candle_begin_time')[key].apply(lambda x: x.rank(ascending=factor_para_dict[key]))
        _df['因子'] += _df[key] * 1 / len(factor_para_dict.keys())  # 默认等权处理

    # ===前置过滤
    _df = before_filter(_df)

    # ===选币
    select_coin = select_long_and_short_coin(_df, select_coin_num)

    # 过滤可能造成出现当周期不足选出同时做多和做空币种的时候，这里将这些数据过滤掉，当周期内直接空仓
    select_coin['总币数'] = select_coin.groupby('candle_begin_time')['symbol'].transform('size')
    select_coin = select_coin[select_coin['总币数'] >= select_coin_num * 2]  # 去除选币数量不足的数据

    results = []
    # 分别计算每个offset的资金曲线
    for offset, g_df in select_coin.groupby('offset'):
        g_df = g_df.copy()
        equity = cal_equity(g_df, c_rate, select_coin_num)
        equity['资金曲线'] = (equity['本周期多空涨跌幅'] + 1).cumprod()
        equity.loc[equity['资金曲线'] < margin_rate, '是否爆仓'] = 1
        equity['是否爆仓'].fillna(method='ffill', inplace=True)
        equity.loc[equity['是否爆仓'] == 1, '资金曲线'] = 0

        # 策略评价
        rtn = strategy_evaluate(equity).T

        # 增加新的字段
        rtn.loc[0, 'offset'] = offset
        rtn.loc[0, '因子组合'] = str(factor_para_dict)
        results.append(rtn)
    return results


# 构建几个因子的组合方式(数字越大，越耗时)
factor_count = 1

# 通过itertools.combinations构建因子的排列组合
factors = list(itertools.combinations(all_factor_column_list, factor_count))

# 通过itertools.product构建True，False的全组合
reverses = list(itertools.product([True, False], repeat=factor_count))

# 循环遍历因子组合和排序组合，构建完整的回测因子组合(多参数目前默认全是等权)
factor_para_list = []
for f in factors:  # 遍历排列组合后的因子列表
    for r in reverses:  # 遍历排序组合列表
        factor_dict = {}  # 存储因子信息
        _col = []  # 临时变量，用来去除单因子自己与自己的组合
        for i in range(0, factor_count):
            factor_dict[f[i]] = r[i]
            _col.append(f[i].split('_')[0])  # 将因子信息添加到col中
        # 去除单因子自己与自己的组合
        if len(set(_col)) < factor_count:
            continue
        factor_para_list.append(factor_dict)

print('遍历因子组合数量:', len(factor_para_list))

# 并行的计算所有的因子评价信息
all_data_list = Parallel(n_jobs=max(os.cpu_count() - 1, 1))(
    delayed(cal_factor_rtn)(df, factor_para)
    for factor_para in factor_para_list
)

# 将所有因子的评价信息，从二维数组转成一维数组，方便后续concat操作
rtn_list = []
for rows in all_data_list:
    for row in rows:
        rtn_list.append(row)

# 数据合并
rtn_df = pd.concat(rtn_list, ignore_index=True)
# 整理一下字段
rtn_df = rtn_df[['offset', '因子组合', '累积净值', '年化收益', '最大回撤', '胜率', '盈亏收益比', '最大连续盈利周期数', '最大连续亏损周期数',
                 '最大回撤开始时间', '最大回撤结束时间', '年化收益/回撤比']]
rtn_df.sort_values(by=['年化收益/回撤比'], inplace=True, ascending=False)
rtn_df.reset_index(drop=True, inplace=True)
rtn_df.to_csv(root_path + f'/data/rtn_{hold_period}.csv', encoding='gbk', index=False)
print(rtn_df)
