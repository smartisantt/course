#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path

from manager_auth.views import login, register, sendCode, logout, modifyPassword, resetPassword, initAdmin

urlpatterns = [
    # path('login/', createAdmin, name='createAdmin'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('sendCode/', sendCode, name='sendCode'),
    path('logout/', logout, name='logout'),
    path('modifyPassword/', modifyPassword, name='modifyPassword'),
    path('resetPassword/', resetPassword, name='resetPassword'),
    path('initAdmin/', initAdmin, name='initAdmin'),
]

