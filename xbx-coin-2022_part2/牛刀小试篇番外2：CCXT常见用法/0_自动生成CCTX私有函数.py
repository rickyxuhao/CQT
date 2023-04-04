"""
《邢不行-2022新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx9025
本程序作者: 邢不行

# 课程内容
查找CCXT私有函数
"""
import ccxt


def get_all_api(exchange):
    """
    获取CCXT的所有私有函数
    :param exchange: 实例化后的交易所变量
    :return:
    """
    _api_path_list = []
    all_api_dict = exchange.describe()['api']
    for first_k, first_v in all_api_dict.items():
        if isinstance(first_v, dict):
            for second_k, second_v in first_v.items():
                if second_k in ['get', 'post', 'put', 'delete'] and isinstance(second_v, dict):
                    for third_k, third_v in second_v.items():
                        last_path = ''.join([i[0].upper() + i[1:] for i in third_k.split('/')])
                        last_path = ''.join([i[0].upper() + i[1:] for i in last_path.split('-')])
                        _api_path = first_k + second_k[0].upper() + second_k[1:] + last_path
                        _api_path_list.append(_api_path)
    return _api_path_list


def get_private_functions(_api_word, _api_path_list):
    """
    根据API信息，获取私有函数
    :param _api_word:API接口信息（例子：GET /api/v5/public/price-limit）
    :param _api_path_list:所有私有函数合集
    :return:
    """
    method = _api_word.split()[0]
    api_name = _api_word.split()[1]
    api_type = api_name.split('/')[1] if 'api' in api_name else ''

    res_list = []
    for api_path in _api_path_list:
        last_api_path = ''.join([i[0].upper() + i[1:] for i in api_name.split('/')[-1:]])
        last_api_path = ''.join([i[0].upper() + i[1:] for i in last_api_path.split('-')])
        if api_path.endswith(last_api_path) and method.capitalize() in api_path:
            if (api_type == 'api') and ('api' not in api_path):
                res_list.append(api_path)
            elif (api_type != 'api') and (api_path.startswith(api_type)):
                res_list.append(api_path)
    print(res_list)


if __name__ == '__main__':
    exchange = ccxt.binance()
    api_path_list = get_all_api(exchange)
    while True:
        api_word = input('请输入API接口信息（例子：GET /api/v5/public/price-limit）：')
        get_private_functions(api_word, api_path_list)
