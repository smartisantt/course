#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import re

from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from common.models import User
from utils.funcTools import my_logger

logger = logging.getLogger('ipandpath')

# 无需token的路由
url_list = [
                "/api/manage/auth/login/",
                "/api/manage/auth/register/",
                "/api/manage/auth/sendCode/",
                "/api/manage/auth/resetPassword/",
                "/api/manage/auth/initAdmin/",
                "/api/manage/im/imLogin/",
                "/api/manage/notoken/ppt2png/",
            ]


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if re.match(r'^/api/manage/notoken[a-z0-9A-Z/]+/$', request.path):
            return AnonymousUser, None
        if request.path in url_list:
            return AnonymousUser, None

        token = request.META.get('HTTP_TOKEN')
        if not token:
            raise AuthenticationFailed('提供有效的身份认证标识')
        # 打印日志消息
        my_logger(request, logger)

        # 验证token
        try:
            user_info = caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            raise AuthenticationFailed('连接Redis失败!!')

        if not user_info:
            raise AuthenticationFailed('登录失效请登录')

        if user_info:
            UserUuid = user_info.get('uuid', '')
            if not UserUuid:
                raise AuthenticationFailed('没有管理员权限')
            user = User.objects.filter(uuid=UserUuid, managerStatus=1).first()
            if not user:
                raise AuthenticationFailed('没有管理员权限')
            return user, token


class CustomAuthorization(BasePermission):

    message = '对不起，你没有权限'

    def has_permission(self, request, view):
        # 当前用户的权限缓存
        if not request.user or isinstance(request.user, AnonymousUser):
            return True
        # path = request.path
        # if not path.startswith("/api/manage/"):
        #     return False
        # for role in request.user.roles.all():
        #     for permission in role.permissions.all():
        #         if permission.url in request.path:
        #             return True
        # return False
        return True


class IMAuthentication(BaseAuthentication):

    def authenticate(self, request):
        token = request.META.get('HTTP_TOKEN', None)
        if not token:
            raise AuthenticationFailed("请登录后继续访问")
        # 打印日志消息
        my_logger(request, logger)
        try:
            # 读取客户端 后台的 token
            user_info = caches['client'].get(token) or caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            raise AuthenticationFailed("服务器缓存错误")
        if not user_info:
            raise AuthenticationFailed('登录失效，请重新登录')
        UserUuid = user_info.get('uuid', '')
        user = User.objects.filter(uuid=UserUuid).first()
        if not user:
            raise AuthenticationFailed("登录失效，请重新登录")
        return user, token
