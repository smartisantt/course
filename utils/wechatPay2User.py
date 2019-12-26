
import hashlib
import time
import requests
from bs4 import BeautifulSoup
from random import Random

# 微信公众号、商户平台基础配置
from parentscourse_server.config import version

APPID = "wx233ca74b3d313293"                            # 商户账号appid
APIKEY = '1e5ddecea41cf3c8d86e609c1299dd81'             # 商户key
create_ip = '192.168.100.235'
# MCHID = '1532139641'                                  #
MCHID = '1547729361'                                    # 商户号


if version == "debug":
    api_client_cert_path = "D:/soft/apiclient/apiclient_cert.pem"
    api_client_key_path = "D:/soft/apiclient/apiclient_key.pem"
    amount = 30
elif version == "test":
    api_client_cert_path = "/usr/local/share/ca-certificates/apiclient_cert.pem"
    api_client_key_path = "/usr/local/share/ca-certificates/apiclient_key.pem"
    amount = 30
elif version == "ali_test":
    api_client_cert_path = ""   # 正式环境提现需要配置证书，微信后台配置需要添加api的ip
    api_client_key_path = ""
    amount = 0                  # 正式环境提现金额为真实退款金额，测试提现金额为0.3元


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
        # if k == 'detail' and not v.startswith('<![CDATA['):  # 添加XML标记
        #     v = '<![CDATA[{}]]>'.format(v)
        data_xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(data_xml)).encode('utf-8')  # 返回XML，并转成utf-8，解决中文的问题


def trans_xml_to_dict(data_xml):
    soup = BeautifulSoup(data_xml, features='html.parser')
    xml = soup.find('xml')  # 解析XML
    if not xml:
        return {}
    data_dict = dict([(item.name, item.text) for item in xml.find_all()])
    return data_dict


def wx_pay_to_user(detail):
    """企业付款"""
    url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"
    detail['sign'] = get_sign(detail, APIKEY)
    xml = trans_dict_to_xml(detail)
    response = requests.request('post', url, data=xml, cert=(api_client_cert_path, api_client_key_path))
    return response.content


def wx_refund_to_user(detail):
    """退款"""
    url = "https://api.mch.weixin.qq.com/secapi/pay/refund"
    detail['sign'] = get_sign(detail, APIKEY)
    xml = trans_dict_to_xml(detail)
    response = requests.request('post', url, data=xml, cert=(api_client_cert_path, api_client_key_path))
    return response.content


def enterprise_payment_to_wallet(data_dict):
    """企业微信付款给用户"""

    params = {
        "mch_appid": APPID,
        "mchid": MCHID,
        "device_info": data_dict.get("device_info", "WEB"),
        "nonce_str": random_str(),
        "partner_trade_no":  data_dict.get("partner_trade_no", "WEB"),
        "openid": data_dict.get("openid"),
        "check_name": "NO_CHECK",
        # "re_user_name": "name",                                #
        "amount": amount or data_dict.get("amount"),             # 调试的时候退款默认是1分钱
        "desc": data_dict.get("desc"),
        "spbill_create_ip": data_dict.get("spbill_create_ip")
    }

    # 调用微信企业付款接口
    notify_result = wx_pay_to_user(params)
    # 返回解析后的结果
    notify_result = trans_xml_to_dict(notify_result)
    # print(notify_result)
    # print('向微信请求', notify_result)
    if "return_code" not in notify_result:
        return False, "企业微信付款给用户出错"

    if 'return_code' in notify_result and notify_result['return_code'] == 'FAIL':
        return False, notify_result['return_msg']
    if 'partner_trade_no' not in notify_result:
        return False, notify_result['err_code_des']
    # 以下字段在return_code 和result_code都为SUCCESS的时候有返回
    res = dict()
    res['partner_trade_no'] = notify_result['partner_trade_no']      # 商户订单号
    res['payment_time'] = notify_result['payment_time']              # 微信付款单号
    res['payment_no'] = notify_result['payment_no']                  # 付款成功时间 2015-05-19 15：26：59
    # print(res)
    return True, res


def wx_refund_query(detail):
    """微信退款结果查询"""
    detail['sign'] = get_sign(detail, APIKEY)
    xml = trans_dict_to_xml(detail)
    response = requests.request('post', 'https://api.mch.weixin.qq.com/pay/refundquery',
                                data=xml,  cert=(api_client_cert_path, api_client_key_path))
    return response.content


def hbb_wx_refund_query(orderNO):
    """退款结果主动查询"""
    params = {
        "appid": APPID,
        "mch_id": MCHID,
        "out_refund_no": orderNO,
        "nonce_str": random_str(),
    }
    notify_result = wx_refund_query(params)
    notify_result = trans_xml_to_dict(notify_result)
    if 'result_code' not in notify_result:
        return False, "查询出错"
    if "result_code" in notify_result and notify_result['result_code'] == 'FAIL':
        return False, notify_result['return_msg']
    if "result_code" in notify_result and notify_result['result_code'] == 'SUCCESS':
        return True, notify_result



def wx_refund(data_dict):
    """
    申请退款
    """
    params = {
        "appid": APPID,
        "mch_id": MCHID,
        "out_trade_no": data_dict.get("orderNo"),                   # 我们生成的订单编号，用这个编号去查询
        "nonce_str": random_str(),
        "sign_type": "MD5",
        "out_refund_no": data_dict.get("out_refund_no"),            # 商户系统内部的退款单号，商户系统内部唯一
        "total_fee": data_dict.get("total_fee"),                    # 订单总金额，单位为分
        "refund_fee": data_dict.get("refund_fee"),                  # 退款总金额，订单总金额，单位为分，只能为整数
        "refund_desc": data_dict.get("refund_desc", "好呗呗退款")    # 退款原因
    }

    notify_result = wx_refund_to_user(params)
    # 返回解析后的结果
    notify_result = trans_xml_to_dict(notify_result)

    if 'result_code' not in notify_result:
        return False, "微信退款出错"
    if "result_code" in notify_result and notify_result['result_code'] == 'FAIL':
        return False, notify_result['return_msg']
    if "result_code" in notify_result and notify_result['result_code'] == 'SUCCESS':
        return True, notify_result


if __name__ == "__main__":
    # dataInfo = {
    #     "device_info": "13546879484654185",             # 设备号， 这里可以存放 操作退款管理员的uuid
    #     "amount": 30,                                   # 退款金额 单位分
    #     "desc": "测试",                                 # 退款备注
    #     "spbill_create_ip": "192.168.100.199",                    #
    #     "partner_trade_no": "2132312",                  # 商户订单号
    #     "openid": "oXmFf0qWpaoyYyiNURA90JK-bSKc"        # 退款给用户的openid
    # }
    dataInfo = {
        "orderNo": "2019112521101915746874198260",         # 商户系统内部订单号 完成的订单查询
        "out_refund_no": "123455",                          # 商户系统内部的退款单号
        "total_fee": 1,                                     # 总共支付金额
        "refund_fee": 1,                                    # 退款金额
        "refund_desc": "测试退款"                                # 退款原因
    }
    print(wx_refund(dataInfo))
    # print(enterprise_payment_to_wallet(dataInfo))
    #
    # print(hbb_wx_refund_query("123456"))

