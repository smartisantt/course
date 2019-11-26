#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import django_filters
from django import forms
from django_filters.fields import RangeField
from django_filters.widgets import DateRangeWidget, BooleanWidget

from client.models import Banner
from common.modelChoices import *
from utils.errors import ParamError
from common.models import Tags, Section, Courses, Experts, MustRead, CourseSource, SectionCourse, User, Goods, \
    HotSearch, LiveCourse, LiveCourseMsg


def validate_time(startTime, endTime):
    """
    校验时间
    """
    if (startTime and endTime):
        if startTime > endTime:
            return False
    return True


class TagFilter(django_filters.FilterSet):
    """标签filter"""
    uuid = django_filters.CharFilter("uuid", lookup_expr="iexact")  # 精确匹配
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    tagType = django_filters.ChoiceFilter(choices=TAG_CHOICES)
    level = django_filters.ChoiceFilter(choices=TAG_LEVEL_CHOICES)
    enable = django_filters.BooleanFilter("enable", widget=BooleanWidget())
    class Meta:
        model = Tags
        fields = ("name", "tagType", "parentUuid", "weight", "enable", "level")


class SectionFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    intro = django_filters.CharFilter("intro", lookup_expr="icontains")  # 栏目说明

    enable = django_filters.BooleanFilter("enable", widget=BooleanWidget())
    isShow = django_filters.BooleanFilter("isShow", widget=BooleanWidget())

    class Meta:
        model = Section
        fields = ("uuid", "createTime", "updateTime", "name", "intro", "enable", "isShow")


class ExpertFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    department = django_filters.CharFilter("department", lookup_expr="icontains")  # 科室
    jobTitle = django_filters.CharFilter("jobTitle", lookup_expr="icontains")  # 职称
    hospital = django_filters.CharFilter("hospital", lookup_expr="icontains")  # 模糊匹配
    tel = django_filters.CharFilter("tel", lookup_expr="icontains")  # 模糊匹配
    enable = django_filters.BooleanFilter(widget=BooleanWidget())
    isStar = django_filters.BooleanFilter(widget=BooleanWidget())

    class Meta:
        model = Experts
        fields = ("uuid", "avatar", "name", "department", "jobTitle", "hospital", "tel", "isStar", "enable")


class MustReadFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    mustReadType = django_filters.ChoiceFilter(choices=MUSTREAD_TYPE_CHOICES)  # 模糊匹配
    mustReadNum = django_filters.NumberFilter()

    class Meta:
        model = MustRead
        fields = ("uuid", "createTime", "updateTime", "name", "content", "mustReadNum", "mustReadType", "enable")


class CourseSourceFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    sourceType = django_filters.ChoiceFilter(choices=COURSESOURCE_TYPE_CHOICES)
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")
    enable = django_filters.BooleanFilter("enable", widget=BooleanWidget())

    class Meta:
        model = CourseSource
        fields = (
            "uuid", "createTime", "name", "sourceUrl", "sourceType", "fileSize", "duration", "pages", "enable")


class SearchSectionCourseFilter(django_filters.FilterSet):
    sectionUuid = django_filters.CharFilter("sectionUuid", lookup_expr="exact")
    status = django_filters.ChoiceFilter("status",choices=SECTION_COURSE_SHOW_STATUS)

    class Meta:
        model = SectionCourse
        fields = "__all__"


class SearchUserFilter(django_filters.FilterSet):
    nickName = django_filters.CharFilter("nickName", lookup_expr="icontains")
    tel = django_filters.CharFilter("tel", lookup_expr="icontains")

    class Meta:
        model = User
        fields = ()


class SearchGoodsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter("name", lookup_expr="icontains")

    class Meta:
        model = Goods
        fields = ("goodsType", )


class SearchCoursesFilter(django_filters.FilterSet):
    name = django_filters.CharFilter("name", lookup_expr="icontains")

    class Meta:
        model = Courses
        fields = ()




class SectionCourseFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")

    class Meta:
        model = Section
        fields = (
            "uuid", "updateTime", "name", "showNum", "weight", "enable")


class BannerFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter("uuid", lookup_expr="exact")
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")

    class Meta:
        model = Banner
        fields = ()


class HotSearchFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter("keyword", lookup_expr="icontains")

    class Meta:
        model = HotSearch
        fields = ("status", )


class LiveCourseFilter(django_filters.FilterSet):
    name = django_filters.CharFilter("name", lookup_expr="icontains")
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")
    enable = django_filters.BooleanFilter("enable", widget=BooleanWidget())

    class Meta:
        model = LiveCourse
        fields = ("enable", )


class LiveCourseMsgFilter(django_filters.FilterSet):
    name = django_filters.CharFilter("name", lookup_expr="icontains")

    class Meta:
        model = LiveCourseMsg
        fields = ("liveCourseUuid", )


