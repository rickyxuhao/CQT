"""
2022  B圈新版课程 | 邢不行
author: 邢不行
微信: xbx9585
"""
import pandas as pd
from tqdm import tqdm
from program.Config import *
from program.Function import read_factor

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


if __name__ == '__main__':
    # 需要运行的事件策略
    event_strategy = 'MaCross'

    # 导入计算事件策略需要的模块。__import__ 动态导入模块。详情请见：https://www.runoob.com/python/python-func-__import__.html
    _cls = __import__('strategy.%s' % event_strategy, fromlist=('',))  # fromlist如果为空，导入的是factors包，所以需要给factors传入参数

    # 读取所有币种的基础K线数据
    df = pd.read_pickle(root_path + '/data/数据整理/因子数据/base_%s_%s.pkl' % (rul_type, candle_type))

    # 读取因子数据
    df = read_factor(df, _cls.factors)

    # ===计算事件
    # 获取事件的计算参数
    parameters_list = getattr(_cls, 'batch_parameters')()
    # 遍历参数
    for parameters in tqdm(parameters_list):
        # 计算事件
        df = getattr(_cls, 'event_strategy')(df, parameters)

    # 只保留事件列
    event_cols = [col for col in df.columns if _cls.strategy_name in col]
    df = df[['candle_begin_time', 'symbol'] + event_cols]
    df.rename(columns={'candle_begin_time': '事件日期'}, inplace=True)  # 重命名列名

    # 对数据进行整理
    df.sort_values(by=['事件日期', 'symbol'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    # 保存文件
    df.to_pickle(root_path + '/data/事件策略event合集/%s.pkl' % _cls.strategy_name)
    print(df)
