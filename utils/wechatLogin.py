"""
微信授权登录API
author:York
time:2019-10-12
"""
import json
import logging

import requests


class WxLogin(object):

    def __init__(self, appType="web"):
        self.get_token_host = "https://api.weixin.qq.com/sns/oauth2/access_token"
        self.refresh_token_host = "https://api.weixin.qq.com/sns/oauth2/refresh_token"
        self.check_token_host = "https://api.weixin.qq.com/sns/auth"
        self.user_info_host = "https://api.weixin.qq.com/sns/userinfo"

        # 微信应用信息
        self.APPID = "wxd3d1c26385c26506"
        self.APPSECRET = "dd61b55eb4589f52ad349a2ba915d829"
        if appType == "web":
            self.APPID = "wx233ca74b3d313293"
            self.APPSECRET = "9cad6815a46a19e8d2fc5b50c2c3a1e4"

    def get_access_token(self, code):
        """
        获取access_token
        :return:
        """
        data = {
            "appid": self.APPID,
            "secret": self.APPSECRET,
            "code": code,
            "grant_type": "authorization_code"
        }
        try:
            response = requests.get(self.get_token_host, params=data)
        except Exception as e:
            logging.error(str(e))
            return False
        # print(response.content.decode("utf-8"))
        return json.loads(response.content.decode("utf-8"))

    def check_token(self, access_token, openid):
        data = {
            "access_token": access_token,
            "openid": openid
        }
        try:
            response = requests.get(self.check_token_host, params=data)
        except Exception as e:
            logging.error(str(e))
            return False
        return json.loads(response.content.decode("utf-8"))

    def refresh_token(self, refresh_token):
        data = {
            "appid": self.APPID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        try:
            response = requests.get(self.refresh_token_host, params=data)
        except Exception as e:
            logging.error(str(e))
            return False
        return json.loads(response.content.decode("utf-8"))

    def get_user_info(self, access_token, openid):
        data = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN"
        }
        try:
            response = requests.get(self.user_info_host, params=data)
        except Exception as e:
            logging.error(str(e))
            return False
        return json.loads(response.content.decode("utf-8"))

    def work_on(self, code):
        res = self.get_access_token(code)
        if not res:
            return False
        access_token = res.get("access_token")
        refresh_token = res.get("refresh_token")
        openid = res.get("openid")
        check_res = self.check_token(access_token, openid)
        if not check_res:
            return False
        if check_res.get("errcode") != 0:
            refresh_res = self.refresh_token(refresh_token)
            access_token = refresh_res.get("access_token")
            # refresh_token = refresh_res.get("refresh_token")
            openid = refresh_res.get("openid")
        user_res = self.get_user_info(access_token, openid)
        if not user_res:
            return False
        # print(user_res)
        return user_res


if __name__ == "__main__":
    wxLogin = WxLogin()
    print(wxLogin.work_on("001ipmAi1uBpZu09pOAi1AI5Ai1ipmAH"))
    # access_token = "26_AEkF4tQIbdYWiejWytHQiqbZNS1CPATIB4TLyykhxFuUdFMepHvbgldGUGCs0S-bON0wSNkG7dHAwxMq2H7s6g"
    # openid = "oXmFf0qWpaoyYyiNURA90JK-bSKc"
    # print(wxLogin.get_user_info(access_token, openid))
