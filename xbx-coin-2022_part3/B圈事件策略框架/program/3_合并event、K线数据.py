"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
from datetime import datetime
from multiprocessing import cpu_count
from joblib import Parallel, delayed
from program.Config import *
from program.Function import *

N_period = 30  # 记录未来N个周期的收益率
indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=N_period)  # 反向rolling申明变量

# ===读取相关数据
# 读取需要计算事件的数据
event_df = pd.read_pickle(root_path + '/data/事件策略event合集/%s.pkl' % event.split('_')[0])
print(event_df)
# 获取所有的事件列
event_list = [column for column in event_df.columns if event.split('_')[0] in column]
print(event_df.head(5))

# 事件相关的币种
symbol_list = sorted(event_df['symbol'].drop_duplicates().to_list())

# symbol_list = symbol_list[:10]
# 读取BTC数据用作指数数据：并且会对btc数据的空缺值进行补全。
benchmark_df = import_benchmark_data(candle_path % candle_type + '/BTC-USDT.csv', rul_type, start=date_start,
                                     end=date_end)


# ===处理单个币种
def cal_with_symbol(code):
    print(code)
    # 读取K线数据
    df = pd.read_csv(candle_path % candle_type + '%s.csv' % code, encoding='gbk', parse_dates=['candle_begin_time'],
                     skiprows=1)

    agg_dict = {'symbol': 'first', 'open': 'first', 'high': 'max', 'low': 'min',
                'close': 'last', 'quote_volume': 'sum', }
    df = df.resample(rul_type, on='candle_begin_time').agg(agg_dict)
    df.reset_index(inplace=True, drop=False)

    # 计算涨跌幅
    df['涨跌幅'] = df['close'].pct_change()
    df.loc[df['涨跌幅'].isna(), '涨跌幅'] = df['close'] / df['open'] - 1
    df['开盘买入涨跌幅'] = df['close'] / df['open'] - 1  # 为之后开盘买入做好准备
    # 和基准数据合并
    df = merge_with_benchmark(df, benchmark_df)
    if df.shape[0] < N_period:
        return pd.DataFrame()

    # ==============================计算事件策略相关代码==============================
    # 读取本币种的事件
    event_data = event_df[event_df['symbol'] == code].copy()
    del event_data['symbol']

    # 将事件数据和K线数据合并
    df = pd.merge(left=event_data, right=df, left_on=['事件日期'], right_on=['candle_begin_time'], how='right')

    # 实际持仓要晚一个周期
    for event in event_list:
        df[event] = df[event].shift()
    df['事件日期'] = df['事件日期'].shift()

    # ==============================计算事件策略相关代码==============================
    # 计算每周期未来N周期的涨跌幅（包含当周期）
    df['未来N周期涨跌幅'] = [window.to_list() for window in df['涨跌幅'].rolling(window=indexer, min_periods=1)]
    # 把第一个周期的涨跌幅改成开盘买入涨跌幅
    df['开盘买入涨跌幅'] = df['开盘买入涨跌幅'].apply(lambda x: [x])
    df['未来N周期涨跌幅'] = df['未来N周期涨跌幅'].apply(lambda x: x[1:])
    df['未来N周期涨跌幅'] = df['开盘买入涨跌幅'] + df['未来N周期涨跌幅']

    # 某些事件虽然发生，但是当前周期无法买入，所以将该事件强行从1设置为0
    ''''
    比如一个币种从22年1月3日的8点到22年1月8日的23点无法交易,就需要把这些信号去除掉
    '''
    for event in event_list:
        # 删除一些有信号但实际无法买入的
        df.loc[df['是否交易'] != 1, event] = 0

    # 只保留发生事件的日期
    df = df[df['事件日期'].notna()]

    # 只保留需要的列，要不然数据会很大
    col = ['candle_begin_time', '事件日期', 'symbol', '开盘买入涨跌幅', '未来N周期涨跌幅'] + event_list
    df = df[col]
    # print(df)
    # exit()

    return df


if __name__ == '__main__':

    # cal_with_symbol('ETHDOWN-USDT')
    # 并行或串行计算所有币种
    start_time = datetime.now()  # 标记开始时间
    multiply_process = True
    if multiply_process:
        df_list = Parallel(n_jobs=max(cpu_count() - 1, 1))(
            delayed(cal_with_symbol)(symbol_code) for symbol_code
            in symbol_list)
    else:
        df_list = []
        for symbol_code in symbol_list:
            data = cal_with_symbol(symbol_code)
            df_list.append(data)

    print('读入完成, 开始合并', datetime.now() - start_time)
    all_symbol_data = pd.concat(df_list, ignore_index=True)

    # ===将数据存入数据库之前，先排序、reset_index
    all_symbol_data.sort_values(['candle_begin_time', 'symbol'], inplace=True)
    if rank_factor:  # 如果有排序因子，则加载排序因子
        all_symbol_data = load_rank_factor(all_symbol_data, rank_factor.split('_')[0])
    print(all_symbol_data.sample(5))
    all_symbol_data.to_pickle(root_path + '/data/数据整理/all_symbol_data_%s.pkl' % rul_type)
    print('运行完成:', datetime.now() - start_time)
