#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager import views
from manager_rabc.views import *

urlpatterns = [
    # 用户名模糊搜索
    path('searchNickname/', UserSearchView.as_view()),
    path('validateTel/', validate_tel),
]

router = DefaultRouter()
router.register('user', UserRolesView)

# 管理员相关路由
router.register('userRoles', UserView)
router.register('roles', RoleView)
router.register('permission', PermissionsView)

urlpatterns += router.urls


