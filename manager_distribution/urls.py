#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager_distribution.views import CourseRepresView, OrderDetailView, CourseRepresTradeView, \
    CourseRepresWithdrawView

urlpatterns = [
]

router = DefaultRouter()

# 课代表管理
router.register('courseRepresManag', CourseRepresView)
# 课代表管理>>订单详细
router.register('courseRepresManagOrderDetail', OrderDetailView)
# 菜单：【课代表分成交易管理】
router.register('classRepreDivideTradeManag', CourseRepresTradeView)

# 菜单：【课代表提现交易管理】
router.register('classRepreCashwithdrawManag', CourseRepresWithdrawView)


urlpatterns += router.urls
