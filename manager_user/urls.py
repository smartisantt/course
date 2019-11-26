#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path
from rest_framework.routers import DefaultRouter

from manager_order.views import OrderDetailView
from manager_user.views import UserView, login

urlpatterns = [
    path('login/', login, name='login')
]

router = DefaultRouter()

router.register('userList', UserView)
router.register('userListOrder', OrderDetailView)

urlpatterns += router.urls
