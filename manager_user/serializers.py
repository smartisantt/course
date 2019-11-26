#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from rest_framework import serializers

from common.models import User, UserMember, USER_MODIFY_STATUS_CHOICES
from datetime import datetime
from utils.funcTools import timeStamp2dateTime



class UserBasicSerializer(serializers.ModelSerializer):
    # 会员信息，连表查询 查询是否有会员信息， 会员到期时间是否已过期
    vipInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_vipInfo(user):
        # 肯能有多条会员记录，取最近一次的到期时间的会员记录判断时间
        res = UserMember.objects.filter(userUuid_id=user.uuid).order_by("-endTime").first()
        if not res:
            return {"isVip": False, "msg": "暂无会员信息"}
        elif timeStamp2dateTime(res.endTime).date() < datetime.now().date() :
            return {"isVip": False, "msg": "会员已过期"}
        else:
            # 毫秒时间戳转字符串时间
            timeArray = time.localtime(int(res.endTime/1000))
            otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
            return {"isVip": True, "msg": otherStyleTime+"到期"}

    class Meta:
        model = User
        fields = ('uuid', 'userNum', 'nickName', 'avatar',
                  'createTime', 'tel', 'gender', 'status',
                  'avatar', 'managerStatus', 'remark', 'vipInfo')


class UserUpdateSerializer(serializers.Serializer):
    # remark = serializers.CharField(max_length=1024, required=False,
    #                                error_messages={
    #                                    'max_length': '备注长度不要大于1024个字符'
    #                                })

    status = serializers.ChoiceField(choices=USER_MODIFY_STATUS_CHOICES, required=True,
                                     error_messages={'required': "用户状态必填"})


    def update_user(self, instance, validate_data):
        instance.status = validate_data.get('status')
        instance.save()
        res = {
            'user': UserBasicSerializer(instance).data
        }
        return res







