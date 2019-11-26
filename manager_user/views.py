#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from django.core.cache import caches
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from datetime import datetime, timedelta

from common.api import Api
from common.models import User
from manager_user.filters import UserFilter
from manager_user.serializers import UserBasicSerializer, UserUpdateSerializer
from utils.errors import ParamError


# 后台能展示的普通用户的条件，已删除的不再展示
from utils.funcTools import get_ip_address, create_session, http_return


from utils.msg import USER_NOT_EXISTS, PUT_SUCCESS
from utils.qFilter import USER_Q


class UserView(viewsets.GenericViewSet,
               mixins.CreateModelMixin,
               mixins.ListModelMixin,
               mixins.DestroyModelMixin,
               mixins.UpdateModelMixin,
               mixins.RetrieveModelMixin):
    queryset = User.objects.filter(USER_Q)
    serializer_class = UserBasicSerializer
    filter_class = UserFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime', )

    # @action(methods=('GET', ), detail=True)
    # def consume(self, request, pk):             # 消费记录  /api/manage/userManage/user/<string:uuid>/consume/
    #     return HttpResponseRedirect("/api/manage/orderManage/orderManage/?buyerUuid={}".format(pk))
    #
    # @action(methods=('GET',), detail=True)
    # def share(self, request, pk):              # 分销记录  /api/manage/userManage/user/<string:uuid>/share/
    #     return HttpResponseRedirect("/api/manage/orderManage/orderManage/?shareUserUuid={}".format(pk))

    #  禁用/恢复 用户
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        serializers_data = UserUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_user(instance, serializers_data.data)
        return Response(PUT_SUCCESS)



@api_view(['POST'])
def login(request):
    """
    后台管理端登录模块
    """
    # 获取前端传入token
    token = request.META.get('HTTP_TOKEN')
    # 先在缓存查找
    try:
        user_data = caches['default'].get(token)
    except Exception as e:
        logging.error(str(e))
        return http_return(500, '服务器连接redis失败')

    # 缓存中有数据
    if user_data:
        user_info = caches['default'].get(token)
        userId = user_info.get('userId', '')
        user = User.objects.filter(userID=userId, managerStatus=1).only('userID').first()
        if not user:
            return http_return(403, '此用户被禁止登录')
        userAvatar = user.avatar or "https://hbb-ads.oss-cn-beijing.aliyuncs.com/file4142825175948.jpg"
        return http_return(200, '成功登录',
                           {"nickName": user.nickName,
                            "tel": user.tel,
                            "uuid": user.uuid,
                            "avatar": userAvatar,
                            "managerStatus": user.managerStatus})

    # 如果没有（调用接口查询），
    if not user_data:
        api = Api()
        user_info = api.check_token(token)
        if not user_info:
            return http_return(401, '无效token')
        else:
            userId = user_info.get('userId', '')
            if not userId:
                return http_return(401, '无效token')

            user = User.objects.filter(userID=userId, managerStatus=1).only('userID').first()
            if not user:
                return http_return(403, '没有权限')

            # 写入缓存
            loginIp = get_ip_address(request)
            if not create_session(user, token, loginIp):
                return http_return(500, '创建缓存失败')

            userAvatar = user.avatar or "https://hbb-ads.oss-cn-beijing.aliyuncs.com/file4142825175948.jpg"
            return http_return(200, '成功登录',
                               {"nickName": user.nickName,
                                "tel": user.tel,
                                "uuid": user.uuid,
                                "avatar": userAvatar,
                                "managerStatus": user.managerStatus})