#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager_order.views import OrderDetailView, RefundView

urlpatterns = [
]

router = DefaultRouter()

# 订单列表
router.register('orderManage', OrderDetailView)

# 退款管理
router.register('refundManage', RefundView)


urlpatterns += router.urls
