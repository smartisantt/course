#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager.views import *
from manager_course.views import CourseView, ChapterView, RecyclingView, DummyUserView, RandomDummyView, ChatsHistoryView

urlpatterns = [

]


router = DefaultRouter()
# router.register('user', UserView)
router.register('', CourseView)
router.register('Recycling/Lesson', RecyclingView)
router.register('seriesLesson/chapter', ChapterView)
router.register('liveRoom/dummyUser', DummyUserView)
router.register('liveRoom/randomUser', RandomDummyView)
router.register('liveRoom/chatsHistory', ChatsHistoryView)

urlpatterns += router.urls
