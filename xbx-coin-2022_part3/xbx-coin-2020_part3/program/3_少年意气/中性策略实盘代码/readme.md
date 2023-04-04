# 中性实盘操作指南

## 0. 购买服务器
推荐阿里云轻量云服务器
https://swas.console.aliyun.com/#/servers

选择"新加坡节点"或"香港节点"

推荐配置2G2C 40G SSD

## 1. 设置合约持仓方式
https://www.binance.com/zh-CN/futures/BTCUSDT

![image-20221010124208344](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2022-10-10-044208.png)

偏好设置为单向持仓
![image-20221010124305699](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2022-10-10-044306.png)

## 2. 创建api key
https://www.binance.com/zh-CN/my/settings/api-management
![image-20221010124740972](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2022-10-10-044741.png)
设置好交易权限，并绑定服务器ip
![image-20221010125310903](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2022-10-10-045311.png)


## 3. 配置实盘代码
config.py
```python
apiKey = "xxx"
secret = "xxx"
```
配置策略
```python
# ===策略配置
stratagy_list = {
    "factor_name": "c_factor1",  
    "hold_period": "6H",
    "factors": [
        ('Bias', False, [30], 0.5),
        ('Cci', False, [36], 0.5)
    ],
    "select_coin_num":   1,
}
```

## 4. 配置实盘环境
```python
conda create -n py38trading python=3.8

conda activate py38trading

pip install -r requirements.txt

```

## 5. 运行实盘代码
运行实盘启动脚本：startup.py
```python
python startup.py
```


