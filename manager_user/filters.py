#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import django_filters

from common.models import User, Role, Permissions, USER_STATUS_CHOICES, GENDER_CHOICES
from utils.errors import ParamError


def validate_time(startTime, endTime):
    """
    校验时间
    """
    if (startTime and endTime):
        if startTime > endTime:
            return False
    return True


class UserFilter(django_filters.FilterSet):
    uuid = django_filters.CharFilter(lookup_expr='icontains')
    nickName = django_filters.CharFilter(lookup_expr='icontains')
    tel = django_filters.CharFilter(lookup_expr='contains')
    status = django_filters.ChoiceFilter(choices=USER_STATUS_CHOICES)
    gender = django_filters.ChoiceFilter(choices=GENDER_CHOICES)
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")  # searchTime_before   searchTime_after

    class Meta:
        model = User
        fields = ('uuid', 'nickName', 'tel', 'status', 'gender')


class RoleFilter(django_filters.FilterSet):
    roleName = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Role
        fields = ('uuid', 'roleName')


class PermissionsFilter(django_filters.FilterSet):

    class Meta:
        model = Permissions
        fields = ('uuid', 'menuName')

