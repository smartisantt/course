"""
微信支付API
author:York
time:2019-10-25
"""

import hashlib
import logging
import time
import requests
from bs4 import BeautifulSoup
from random import Random

# 微信公众号、商户平台基础配置
from common.models import PayLog
from parentscourse_server.config import HOST_URL, WEBAPPID

APPID = WEBAPPID
APIKEY = '1e5ddecea41cf3c8d86e609c1299dd81'
create_ip = '192.168.100.235'
MCHID = '1547729361'


def random_str(randomlength=8):
    """
    生成随机字符串
    :param randomlength: 字符串长度
    :return:
    """
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def craete_out_trade_no():
    """
    创建微信商户订单号
    :return:
    """
    local_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    result = 'wx{}'.format(local_time[2:])
    return result


def get_sign(data_dict, key):
    # 签名函数，参数为签名的数据和密钥
    params_list = sorted(data_dict.items(), key=lambda e: e[0], reverse=False)  # 参数字典倒排序为列表
    params_str = "&".join(u"{}={}".format(k, v) for k, v in params_list) + '&key=' + key
    # 组织参数字符串并在末尾添加商户交易密钥
    md5 = hashlib.md5()  # 使用MD5加密模式
    md5.update(params_str.encode('utf-8'))  # 将参数字符串传入
    sign = md5.hexdigest().upper()  # 完成加密并转为大写
    return sign


def trans_dict_to_xml(data_dict):  # 定义字典转XML的函数
    data_xml = []
    for k in sorted(data_dict.keys()):  # 遍历字典排序后的key
        v = data_dict.get(k)  # 取出字典中key对应的value
        if k == 'detail' and not v.startswith('<![CDATA['):  # 添加XML标记
            v = '<![CDATA[{}]]>'.format(v)
        data_xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(data_xml)).encode('utf-8')  # 返回XML，并转成utf-8，解决中文的问题


def trans_xml_to_dict(data_xml):
    soup = BeautifulSoup(data_xml, features='html.parser')
    xml = soup.find('xml')  # 解析XML
    if not xml:
        return {}
    data_dict = dict([(item.name, item.text) for item in xml.find_all()])
    return data_dict


def wx_pay_unifiedorde(detail,request):
    """
    访问微信支付统一下单接口
    :param detail:
    :return:
    """
    detail['sign'] = get_sign(detail, APIKEY)
    detail['userUuid'] = request.user.get("userObj")
    try:
        PayLog.objects.create(**detail)
        detail.pop("userUuid")
    except Exception as e:
        logging.error(str(e))
    xml = trans_dict_to_xml(detail)
    response = requests.request('post', 'https://api.mch.weixin.qq.com/pay/unifiedorder',
                                data=xml)
    return response.content


def hbb_wx_pay_params(data_dict, request):
    """
    从公众号端获取微信的Jsapi支付需要的参数
    :param openid:微信公众号用户的openid
    :param total_fee:支付金额
    :param pay_type: 支付类型
    :return:
    """

    params = {
        "appid": APPID,
        "mch_id": MCHID,
        "nonce_str": random_str(),
        "sign_type": "MD5",
        "body": '商品描述：{0}'.format(data_dict.get("body")),
        "out_trade_no": data_dict.get("orderNo"),
        "fee_type": "CNY",
        "total_fee": data_dict.get("price"),
        "spbill_create_ip": data_dict.get("userIP"),
        "goods_tag": "好呗呗优惠券",  # 优惠标记
        "notify_url": '{0}/api/common/wxpayresult/'.format(HOST_URL),  # 回调地址
        "trade_type": "JSAPI",
        "product_id": data_dict.get("goodsID"),
        "openid": data_dict.get("openid"),
        "device_info": data_dict.get("device_info")
    }

    # 调用微信统一下单支付接口url
    notify_result = wx_pay_unifiedorde(params, request)
    notify_result = trans_xml_to_dict(notify_result)
    # print('向微信请求', notify_result)
    if 'return_code' in notify_result and notify_result['return_code'] == 'FAIL':
        return False
    if 'prepay_id' not in notify_result:
        return False
    params['prepay_id'] = notify_result['prepay_id']
    params['timeStamp'] = int(time.time())
    params['nonceStr'] = random_str(16)
    params['sign'] = get_sign({'appId': APPID,
                               "timeStamp": params['timeStamp'],
                               'nonceStr': params['nonceStr'],
                               'package': 'prepay_id=' + params['prepay_id'],
                               'signType': 'MD5',
                               },
                              APIKEY)

    ret_params = {
        'package': "prepay_id=" + params['prepay_id'],
        'appid': APPID,
        'timeStamp': str(params['timeStamp']),
        'nonceStr': params['nonceStr'],
        'sign': params['sign'],
    }

    return ret_params


def wx_pay_orderquery(detail):
    """
    微信订单支付结果查询
    :param detail:
    :return:
    """
    detail['sign'] = get_sign(detail, APIKEY)
    xml = trans_dict_to_xml(detail)
    response = requests.request('post', 'https://api.mch.weixin.qq.com/pay/orderquery',
                                data=xml)
    return response.content


def hbb_wx_pay_query(orderNO):
    """
    支付结果主动查询
    :param data_dict:
    :return:
    """
    params = {
        "appid": APPID,
        "mch_id": MCHID,
        "out_trade_no": orderNO,
        "nonce_str": random_str(),
        "sign_type": "MD5",
    }
    notify_result = wx_pay_orderquery(params)
    notify_result = trans_xml_to_dict(notify_result)
    if 'return_code' not in notify_result and notify_result['return_code'] != 'SUCCESS':
        return False
    if "trade_state" in notify_result:
        return notify_result
    return False


if __name__ == "__main__":
    dataInfo = {
        "body": "这里是课程介绍",
        "orderNo": "13546879484654185",
        "price": 1,
        "userIP": "192.168.100.199",
        "goodsID": "adfad1654erg521vad5415asd",
        "openid": "oXmFf0qWpaoyYyiNURA90JK-bSKc"
    }
    print(hbb_wx_pay_params(dataInfo))
