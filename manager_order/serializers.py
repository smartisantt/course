#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from django.db import transaction
from rest_framework import serializers
from datetime import datetime

from client.clientCommon import get_orderNO
from client.models import Behavior
from common.models import Orders, OrderDetail, User, Payment, UserMember, Refund, RefundOperation, \
    REFUND_MONEY_CHECK_CHOICES, WxEnterprisePaymentToWallet, UserCoupons

# 订单列表
from utils.errors import ParamError
from utils.funcTools import timeStamp2dateTime, get_ip_address
from utils.timeTools import timeChange
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
        fields = ("uuid", "payStatus", "payInfo", "shareUserUuid", "shareMoney",
                  "shareMoneyStatus")


# 支付信息
class PayInfoSerializer(serializers.ModelSerializer):
    payTime = serializers.SerializerMethodField()

    @staticmethod
    def get_payTime(obj):
        try:
            # 秒时间戳转 datetime
            return timeChange(obj.payTime, 1)
        except Exception:
            return

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
        exclude = ("orderUuid", "updateTime", "goodsUuid", "o_product_id")


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
    # 退款金额， 前端传的是元  注意：655.17*100 不等于65517 应该这样处理：int(655.17*100+0.5)  一次最多退500
    refundMoney = serializers.DecimalField(min_value=0, required=True, decimal_places=2, max_digits=5,
                                           error_messages={"required": "退款金额必填", "min_value": "退款金额不能小于0"})
    # 退款备注
    refundReason = serializers.CharField(max_length=255, required=False,
                                         error_messages={"max_length": "退款原因不要超过255个字符"})
    # 订单的状态需要是已支付状态且没有发生退款 才可以退款
    orderDetailUuid = serializers.PrimaryKeyRelatedField(queryset=OrderDetail.objects.filter(orderUuid__payStatus=2),
                                                         required=True,
                                                         error_messages={
                                                             'required': "子订单uuid必填", "does_not_exist": "子订单不存在或无法退款"
                                                         })

    def validate(self, attrs):
        # 如果在此之前已经申请过退款， 且退款状态是在退款中或退款成功则返回。
        if Refund.objects.filter(orderDetailUuid=attrs["orderDetailUuid"], refundMoneyStatus__in=[1, 2]).exists():
            raise ParamError("此订单正在退款或退款成功。")
        # 校验退款金额是否合法
        if attrs["orderDetailUuid"].payPrice < int(float(attrs["refundMoney"]) * 100 + 0.5):
            raise ParamError("订单付款款金额{}元，退款金额已超出。".format(attrs["orderDetailUuid"].payPrice / 100))
        return attrs

    def createRefund(self, validated_data, request):
        # validated_data["orderDetailUuid_id"] = validated_data.pop("orderDetailUuid")
        refund = Refund.objects.filter(orderDetailUuid=validated_data["orderDetailUuid"]).first()
        # 如果之前有退款是被关闭或者取消 再次发起退款
        if refund:
            refund.refundMoneyStatus = 1
            refund.refundMoney = int(float(validated_data["refundMoney"]) * 100 + 0.5)  # 元变分
            refund.refundReason = validated_data["refundReason"]
            refund.creatorUuid = request.user
            refund.save()

            # orderdetail paystatus 改变成 退款中
            order = validated_data["orderDetailUuid"].orderUuid
            order.payStatus = 3
            order.save()

            # 退款记录表
            RefundOperation.objects.create(
                adminUserUuid=request.user,
                refundMoneyStatus=1,
                refundUuid=refund,
                operation="{0}[{1}]提交退款申请。".format(request.user.nickName, request.user.tel),
                remark=validated_data["refundReason"]
            )
            return True
        # 如果之前都没有退款
        validated_data["creatorUuid"] = request.user
        validated_data["refundMoney"] = int(float(validated_data["refundMoney"]) * 100 + 0.5)
        validated_data["refundMoneyWay"] = 3  # 目前只有微信退款
        validated_data["refundNum"] = get_orderNO()
        refund = Refund.objects.create(**validated_data)

        # orderdetail paystatus 改变成 退款中
        order = validated_data["orderDetailUuid"].orderUuid
        order.payStatus = 3
        order.save()

        # 退款记录表
        RefundOperation.objects.create(
            adminUserUuid=request.user,
            refundMoneyStatus=1,
            refundUuid=refund,
            operation="{0}[{1}]提交退款申请。".format(request.user.nickName, request.user.tel),
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
            # 校验参数
            try:
                orderNum = instance.orderDetailUuid.orderUuid.orderNum
                if not orderNum:
                    raise ParamError("没有订单编号")
            except Exception as e:
                raise ParamError("没有订单编号")

            try:
                payAmount = instance.orderDetailUuid.orderUuid.payAmount
                if not payAmount:
                    raise ParamError("没有订单实际支付金额")
            except Exception as e:
                raise ParamError("没有订单实际支付金额")

            if instance.refundMoney > payAmount:
                raise ParamError("退款金额超出付款金额")

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

            # 微信退款成功， 修改order 里的payStatus的状态 变为4   如果有分销，如果是未结算状态，则需要改变分销状态4 取消分销
            orderDetail = instance.orderDetailUuid
            order = orderDetail.orderUuid
            if order.shareMoneyStatus == 2:
                order.shareMoneyStatus = 4
            order.payStatus = 4
            order.save()

            # 退款成功修改，修改 删除Behavior中type=5  courseUuid
            behavior = Behavior.objects.filter(
                behaviorType=5,
                courseUuid_id=orderDetail.goodsUuid.content,
                userUuid=orderDetail.orderUuid.userUuid).first()
            behavior.isDelete = True
            behavior.save()

            # 微信退款成功，修改 用户已领取优惠券状态
            if order.couponUuid:
                UserCoupons.objects.filter(uuid__in=order.couponUuid.split(",")).update(
                    status=1, updateTime=datetime.now()
                )

        else:
            # 拒绝退款， 修改order 里的payStatus的状态 变为2 支付成功
            orderDetail = instance.orderDetailUuid
            order = orderDetail.orderUuid
            order.payStatus = 2
            order.save()

        instance.refundMoneyStatus = validated_data.get("refundMoneyStatus")
        instance.remark = validated_data.get("remark", "")

        # 操作记录表
        if validated_data.get("refundMoneyStatus") == 2:
            instance.receiverUuid = request.user
            msg = "{0}[{1}]受理业务，退款成功。".format(request.user.nickName, request.user.tel)
        else:
            msg = "{0}[{1}]受理业务，拒绝退款。".format(request.user.nickName, request.user.tel)
        instance.save()
        RefundOperation.objects.create(
            adminUserUuid=request.user,
            refundMoneyStatus=validated_data.get("refundMoneyStatus"),
            refundUuid=instance,
            operation=msg,
            remark=validated_data.get("remark", "")
        )
        return True
