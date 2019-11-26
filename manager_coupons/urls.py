#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rest_framework.routers import DefaultRouter

from manager_coupons.views import CouponsView, UserCouponsView

urlpatterns = [

]


router = DefaultRouter()
router.register('couponManage', CouponsView)
router.register('couponManage/userCoupon/detail', UserCouponsView)

urlpatterns += router.urls
