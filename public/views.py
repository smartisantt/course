#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from rest_framework.response import Response
from rest_framework import viewsets, mixins

from client.views import BasePermissionModel
from public.areaAPI import Area
from public.models import ChinaArea
from public.serializers import AreaSerializer, AreaPostSerializer
from utils.errors import ParamError, APIQueryError
from utils.msg import API_QUERY_ERROR, POST_SUCCESS


class AreaView(BasePermissionModel,
               viewsets.GenericViewSet,
               mixins.CreateModelMixin,
               mixins.ListModelMixin,
               mixins.RetrieveModelMixin):
    """地区接口"""

    queryset = ChinaArea.objects.filter(adcode="100000").prefetch_related('parentUuid')
    serializer_class = AreaSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """增加"""
        area = Area()
        area_data = area.get_data()
        if not area_data:
            raise APIQueryError(API_QUERY_ERROR)
        serializers_data = AreaPostSerializer(data=area_data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError({'code': 400, 'msg': list(serializers_data.errors.values())[0][0]})
        serializers_data.create_area(serializers_data.data)

        return Response(POST_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(API_QUERY_ERROR)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
