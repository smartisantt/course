#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rest_framework.routers import DefaultRouter

from public.views import *

urlpatterns = []

router = DefaultRouter()
router.register('area', AreaView)

urlpatterns += router.urls
