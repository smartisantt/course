#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, authentication_classes, action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from manager_auth.views import getAndCheckTel
from manager_rabc.filters import *
from manager_rabc.serializers import *
from common.models import User, Role
from utils.auths import CustomAuthentication
from utils.errors import ParamError

# 后台管理员状态：正常和被禁用的状态
from utils.funcTools import http_return

q = Q(managerStatus__in=[1, 3])
# 所有普通用户状态
#     (1, "正常"),
#     (2, "删除"),
#     (3, "禁止登录"),
#     (4, "禁止发言")
q2 = Q(status__in=[1, 3, 4])


# 后台管理员用户操作
class UserView(viewsets.GenericViewSet,
               mixins.ListModelMixin,
               mixins.DestroyModelMixin,
               mixins.UpdateModelMixin,
               mixins.RetrieveModelMixin):

    queryset = User.objects.filter(q).prefetch_related('roles')
    serializer_class = UserBasicSerializer
    filter_class = UserFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    #GET  /api/manage/roles/userRoles/<string:uuid>/menu/
    # 获取指定用户显示的菜单
    @action(methods=('GET', ), detail=True)
    def menu(self, request, pk):
        try:
            user = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        # 遍历当前用户拥有的角色，角色拥有的菜单，如果二级菜单已选择，则要添加上对应的一级菜单，菜单要去重
        data = []
        for role in user.roles.all():
            for permission in role.permissions.all():
                if (permission.uuid not in data) and (permission.uuid):
                    data.append(permission.uuid)
                if (permission.parentUuid_id) and (permission.parentUuid_id not in data):
                    data.append(permission.parentUuid_id)
        queryset = Permissions.objects.filter(enable=True, uuid__in=data, parentUuid_id__isnull=True)\
            .prefetch_related('subMenu').order_by("sortNum")
        return Response(UserPermissionsBasicSerializer(queryset, many=True, context={"data":data}).data)

    def destroy(self, request, *args, **kwargs):
        # 删 管理员
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        instance.managerStatus = 2  # 这里只改变管理员状态为删除状态， 无法再登录后台
        instance.save()
        return Response(DEL_SUCCESS)

    def update(self, request, *args, **kwargs):
        # 改
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        # if request.user == instance:
        #     raise ParamError("无法修改自己的角色")
        serializers_data = UserUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_user(instance, serializers_data.data)
        return Response(PUT_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RoleView(viewsets.GenericViewSet,
               mixins.CreateModelMixin,
               mixins.ListModelMixin,
               mixins.DestroyModelMixin,
               mixins.UpdateModelMixin,
               mixins.RetrieveModelMixin):

    queryset = Role.objects.exclude(status=3).prefetch_related('permissions')
    serializer_class = RoleBasicSerializer
    filter_class = RoleFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('createTime',)

    def create(self, request, *args, **kwargs):
        # 增
        serializers_data = RolePostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
            # raise ParamError({'code': 400, 'msg': "参数有误", "errors": serializers_data.errors})
        serializers_data.create_role(serializers_data.data)
        return Response(POST_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(ROLE_NOT_EXISTS)
        # 角色被使用则不能删除
        if User.objects.filter(roles=instance).exists():
            raise ParamError("角色被使用则不能删除")
        instance.status = 3
        users = User.objects.all()
        instance.user.remove(*users)
        # 删除中间表数据， 删除角色的时候，用户关联的角色的中间表也被删除
        instance.save()
        return Response(DEL_SUCCESS)

    def update(self, request, *args, **kwargs):
        # 改
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(ROLE_NOT_EXISTS)
        serializers_data = RoleUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_role(instance, serializers_data.data)
        return Response(PUT_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        # 查
        try:
            instance = self.get_object()
            if instance.status == 3:
                raise ParamError(ROLE_NOT_EXISTS)
        except Exception as e:
            raise ParamError(ROLE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# 权限菜单
class PermissionsView(viewsets.GenericViewSet,
                      mixins.RetrieveModelMixin,
                      mixins.ListModelMixin):

    queryset = Permissions.objects.filter(enable=True, parentUuid_id__isnull=True).prefetch_related('subMenu')
    serializer_class = PermissionsBasicSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('sortNum',)
    pagination_class = None


# 用户昵称模糊搜索
class UserSearchView(ListAPIView):
    queryset = User.objects.only('uuid', 'nickName').exclude(status=2).order_by("nickName")
    serializer_class = UserSearchSerializer
    filter_class = UserSearchFilter
    pagination_class = None


# 用户分配权限 已有用户分配权限  和 添加新管理员
class UserRolesView(viewsets.GenericViewSet,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin):

    queryset = User.objects.filter(q2).prefetch_related('roles')
    serializer_class = UserBasicSerializer
    filter_class = UserFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('createTime',)

    # 添加新管理员
    def create(self, request, *args, **kwargs):
        # 增
        serializers_data = UserRolesPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_user(serializers_data.validated_data)
        return Response(ADD_AMDIN_SUCCESS)

    # 已有用户分配权限
    def update(self, request, *args, **kwargs):
        # 改
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        if instance.managerStatus == 1:
            raise ParamError("此用户已是管理员")
        msg = {'code': 200, 'msg': '添加管理员成功'}
        if not instance.passwd:
            msg = {'code': 200, 'msg': '该用户为迁移用户，密码为123456'}
        serializers_data = UserRolesUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_user(instance, serializers_data.validated_data)
        return Response(msg)

    def retrieve(self, request, *args, **kwargs):
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# 查询用户 是新用户 还是普通用户变管理员 还是已经添加过的管理员  还是已经删除过的管理员
@api_view(['POST'])
def validate_tel(request):
    res, msg, tel = getAndCheckTel(request)
    if not res:
        return http_return(400, msg)

    # status 1 普通用户 2 新建用户  3 已是管理员
    user = User.objects.filter(tel=tel).first()
    if not user:
        # 新用户
        return http_return(200, '该用户为新用户', {'status': 2})
    if user.managerStatus in [2, 3, 4]:
        # 普通用户
        return http_return(200, '该用户为普通用户', {'status': 1, 'uuid': user.uuid})
    else:
        return http_return(200, '该用户已经是管理员', {'status': 3})

