#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.
from common.models import BaseModel


class ChinaArea(BaseModel):
    """
    中国省市区（县）列表
    数据来源于高德地图
    """
    parentUuid = models.ForeignKey('self', on_delete=models.CASCADE, to_field='uuid', related_name="children",
                                   null=True, default=None)
    level = models.CharField(max_length=32, verbose_name="级别")
    adcode = models.CharField(max_length=32, verbose_name="区域代码")
    name = models.CharField(max_length=64, verbose_name="区域名")
    center = models.CharField(max_length=32, verbose_name="中心点")
    status = models.CharField(max_length=32, default='normal')

    class Meta:
        db_table = "tb_china_area"