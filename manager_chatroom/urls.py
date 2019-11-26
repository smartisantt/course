#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path
from rest_framework.routers import DefaultRouter

from manager_chatroom.views import echo_once

urlpatterns = [
    path('echo_once', echo_once),
]

