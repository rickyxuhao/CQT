"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx6660
"""
from glob import glob
from joblib import Parallel, delayed
from program.Config import *
from program.Functions import *
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
import warnings
warnings.filterwarnings("ignore")


def calc_factors(file_path):
    print(file_path)
    # ===读取数据文件
    df = pd.read_csv(file_path, encoding='gbk', skiprows=1, parse_dates=['candle_begin_time'])

    # ===处理数据
    df.sort_values(by='candle_begin_time', inplace=True)
    df.drop_duplicates(subset=['candle_begin_time'], inplace=True, keep='last')
    df['avg_price'] = df['avg_price_1m']  # 使用1m均价作为开仓均价。你资金量大的话，也可以使用5m均价
    df['avg_price'].fillna(value=df['open'], inplace=True)  # 若1分钟均价空缺，使用open填充
    df['下个周期_avg_price'] = df['avg_price'].shift(-1)  # 用于后面计算当周期涨跌幅
    df.reset_index(drop=True, inplace=True)

    # ===计算选币因子
    df, factor_column_list = calc_factors_for_filename(df, factor_class_list, filename='factors')

    # ===计算过滤因子
    df, filters_column_list = calc_factors_for_filename(df, filter_class_list, filename='filters')

    # 币种的前N根K线删除
    df = df[min_kline_num:]
    if df.empty:
        return pd.DataFrame()

    # ===进行周期转换
    exg_dict = {'avg_price': 'first', '下个周期_avg_price': 'last'}
    # 对每个因子设置转换规则
    for f in factor_column_list + filters_column_list:
        exg_dict[f] = 'first'
    # 开始周期转换
    df = trans_period_for_period(df, hold_period, exg_dict)

    # 返回整理后的数据
    return df


if __name__ == '__main__':
    # 获取所有文件路径
    symbol_file_path = glob(kline_path + '*USDT.csv')  # 获取kline_path路径下，所有以usdt.csv结尾的文件路径

    # 并行或串行处理数据
    multiply_process = False  # 在测试的时候可以改成False
    if multiply_process:
        df_list = Parallel(n_jobs=max(os.cpu_count() - 1, 1))(
            delayed(calc_factors)(file_path)
            for file_path in symbol_file_path
        )
    else:
        df_list = []
        for file_path in symbol_file_path:
            df_list.append(calc_factors(file_path))

    # 合并数据
    all_coin_data = pd.concat(df_list, ignore_index=True)

    # 输出数据
    print(all_coin_data)
    all_coin_data.to_pickle(root_path + f'/data/数据整理/all_coin_factor_data_{hold_period}.pkl')
