#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import django_filters
from django_filters.widgets import BooleanWidget

from common.models import User, SHARE_STATUS_CHOICES, Orders, OrderDetail, GOODS_TYPE_CHOICES, Withdrawal


class CourseRepreslFilter(django_filters.FilterSet):
    tel = django_filters.CharFilter(lookup_expr="icontains")
    nickName = django_filters.CharFilter(lookup_expr="icontains")
    shareStatus = django_filters.ChoiceFilter(choices=SHARE_STATUS_CHOICES)  # 分销权限
    isShopper = django_filters.BooleanFilter("isShopper", widget=BooleanWidget())

    class Meta:
        model = User
        fields = ()

class OrderBasicFilter(django_filters.FilterSet):
    # shareUuid
    shareUserUuid = django_filters.CharFilter(method='filter_by_shareUuid') # 分享人的uuid

    def filter_by_shareUuid(self, queryset, name, value):
        return queryset.filter(orderUuid__shareUserUuid__uuid__exact=value)

    class Meta:
        model = OrderDetail
        fields = ()


class OrderBasic2Filter(django_filters.FilterSet):
    goodsName = django_filters.CharFilter("goodsName", lookup_expr='icontains')                     # 课程名称
    detailNum = django_filters.CharFilter(lookup_expr='icontains')                                  # 订单编号
    tel = django_filters.CharFilter(method='filter_by_tel')                                         # 课代表电话
    userNum = django_filters.NumberFilter(method='filter_by_userNum')                               # 课代表id
    nickName = django_filters.CharFilter(method='filter_by_nickName')                               # 课代表昵称
    shareMoneyStatus = django_filters.CharFilter(method='filter_by_shareMoneyStatus')               # 结算状态
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")

    def filter_by_tel(self, queryset, name, value):
        return queryset.filter(orderUuid__shareUserUuid__tel__icontains=value)

    def filter_by_userNum(self, queryset, name, value):
        return queryset.filter(orderUuid__shareUserUuid__userNum=value)

    def filter_by_nickName(self, queryset, name, value):
        return queryset.filter(orderUuid__shareUserUuid__nickName=value)

    def filter_by_shareMoneyStatus(self, queryset, name, value):
        return queryset.filter(orderUuid__shareMoneyStatus=value)

    class Meta:
        model = OrderDetail
        fields = ("goodsType", )


class WithdrawalFilter(django_filters.FilterSet):
    tel = django_filters.CharFilter(method='filter_by_tel')  # 课代表电话
    nickName = django_filters.CharFilter(method='filter_by_nickName')  # 课代表昵称
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")

    def filter_by_tel(self, queryset, name, value):
        return queryset.filter(userUuid__tel__icontains=value)

    def filter_by_nickName(self, queryset, name, value):
        return queryset.filter( userUuid__nickName__icontains=value)

    class Meta:
        model = Withdrawal
        fields = ()



