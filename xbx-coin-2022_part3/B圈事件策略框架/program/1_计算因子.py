"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
from datetime import datetime
from multiprocessing import cpu_count
from joblib import Parallel, delayed
from program.Function import *
from program.Config import *


pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


def cal_factor(symbol, benchmark_df, rul_type, parameters_list, cls):
    """
    处理单个币种
    :param symbol:
    :param benchmark_df:
    :param rul_type:
    :param parameters_list:
    :param cls:
    :return:
    """
    print(symbol)

    # 读取这个币种的基础K线数据
    candle_df = pd.read_csv(candle_path % candle_type + symbol, encoding='gbk', parse_dates=['candle_begin_time'],
                            skiprows=1)
    agg_dict = {'symbol': 'first', 'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'quote_volume': 'sum',
                '是否交易': 'first'}  # 为之后的周期转换做好准备

    # 将K线数据和基准数据合并，填充没有交易的数据
    candle_df = merge_with_benchmark(candle_df, benchmark_df)

    # 有的因子的计算需要外部数据，导入计算该因子需要的其他额外数据。
    candle_df, agg_dict = getattr(cls, 'special_data')(candle_df, symbol, agg_dict)

    # 转换数据的周期
    df = candle_df.resample(rul_type, on='candle_begin_time').agg(agg_dict)
    df.reset_index(inplace=True, drop=False)

    # 如果数据为空，返回空值
    if df.empty:
        return pd.DataFrame()

    # 逐个参数计算因子
    for para in parameters_list:
        df = getattr(cls, 'calculate')(df, para)

    return df


if __name__ == '__main__':

    # 计算的因子的名称
    factor = 'Ma'
    print('开始计算因子：', factor)

    # __import__ 动态导入模块。详情请见：https://www.runoob.com/python/python-func-__import__.html
    cls = __import__('factor.%s' % factor, fromlist=('',))  # fromlist如果为空，导入的是factors包，所以需要给factors传入参数

    # 读取BTC一小时的数据，并且会BTC数据的空缺值进行补全。将这个数据当做指数数据
    benchmark = import_benchmark_data(candle_path % candle_type + '/BTC-USDT.csv',
                                      rul_type='1H', start='2009-01-01', end=date_end)

    # 读取所有币种的名称
    symbol_list = os.listdir(candle_path % candle_type)
    symbol_list = [s for s in symbol_list if '.csv' in s]  # 只读取包含.csv的文件，避免文件夹下有其他文件干扰
    # symbol_list = symbol_list[:10]  # 测试的时候可以只取10个

    # =====开始计算因子
    start_time = datetime.now()  # 标记开始计算的时间

    # 获取遍历因子的参数
    parameters_list = getattr(cls, 'batch_parameters')()  # 调用函数

    # 开始并行或者串行计算每个币种的因子
    multi_process = True
    if multi_process:  # 并行
        df_list = Parallel(n_jobs=cpu_count() - 1)(
            delayed(cal_factor)(code, benchmark, rul_type, parameters_list, cls) for code in symbol_list)
    else:  # 串行
        df_list = []
        for symbol_code in symbol_list:
            data = cal_factor(symbol_code, benchmark, rul_type, parameters_list, cls)
            df_list.append(data)

    print('计算完成, 开始合并。计算花费时间：', datetime.now() - start_time)  # 标记结束计算的时间

    # 把所有计算完成后的数据进行合并并重置索引
    all_symbol_data = pd.concat(df_list, ignore_index=True)

    # 逐个参数计算截面因子数据
    for parameters in parameters_list:
        all_symbol_data = getattr(cls, 'cross_section_calculate')(all_symbol_data, parameters, candle_type=candle_type)

    # =====因子计算完成
    all_symbol_data.sort_values(['candle_begin_time', 'symbol'], inplace=True)  # 因子排序
    all_symbol_data.reset_index(inplace=True, drop=True)
    print(all_symbol_data)
    # 定义因子保存的路径   #####修改：这些写成函数放到function里面
    path = root_path + '/data/数据整理/因子数据/'
    # 避免因子文件夹不存在，先判断一下，如果不存在则创建
    path = os.path.join(path, factor)  # 拼接路径， 比如我们现在计算的因子为Ma，经过这一步拼接后的路径为：root_path + '/data/数据整理/因子数据/Ma'
    if not os.path.exists(path):  # 判断文件夹是否存在
        os.mkdir(path)  # 不存在则创建
    path = os.path.join(path, rul_type)  # 拼接路径，比如我们现在计算的因子为Ma，周期为8H，拼接后的结果为：root_path + '/data/数据整理/因子数据/Ma/8H'
    if not os.path.exists(path):  # 判断文件夹是否存在
        os.mkdir(path)  # 不存在则创建

    # 逐个保存因子列数据
    for c in set([column for column in all_symbol_data.columns if cls.factor_name in column]):
        # 判断周期文件是否存在
        all_symbol_data[[c]].to_pickle(os.path.join(path, '%s_%s_%s.pkl' % (c, rul_type, candle_type)))

    # 保存base数据（在每次计算因子的时候都会重新计算一遍，会重复）
    head_columns = ['candle_begin_time', 'symbol', 'open', 'high', 'low', 'close', 'quote_volume',
                    '是否交易']  # 定义base数据需要的列
    all_symbol_data[head_columns].to_pickle(root_path + '/data/数据整理/因子数据/base_%s_%s.pkl' % (rul_type, candle_type))
