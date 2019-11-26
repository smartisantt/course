#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager.views import *

urlpatterns = [
]

router = DefaultRouter()
# router.register('user', UserView)

router.register('LableManageAll', TagView)                                      # 之前路由tags
router.register('columnManage', SectionView)                                    # 之前section
router.register('columnManage/changeWeight', SectionChangeView)                 # 修改栏目展示顺序
router.register('userManage/specialist', ExpertView)                            # 之前路由experts
router.register('lessonManage/lessonStoreManageAll', CourseSourceView)          # 课件库
router.register('lessonManage/lessonStoreManageAllLiveCourse', LiveCourseView)  # 上传直播课件 + 素材
router.register('lessonManage/lessonStoreManageAllMsg', LiveCourseMsgView)      # 单条消息列表
router.register('fixedSettings/mustRead', MustReadView)                         # 固定配置，之前路由mustRead
router.register('fixedSettings/sectionCourse', SectionCourseView)               # 之前路由sectionCourse
router.register('fixedSettings/banner', BannerView)                             # 陈伦巨 写的banner
router.register('fixedSettings/changeBannerOrder', BannerChangeView)            # 交换轮播图顺序
router.register('fixedSettings/hotSearch', HotSearchView)                       # 陈伦巨 写的搜索词
router.register('fixedSettings/changeHotSearchOrder', HotSearchChangeView)     # 交换关键词顺序
router.register('fixedSettings/courseLive', CourseLiveView)                    # 陈伦巨 写的大咖直播
router.register('fixedSettings/changeCourseLiveOrder', CourseLiveChangeView)     # 交换大咖直播顺序
router.register('fixedSettings/mayLike', MayLikeView)                           # 陈伦巨 写的猜你喜欢
router.register('fixedSettings/changeMayLikeOrder', MayLikeOrderChangeView)    # 交换猜你喜欢顺序
router.register('search/sectionCourse', searchSectionCourseView)                # 搜索
router.register('search/user', searchUserView)                                  # 搜索
router.register('search/goods', searchGoodsView)                                # 优惠卷中》》 搜索商品表
router.register('search/courses', searchCoursesView)                            # 搜索课程表
router.register('search/coursesLive', searchCoursesLiveView)                    # 搜索课程表


urlpatterns += router.urls
