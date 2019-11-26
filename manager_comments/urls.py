#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rest_framework.routers import DefaultRouter

from manager_comments.views import CommentsView

urlpatterns = [

]


router = DefaultRouter()
router.register('commentCheck', CommentsView)

urlpatterns += router.urls
