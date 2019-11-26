#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import django_filters

from common.models import User, Role, Permissions, MANAGER_MODIFY_STATUS_CHOICES


def validate_time(startTime, endTime):
    """
    校验时间
    """
    if ( startTime and endTime):
        if startTime > endTime:
            return False
    return True


class UserFilter(django_filters.FilterSet):
    userNum = django_filters.CharFilter(lookup_expr='icontains')
    nickName = django_filters.CharFilter(lookup_expr='icontains')
    tel = django_filters.CharFilter(lookup_expr='contains')
    roles = django_filters.CharFilter(method='filter_by_roles')
    managerStatus = django_filters.ChoiceFilter(choices=MANAGER_MODIFY_STATUS_CHOICES)
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")  # searchTime_before   searchTime_after

    class Meta:
        model = User
        fields = ('userNum', 'nickName', 'tel', 'managerStatus', 'roles')


class RoleFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Role
        fields = ('uuid', 'name')


class PermissionsFilter(django_filters.FilterSet):

    class Meta:
        model = Permissions
        fields = ('uuid', 'menuName')


class UserSearchFilter(django_filters.FilterSet):
    nickName = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = User
        fields = ('uuid', 'nickName')