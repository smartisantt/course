#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager.views import *
from manager_course.views import CourseView, ChapterView, RecyclingView

urlpatterns = [

]


router = DefaultRouter()
# router.register('user', UserView)
router.register('', CourseView)
router.register('Recycling/Lesson', RecyclingView)
router.register('seriesLesson/chapter', ChapterView)


urlpatterns += router.urls
