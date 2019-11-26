import logging
from datetime import datetime

import django_filters

from client.models import Banner, Courses, Comments
from common.models import Experts
from utils.errors import ParamError


def validate_time(startTime, endTime):
    """
    校验时间````````
    """
    if (startTime and endTime):
        if startTime > endTime:
            return False
    return True


class BannerFilter(django_filters.FilterSet):
    """轮播图过滤器"""
    uuid = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')
    target = django_filters.CharFilter(lookup_expr='icontains')
    startTime = django_filters.NumberFilter(method='filter_by_startTime')
    endTime = django_filters.NumberFilter(method='filter_by_endTime')

    class Meta:
        model = Banner
        fields = ('uuid', 'name', 'icon', 'type', 'target')


class SectionFilter(django_filters.FilterSet):
    """板块过滤"""
    pass


class CourseFilter(django_filters.FilterSet):
    """课程过滤器"""
    uuid = django_filters.CharFilter("uuid", lookup_expr='icontains')

    class Meta:
        model = Courses
        fields = ('uuid',)

class CommentFilter(django_filters.FilterSet):
    """评论过滤器"""
    uuid = django_filters.CharFilter("uuid", lookup_expr='icontains')

    class Meta:
        model = Comments
        fields = ('uuid',)

class ExpertFilter(django_filters.FilterSet):
    """课程过滤器"""
    uuid = django_filters.CharFilter("uuid", lookup_expr='icontains')

    class Meta:
        model = Experts
        fields = ('uuid',)


class SearchLikeFilter(django_filters.FilterSet):
    """课程过滤器"""
    name = django_filters.CharFilter("keyword", lookup_expr='icontains')

    class Meta:
        model = Courses
        fields = ('name',)