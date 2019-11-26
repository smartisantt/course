#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import transaction
from pip._internal.utils import logging

from rest_framework import serializers
from public.models import ChinaArea


class AreaSerializer4(serializers.ModelSerializer):
    """地区序列化"""
    label = serializers.CharField(source="name")
    value = serializers.CharField(source="uuid")

    class Meta:
        model = ChinaArea
        fields = ("label", "value")


class AreaSerializer3(serializers.ModelSerializer):
    """地区序列化"""
    label = serializers.CharField(source="name")
    value = serializers.CharField(source="uuid")
    children = AreaSerializer4(many=True)

    class Meta:
        model = ChinaArea
        fields = ("label", "value", "children")


class AreaSerializer2(serializers.ModelSerializer):
    """地区序列化"""
    label = serializers.CharField(source="name")
    value = serializers.CharField(source="uuid")
    children = AreaSerializer3(many=True)

    class Meta:
        model = ChinaArea
        fields = ("label", "value", "children")


class AreaSerializer(serializers.ModelSerializer):
    """地区序列化"""
    label = serializers.CharField(source="name")
    value = serializers.CharField(source="uuid")
    children = AreaSerializer2(many=True)

    class Meta:
        model = ChinaArea
        fields = ("label", "value", "children")


class AreaPostSerializer(serializers.Serializer):
    """提交校验"""
    name = serializers.CharField(max_length=64, required=False)
    level = serializers.CharField(max_length=32, required=False)
    adcode = serializers.CharField(max_length=32, required=False)
    center = serializers.CharField(max_length=32, required=False)
    status = serializers.CharField(max_length=32, required=False)
    districts = serializers.ListField(required=False)

    def create_area(self, validated_data):
        """存储地区信息"""
        province_list = validated_data.pop("districts")
        provinces = []
        for province_data in province_list:
            city_list = province_data.pop("districts")
            del province_data["citycode"]
            cities = []
            for city_data in city_list:
                district_list = city_data.pop("districts")
                del city_data["citycode"]
                districties = []
                for district_data in district_list:
                    del district_data["districts"]
                    del district_data["citycode"]
                    districties.append(ChinaArea.objects.create(**district_data))
                cit = ChinaArea.objects.create(**city_data)
                if len(districties) > 0:
                    cit.children.add(*districties)
                cities.append(cit)
            pro = ChinaArea.objects.create(**province_data)
            if len(cities):
                pro.children.add(*cities)
            provinces.append(pro)
        china = ChinaArea.objects.create(**validated_data)
        china.children.add(*provinces)
        res = {
            'china': AreaSerializer(china).data
        }
        return res
