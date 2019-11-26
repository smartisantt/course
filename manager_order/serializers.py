#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from django.db import transaction
from rest_framework import serializers
from datetime import datetime

from client.clientCommon import get_orderNO
from common.models import Orders, OrderDetail, User, Payment, UserMember, Refund, RefundOperation, \
    REFUND_MONEY_CHECK_CHOICES, WxEnterprisePaymentToWallet

# 订单列表
from utils.errors import ParamError
from utils.funcTools import timeStamp2dateTime, get_ip_address
from utils.wechatPay2User import enterprise_payment_to_wallet, MCHID, APPID, wx_refund


class RefundOperationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RefundOperation
        exclude = ("refundUuid", "uuid", "updateTime")


class RefundSimpleSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()

    @staticmethod
    def get_creator(obj):
        if obj.creatorUuid:
            return obj.creatorUuid.nickName

    @staticmethod
    def get_receiver(obj):
        if obj.receiverUuid:
            return obj.receiverUuid.nickName

    class Meta:
        model = Refund
        fields = ("refundNum", "refundMoney", "refundMoneyStatus", "createTime", "refundReason",
                  "receiver", "creator")


class OrderDetailSerializer(serializers.ModelSerializer):
    orderInfo = serializers.SerializerMethodField()
    buyerInfo = serializers.SerializerMethodField()
    refundInfo = serializers.SerializerMethodField()
    refundOperationInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_refundInfo(obj):
        refund = Refund.objects.filter(orderDetailUuid_id=obj.uuid).first()
        # if obj.refundOrderDetailUuid:
        if refund:
            return RefundSimpleSerializer(refund).data
        return
        # return None


    @staticmethod
    def get_refundOperationInfo(obj):
        # oderdetail -> order -> refund -> refundoperation
        refund = Refund.objects.filter(orderDetailUuid=obj).first()
        if refund:
            refundOperations = RefundOperation.objects.filter(refundUuid=refund).order_by("createTime")
            return RefundOperationSerializer(refundOperations, many=True).data
        return []


    @staticmethod
    def get_orderInfo(obj):
        if obj.orderUuid:
            return OrderInfoSerializer(obj.orderUuid).data
        res = {
          "uuid": None,
          "payStatus": None,
          "payInfo": {
            "payWayName": None,
            "payType": None,
            "usedPoints": None,
            "payTime": None
          },
          "shareUserUuid": None,
          "shareMoney": None,
          "shareMoneyStatus": None
        }
        return res

    @staticmethod
    def get_buyerInfo(obj):
        try:
            return BuyerInfoSerializer(obj.orderUuid.userUuid).data
        except Exception:
            res = {
                    "uuid": None,
                    "nickName": None,
                    "avatar": None,
                    "tel": None,
                    "status": None,
                    "registerPlatform": None,
                    "remark": None,
                    "vipInfo": {
                        "isVip": None,
                        "msg": None
                    },
                    "isShopper": None
                }
            return res

    class Meta:
        model = OrderDetail
        exclude = ("orderUuid", "updateTime", "goodsUuid", "o_product_id")


# 父订单信息
class OrderInfoSerializer(serializers.ModelSerializer):
    payInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_payInfo(obj):
        queryset = Payment.objects.filter(orderNum_id=obj.orderNum).first()
        if queryset:
            return PayInfoSerializer(queryset).data

    class Meta:
        model = Orders
        fields = ("uuid", "payStatus", "payInfo", "shareUserUuid", "shareMoney", "shareMoneyStatus")


# 支付信息
class PayInfoSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['payTime']:
            # 时间戳转datetime
            data['payTime'] = timeStamp2dateTime(data['payTime'])
        return data

    class Meta:
        model = Payment
        fields = ("payWayName", "payType", "usedPoints", "payTime")


# 购买人信息
class BuyerInfoSerializer(serializers.ModelSerializer):
    # 会员信息，连表查询 查询是否有会员信息， 会员到期时间是否已过期
    vipInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_vipInfo(user):
        # 肯能有多条会员记录，取最近一次的到期时间的会员记录判断时间
        res = UserMember.objects.filter(userUuid_id=user.uuid).order_by("-endTime").first()
        if not res:
            return {"isVip": False, "msg": "暂无会员信息"}
        elif timeStamp2dateTime(res.endTime).date() < datetime.now().date():
            return {"isVip": False, "msg": "会员已过期"}
        else:
            # 毫秒时间戳转字符串时间
            timeArray = time.localtime(int(res.endTime / 1000))
            otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
            return {"isVip": True, "msg": otherStyleTime + "到期"}

    class Meta:
        model = User
        fields = ("uuid", "nickName", "avatar", "tel",
                  "status", "registerPlatform", "remark", "vipInfo", "isShopper")


class OrderDetailBasicSerializer(serializers.ModelSerializer):
    rewardStatus = serializers.SerializerMethodField()

    @staticmethod
    def get_rewardStatus(obj):
        try:
            return obj.goodsUuid.rewardStatus
        except Exception:
            return

    class Meta:
        model = OrderDetail
        exclude = ("orderUuid", "updateTime", "goodsUuid", "o_product_id", "couponPrice")


# 退款操作记录
class RefundOperationBasicSerializer(serializers.ModelSerializer):
    operationUser = serializers.SerializerMethodField()

    @staticmethod
    def get_operationUser(obj):
        return obj.adminUserUuid.nickName

    class Meta:
        model = RefundOperation
        exclude = ("adminUserUuid", "updateTime", "refundUuid")


# 退款列表
class RefundBasicSerializer(serializers.ModelSerializer):
    buyerName = serializers.SerializerMethodField()
    buyerAvatar = serializers.SerializerMethodField()
    payPrice = serializers.SerializerMethodField()
    goodsPrice = serializers.SerializerMethodField()
    orderNum = serializers.SerializerMethodField()

    @staticmethod
    def get_buyerName(obj):
        try:
            return obj.orderDetailUuid.orderUuid.userUuid.nickName
        except Exception:
            return

    @staticmethod
    def get_buyerAvatar(obj):
        try:
            return obj.orderDetailUuid.orderUuid.userUuid.avatar
        except Exception:
            return

    @staticmethod
    def get_orderNum(obj):
        try:
            return obj.orderDetailUuid.detailNum
        except Exception:
            return

    @staticmethod
    def get_payPrice(obj):
        try:
            return obj.orderDetailUuid.payPrice
        except Exception:
            return

    @staticmethod
    def get_goodsPrice(obj):
        try:
            return obj.orderDetailUuid.goodsPrice
        except Exception:
            return

    class Meta:
        model = Refund
        exclude = ("creatorUuid", "updateTime", "receiverUuid", "orderDetailUuid")


class RefundPostSerializer(serializers.Serializer):
    # 退款金额
    refundMoney = serializers.IntegerField(min_value=0, required=True,
                                           error_messages={"required": "退款金额必填", "min_value": "退款金额不能小于0"})
    # 退款备注
    refundReason = serializers.CharField(max_length=255, required=False,
                                         error_messages={"max_length": "退款原因不要超过255个字符"})

    orderDetailUuid = serializers.PrimaryKeyRelatedField(queryset=OrderDetail.objects.all(),
                                                         required=True,
                                                         error_messages={
                                                            'required': "子订单uuid必填", "does_not_exist": "子订单不存在"
                                                         })

    def validate(self, attrs):
        # 通过子订单 -》 判断实际退款金额是否合法
        if Refund.objects.filter(orderDetailUuid=attrs["orderDetailUuid"], refundMoneyStatus__in=[1, 2]).exists():
            raise ParamError("此订单正在退款或退款成功。")
        if attrs["orderDetailUuid"].payPrice < attrs["refundMoney"]:
            raise ParamError("超出退款金额{}元".format(attrs["orderDetailUuid"].payPrice/100))
        return attrs

    def createRefund(self, validated_data, request):
        # validated_data["orderDetailUuid_id"] = validated_data.pop("orderDetailUuid")
        refund = Refund.objects.filter(orderDetailUuid=validated_data["orderDetailUuid"]).first()
        # 如果之前有退款是被关闭或者取消 再次发起退款
        if refund:
            refund.refundMoneyStatus = 1
            refund.refundMoney = validated_data["refundMoney"]*100   # 元 变 分
            refund.refundReason = validated_data["refundReason"]
            refund.creatorUuid = request.user
            refund.save()
            # 退款记录表
            RefundOperation.objects.create(
                adminUserUuid=request.user,
                refundMoneyStatus=1,
                refundUuid=refund,
                operation="{0}取消退款".format(request.user.nickName),
                remark=validated_data["refundReason"]
            )
            return True
        # 如果之前都没有退款
        validated_data["creatorUuid"] = request.user
        validated_data["refundMoneyWay"] = 3                    # 目前只有微信退款
        validated_data["refundNum"] = get_orderNO()
        refund = Refund.objects.create(**validated_data)

        # 退款记录表
        RefundOperation.objects.create(
            adminUserUuid=request.user,
            refundMoneyStatus=1,
            refundUuid=refund,
            operation="{0}取消退款".format(request.user.nickName),
            remark=validated_data["refundReason"]
        )
        return True


class OrderInfo2Serializer(serializers.ModelSerializer):
    payInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_payInfo(obj):
        queryset = Payment.objects.filter(orderNum_id=obj.orderNum).first()
        if queryset:
            return PayInfoSerializer(queryset).data

    class Meta:
        model = Orders
        fields = ("uuid", "payStatus", "payInfo", "shareUserUuid",
                  "shareMoney", "shareMoneyStatus", "payAmount")


# 退款详情
class RefundDetailSerializer(serializers.ModelSerializer):
    orderInfo = serializers.SerializerMethodField()
    buyerInfo = serializers.SerializerMethodField()
    orderDetailInfo = serializers.SerializerMethodField()
    refundOperationInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_orderInfo(obj):
        try:
            return OrderInfo2Serializer(obj.orderDetailUuid.orderUuid).data
        except Exception:
            return

    @staticmethod
    def get_refundOperationInfo(obj):
        try:
            queryset = RefundOperation.objects.filter(refundUuid_id=obj.uuid).order_by("createTime")
            return RefundOperationBasicSerializer(queryset, many=True).data

        except Exception:
            return

    @staticmethod
    def get_buyerInfo(obj):
        try:
            return BuyerInfoSerializer(obj.orderDetailUuid.orderUuid.userUuid).data
        except Exception:
            return

    @staticmethod
    def get_orderDetailInfo(obj):
        try:
            return OrderDetailBasicSerializer(obj.orderDetailUuid).data
        except Exception:
            return

    class Meta:
        model = Refund
        exclude = ("creatorUuid", "updateTime", "receiverUuid", "orderDetailUuid")


class RefundUpdateSerializer(serializers.Serializer):
    refundMoneyStatus = serializers.ChoiceField(choices=REFUND_MONEY_CHECK_CHOICES, required=True,
                                                error_messages={"required": "退款状态必填"})  # 栏目类型
    remark = serializers.CharField(required=False, max_length=1024, error_messages={"max_length": "超出字数限制"})

    @transaction.atomic
    def updateRefund(self, instance, validated_data, request):
        # 财务通过审核  修改退款表的状态， 微信支付流水表
        if instance.refundMoneyWay == 3 and validated_data["refundMoneyStatus"] == 2:
            dataInfo = {
                "orderNo": instance.orderDetailUuid.orderUuid.orderNum,         # 商户系统内部订单号 完成的订单查询
                "out_refund_no": instance.refundNum,                            # 商户系统内部的退款单号
                "total_fee": instance.orderDetailUuid.orderUuid.payAmount,      # 总共支付金额
                "refund_fee": instance.refundMoney,                             # 退款金额
                "refund_desc": "商品退款"                                        # 退款原因
            }
            res, msg = wx_refund(dataInfo)
            if not res:
                raise ParamError(msg)
            # 微信退款成功

        instance.refundMoneyStatus = validated_data.get("refundMoneyStatus")
        instance.remark = validated_data.get("remark", "")

        # 操作记录表
        if validated_data.get("refundMoneyStatus") == 2:
            instance.receiverUuid = request.user
            msg = "{0}受理反馈，退款成功。".format(request.user.nickName)
        else:
            msg = "{0}受理反馈，暂不受理。".format(request.user.nickName)
        instance.save()
        RefundOperation.objects.create(
            adminUserUuid=request.user,
            refundMoneyStatus=validated_data.get("refundMoneyStatus"),
            refundUuid=instance,
            operation=msg,
            remark=validated_data.get("remark", "")
        )
        return True








