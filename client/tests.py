#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from django.db.models import Count

import os, django

from client.models import Behavior

DEBUG_HOST = 'http://192.168.100.199:8000'
TEST_HOST = 'http://192.168.100.199:8009'
URL = {
    'create_area': "/area"
}
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()


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


def get_behavior():
    qs = Behavior.objects.filter(behaviorType=3, isDelete=False).extra(
        select={"CreateDate": "DATE_FORMAT(CreateTime,'%%e')"}).values("CreateDate").annotate(count=Count("*")).values(
        "CreateDate", "uuid")
    return qs


if __name__ == "__main__":
    # print(test_create_area())
    print(get_behavior())
