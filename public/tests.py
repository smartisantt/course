#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

DEBUG_HOST = 'http://127.0.0.1:8000'
TEST_HOST = 'http://192.168.100.199:8009'
URL = {
    'create_area': "/api/public/area"
}


def test_create_area():
    """
    测试用户
    :return:
    """
    url = '{0}{1}'.format(DEBUG_HOST, URL['create_area'])
    headers = {'token': 'E55A719CA523B4FF4D81112054D38B18'}
    data = {

    }

    re = requests.post(url, headers=headers, json=data)
    return re.text


if __name__ == "__main__":
    print(test_create_area())
