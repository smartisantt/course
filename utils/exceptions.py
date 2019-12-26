#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:

        response.data['code'] = response.data.get('code') or response.status_code
        if response.data.get('detail'):
            response.data['msg'] = response.data.get('detail')
            if response.data['code'] == 429:
                response.data['code'] = 400
                response.data['msg'] = '今日发送短信已超出限制'
        elif response.data.get('msg'):
            response.data['msg'] = response.data.get('msg')
        elif response.data.get(list(response.data)[0]):
            response.data['msg'] = list(response.data)[0] + "：" + response.data.get(list(response.data)[0])[0]
        else:
            response.data['msg'] = '参数有误'

    return response