import time
import datetime

def timeChange(input_time, method):
    """

    :param datetime: 传入参数
    :param method: 1为时间戳转datetime，2为字符串datetime转时间戳，3为datetime转时间戳
    :return:
    """
    if method == 1:
        timeArray = (int(input_time / 1000))
        otherStyleTime =datetime.datetime.fromtimestamp(timeArray)
    elif method == 2:
        otherStyleTime = int(time.mktime(time.strptime(input_time, "%Y-%m-%dT%H:%M:%S"))) * 1000
    elif method == 3:
        otherStyleTime = int(time.mktime(input_time.timetuple()))*1000
    else:
        otherStyleTime = None
    return otherStyleTime
