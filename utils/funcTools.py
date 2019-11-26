import json
import logging
from datetime import datetime

from django.core.cache import caches
from django.http import HttpResponse

from parentscourse_server.config import USER_CACHE_OVER_TIME


def http_return(code, msg='', info=None):
    """
    返回封装
    :param code: 状态码
    :param msg: 返回消息
    :param info: 返回数据
    :return:
    """
    data = {
        'code': code,
        'msg': msg
    }
    if info is not None:
        data['data'] = info
    return HttpResponse(json.dumps(data), status=code)


def my_logger(request, logger):
    remote_info = ''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        remote_info = ' HTTP_X_FORWARDED_FOR:' + x_forwarded_for.split(',')[0]
    else:
        remote_addr = request.META.get('REMOTE_ADDR')
        remote_info += ' REMOTE_ADDR:' + remote_addr
    token = request.META.get('HTTP_TOKEN')
    user_agent = request.META.get('HTTP_USER_AGENT')
    logger.info(remote_info + ' URL:' + request.path + ' METHOD:' + request.method +
                ' TOKEN:' + token + ' USER_AGENT:' + user_agent)


def get_ip_address(request):
    """获取请求的IP地址"""
    # HTTP_X_FORWARDED_FOR也就是HTTP的请求端真实的IP，
    # 只有在通过了HTTP 代理或者负载均衡服务器时才会添加该项。
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    return ip or request.META['REMOTE_ADDR']


def create_session(user, token, loginIP):
    """用户信息保存至caches"""
    userInfo = {
        'nickName': user.nickName or '',
        'uuid': user.uuid,
        'userId': user.userID,
        'tel': user.tel,
        'loginIp': loginIP
    }
    try:
        caches['default'].set(token, userInfo, timeout=USER_CACHE_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def timeStamp2dateTime(timeNum):
    """
    毫秒时间戳转时间格式
    :param timeNum:
    :return:
    """
    timeStamp = float(timeNum/1000)
    dateArray = datetime.utcfromtimestamp(timeStamp)
    return dateArray


if __name__ == '__main__':
    print(timeStamp2dateTime(1535990400000))