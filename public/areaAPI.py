#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging

import requests


class Area(object):
    """高德地图获取地区信息"""

    def __init__(self):
        self.url = "https://restapi.amap.com/v3/config/district"
        self.headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; InfoPath.3)'}
        self.params = {
            "key": "1d25cdd07a8b5fc88641e916afaf538e",
            "subdistrict": 3
        }

    def get_data(self):
        # 获取地区信息
        try:
            res = requests.get(self.url, params=self.params, headers=self.headers)
            res.encoding = "utf-8"
            # html为json格式的字符串
            data = res.text
            # 把json格式字符串转为python数据类型
            data = json.loads(data)
            if data['info'] == "OK":
                return data["districts"][0]
        except Exception as e:
            logging.err(str(e))
        return False

