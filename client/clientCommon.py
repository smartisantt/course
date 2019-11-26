#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端+H5 公有方法
"""
import datetime
import logging
import random
import re
import time
import uuid


def get_token():
    """
    随机生成token
    :return:
    """
    return uuid.uuid4().hex


def match_tel(tel):
    """
    正则校验手机号
    :param tel:
    :return:
    """
    if re.match(r'^1[3-9]\d{9}$', tel):
        return True
    return False


def datetime_to_string(mydate, rule='%Y-%m-%d %H:%M:%S'):
    """
    将datetime.datetime转为string
    :param mydate:
    :return:
    """
    if isinstance(mydate, datetime.datetime) or isinstance(mydate, datetime.date):
        return mydate.strftime(rule)
    else:
        return mydate


def string_to_datetime(mystr, rule='%Y-%m-%d %H:%M:%S'):
    """
    将string转为 datetime.datetime
    :param mydate:
    :return:
    """
    if isinstance(mystr, str):
        return datetime.datetime.strptime(mystr, rule)
    else:
        return mystr


def page_index(myList, page=1, limit=10):
    """
    分页
    :param page: 页码  第一页为1
    :param limit: 每一页显示条数
    :return: total + list
    """
    page = page if page and int(page) > 0 else 0
    limit = limit if limit else 20

    if not all([isinstance(page, int), isinstance(limit, int)]):
        try:
            page = int(page)
            limit = int(limit)
        except Exception as e:
            logging.error(str(e))
            return myList
    total = len(myList)
    if page == 0:
        startPage = 0
        endPage = limit
    else:
        startPage = (page - 1) * limit
        endPage = page * limit
    if total < startPage:
        return total, []
    if total < endPage:
        endPage = total
    return total, myList[startPage: endPage]


def seconds_to_hour(num):
    """
    秒转时分秒
    :param num:
    :return:
    """
    h = num // 3600
    num = num % 3600
    m = num // 60
    s = num % 60
    return '%d:%d:%d' % (h, m, s)


def hour_to_seconds(data):
    """
    秒转时分秒
    :param num:
    :return:
    """
    h = int(data.split(":")[0]) * 3600
    m = int(data.split(":")[1]) * 60
    s = int(data.split(":")[2])
    return h + m + s


def datetime_to_unix(_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    if isinstance(_time, datetime.datetime):
        return time.mktime(_time.timetuple()) * 1000
    else:
        return _time


def random_string(size=6):
    """
    随机字符串
    :param size:
    :return:
    """
    base_str = '0123456789'
    checkcode = []
    for i in range(size):
        checkcode.append(random.choice(base_str))
    return "".join(checkcode)


def get_default_name(tel):
    """
    获取默认用户名
    :return:
    """
    if tel == '':
        result = ''
    else:
        start = tel[:3]
        end = tel[-4:]
        result = start + "****" + end
    return result


def get_orderNO():
    """
    获取订单号
    :return:
    """
    start = datetime_to_string(datetime.datetime.now(), rule='%Y%m%d%H%M%S')
    end = str(int(time.time() * 1000)) + str(int(time.clock() * 100000))
    res = start + end
    return res[:28]


def get_day_zero_time(date, btype="datetime"):
    """根据日期获取当天凌晨时间"""
    if not date:
        return False
    date_zero = datetime.datetime.now().replace(year=date.year, month=date.month,
                                                day=date.day, hour=0, minute=0, second=0)
    date_zero_time = int(time.mktime(date_zero.timetuple())) * 1000
    if btype == "unix":
        return date_zero_time
    elif btype == "datetime":
        return date_zero
    return False


def get_day_latest_time(date, btype="datetime"):
    """根据日期获取当天最晚时间"""
    if not date:
        return False
    date_latest = datetime.datetime.now().replace(year=date.year, month=date.month,
                                                  day=date.day, hour=23, minute=59, second=59)
    date_latest_time = int(time.mktime(date_latest.timetuple())) * 1000
    if btype == "unix":
        return date_latest_time
    elif btype == "datetime":
        return date_latest
    return False


def unix_time_to_datetime(unix_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    try:
        _time = datetime.datetime.fromtimestamp(unix_time / 1000)
    except:
        _time = unix_time
    return _time


def string_to_unix_time(_str, rule='%Y-%m-%d %H:%M:%S'):
    """
    str 转unix时间戳
    :param _str:
    :param rule:
    :return:
    """
    _time = string_to_datetime(_str, rule)
    return time.mktime(_time.timetuple()) * 1000


def string_to_date(mystr, rule='%Y-%m-%d %H:%M:%S'):
    """
    将string转为 datetime.datetime
    :param mydate:
    :return:
    """
    if isinstance(mystr, str):
        return datetime.datetime.strptime(mystr, rule)
    else:
        return mystr


def is_valid_idcard(idcard):
    """身份证校验"""
    if isinstance(idcard, int):
        idcard = str(idcard)
    IDCARD_REGEX = '[1-9][0-9]{14}([0-9]{2}[0-9X])?'
    if not re.match(IDCARD_REGEX, idcard):
        return False
    items = [int(item) for item in idcard[:-1]]
    factors = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)  # 加权因子
    copulas = sum([a * b for a, b in zip(factors, items)])  # 加权求积
    ckcodes = ('1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2')  # 求余取对应位
    return ckcodes[copulas % 11].upper() == idcard[-1].upper()


if __name__ == "__main__":
    # print(random_string(6))
    # print(get_token())
    print(get_orderNO(),len(get_orderNO()))
    # print(get_day_zero_time(datetime.datetime.today()))
    # print(get_day_latest_time(datetime.datetime.today()))
    # print(match_tel("W13333333333"))
    # print(is_valid_idcard(""))
