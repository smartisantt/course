#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 电话号码正则
TEL_PATTERN = re.compile(r'^1[3-9]\d{9}$')


def CheckPhone(phone):
    if not TEL_PATTERN.match(phone):
        return False
    else:
        return True


# 邮箱正则
# 其他正则。。。


if __name__ == '__main__':
    # if not re.match(TEL_PATTERN, "12333333333"):
    if not TEL_PATTERN.match("136529874115"):
        print("error")
    else:
        print("OK")
