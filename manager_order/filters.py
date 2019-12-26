#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import django_filters

from common.models import OrderDetail, PAY_STATUS_CHOICES, Refund


class OrderDetailFilter(django_filters.FilterSet):
    detailNum = django_filters.CharFilter(lookup_expr="icontains")
    goodsName = django_filters.CharFilter(lookup_expr="icontains")
    buyerName = django_filters.CharFilter(method='filter_by_buyerName')         # 购买人昵称
    buyerUuid = django_filters.CharFilter(method='filter_by_userUuid')          # 购买人的uuid
    shareUserUuid = django_filters.CharFilter(method='filter_by_shareUuid')     # 分享人的uuid
    payStatus = django_filters.NumberFilter(method='filter_by_payStatus')       # 支付状态
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")         # searchTime_before   searchTime_after

    def filter_by_buyerName(self, queryset, name, value):
        return queryset.filter(orderUuid__userUuid__nickName__icontains=value)

    def filter_by_userUuid(self, queryset, name, value):
        return queryset.filter(orderUuid__userUuid__uuid__exact=value)

    def filter_by_shareUuid(self, queryset, name, value):
        return queryset.filter(orderUuid__shareUserUuid__uuid__exact=value)

    # orderDetail -> order ->  Payment
    def filter_by_payStatus(self, queryset, name, value):
        return queryset.filter(orderUuid__payStatus=value)

    class Meta:
        model = OrderDetail
        fields = ()


class RefundFilter(django_filters.FilterSet):
    detailNum = django_filters.CharFilter(method='filter_by_detailNum')          # 订单编号
    buyerName = django_filters.CharFilter(method='filter_by_buyerName')          # 购买人名字

    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")     # searchTime_before   searchTime_after

    def filter_by_detailNum(self, queryset, name, value):
        return queryset.filter(orderDetailUuid__detailNum__icontains=value)

    def filter_by_buyerName(self, queryset, name, value):
        # return queryset.filter(orderUuid__buyerName__icontains=value)
        return queryset.filter(orderDetailUuid__orderUuid__userUuid__nickName__icontains=value)

    class Meta:
        model = Refund
        fields = ("refundMoneyStatus", )