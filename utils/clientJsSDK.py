"""
处理js sdk的使用
"""
import hashlib
import json
import time
from random import Random

import requests

from parentscourse_server.config import WEBAPPID, WEBSECRET, APPID, SECRET


def get_js_sign(data_dict):
    string = '&'.join(['{0}={1}'.format(key.lower(), data_dict[key]) for key in sorted(data_dict)]).encode('utf-8')
    signature = hashlib.sha1(string).hexdigest()
    return signature


def get_js_noncestr(randomlength=8):
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


def get_res_data(js_ticket, url):
    noncestr = get_js_noncestr(16)
    timestamp = int(time.time())
    data_info = {
        "nonceStr": noncestr,
        "jsapi_ticket": js_ticket,
        "timestamp": timestamp,
        "url": url,
    }
    sign = get_js_sign(data_info)
    js_data = {
        "appId": WEBAPPID,
        "nonceStr": noncestr,
        "timestamp": timestamp,
        "signature": sign,
    }
    return js_data


class JsSdk(object):

    def __init__(self, appType=None):
        self.access_token_host = "https://api.weixin.qq.com/cgi-bin/token"
        self.jsapi_ticket_host = "https://api.weixin.qq.com/cgi-bin/ticket/getticket"

        # 微信应用信息
        self.APPID = WEBAPPID
        self.APPSECRET = WEBSECRET
        if appType == "app":
            self.APPID = APPID
            self.APPSECRET = SECRET

    def get_access_token(self):
        data = {
            "grant_type": "client_credential",
            "appid": self.APPID,
            "secret": self.APPSECRET
        }
        response = requests.get(self.access_token_host, params=data)
        res_data = json.loads(response.content.decode("utf-8"))
        access_token = res_data.get("access_token", None)
        if not access_token:
            return False
        return access_token

    def get_jsapi_ticket(self, accesss_token):
        data = {
            "access_token": accesss_token,
            "type": "jsapi"
        }
        response = requests.get(self.jsapi_ticket_host, params=data)
        res_data = json.loads(response.content.decode("utf-8"))
        errcode = res_data.get("errcode")
        if errcode != 0:
            return False
        jsapi_ticket = res_data.get("ticket")
        return jsapi_ticket


if __name__ == "__main__":
    pass
