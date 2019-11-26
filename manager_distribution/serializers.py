#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from django.db import transaction
from django.db.models import Count, Q, Sum
from rest_framework import serializers
from datetime import datetime

from common.models import Orders, OrderDetail, User, Payment, UserMember, Withdrawal, WITHDRAWAL_MONEY_CHECK_CHOICES, \
    WxEnterprisePaymentToWallet, Bill

# 订单列表
from utils.errors import ParamError
from utils.funcTools import timeStamp2dateTime, get_ip_address
from utils.qFilter import PAY_STATUS_Q, SHARE_MONEY_STATUS_Q, SHARE_MONEY_STATUS_Q2
from utils.wechatPay2User import enterprise_payment_to_wallet, APPID, MCHID


class CourseRepresSerializer(serializers.ModelSerializer):
    distributionNum = serializers.SerializerMethodField()      # 分销人数
    orderNum = serializers.SerializerMethodField()
    firstTime = serializers.SerializerMethodField()            # 首次分销成功时间
    totalMoney = serializers.SerializerMethodField()           # 累计分销收入
    income = serializers.SerializerMethodField()               # 已结算


    @staticmethod
    def get_distributionNum(user):
        # A分销人数 分销出去成功购买（支付成功，没有退款）人数 （不含A自己购买）
        return Orders.objects.filter(Q(shareUserUuid=user)&PAY_STATUS_Q).exclude(userUuid=user).\
            values('userUuid_id').annotate(Count('userUuid_id', distinct=True)).count()

    @staticmethod
    def get_orderNum(user):
        # A分订单数 分销出去成功购买（支付成功，没有退款）订单数 （不含A自己购买）
        return Orders.objects.filter(Q(shareUserUuid=user) & PAY_STATUS_Q).exclude(userUuid=user).count()

    @staticmethod
    def get_firstTime(user):
        # A首次分销成功订单时间    分销出去成功购买（支付成功，没有退款）（不含A自己购买）
        order = Orders.objects.filter(Q(shareUserUuid=user) & PAY_STATUS_Q).order_by("createTime").first()
        if order:
            return order.createTime

    @staticmethod
    def get_totalMoney(user):
        # A分销提成累计分销收入
        order = Orders.objects.filter(Q(shareUserUuid=user) & PAY_STATUS_Q & SHARE_MONEY_STATUS_Q).\
            aggregate(nums=Sum('shareMoney'))
        return order['nums']

    @staticmethod
    def get_income(user):
        # A分销已结算的金额
        order = Orders.objects.filter(Q(shareUserUuid=user) & PAY_STATUS_Q & SHARE_MONEY_STATUS_Q2).\
            aggregate(nums=Sum('shareMoney'))
        return order['nums'] or 0

    class Meta:
        model = User
        fields = ("uuid", "nickName", "userNum", "tel", "avatar", "firstTime", "totalMoney", "income",
                  "isShopper", "shareStatus", "distributionNum", "orderNum")


#
class OrderBasicSerializer(serializers.ModelSerializer):
    orderTime = serializers.SerializerMethodField()                     # 交易时间
    nickName = serializers.SerializerMethodField()                      # 买家昵称
    avatar = serializers.SerializerMethodField()                        # 买家头像
    shareMoneyStatus = serializers.SerializerMethodField()              # 交易状态


    @staticmethod
    def get_orderTime(orderDetail):
        try:
            return orderDetail.orderUuid.createTime
        except Exception:
            return

    @staticmethod
    def get_avatar(orderDetail):
        try:
            return orderDetail.orderUuid.userUuid.avatar
        except Exception:
            return

    @staticmethod
    def get_nickName(orderDetail):
        try:
            return orderDetail.orderUuid.userUuid.nickName
        except Exception:
            return

    @staticmethod
    def get_shareMoneyStatus(orderDetail):
        try:
            return orderDetail.orderUuid.shareMoneyStatus
        except Exception:
            return


    class Meta:
        model = OrderDetail
        fields = ("uuid","shareMoney", "goodsName", "orderTime",
                  "nickName", "avatar", "shareMoneyStatus")



class OrderBasic2Serializer(serializers.ModelSerializer):
    goodsName = serializers.SerializerMethodField()
    orderTime = serializers.CharField(source="createTime")             # 交易时间
    courseRepreInfo = serializers.SerializerMethodField()               # 课代表信息
    shareMoneyStatus = serializers.SerializerMethodField()              # 结算状态
    goodsPrice = serializers.SerializerMethodField()              # 订单金额 商品的真实价格

    @staticmethod
    def get_goodsPrice(orderDetail):
        try:
            # return orderDetail.goodsUuid.realPrice            # 单个商品的实际价格（不减优惠卷的金额）
            return orderDetail.orderUuid.payAmount              # 父订单实际支付总金额
        except Exception:
            return


    @staticmethod
    def get_goodsName(orderDetail):
        try:
            return orderDetail.goodsUuid.name
        except Exception:
            return

    @staticmethod
    def get_courseRepreInfo(orderDetail):
        try:
            avatar = orderDetail.orderUuid.shareUserUuid.avatar
            nickName = orderDetail.orderUuid.shareUserUuid.nickName
            tel = orderDetail.orderUuid.shareUserUuid.tel
            userNum = orderDetail.orderUuid.shareUserUuid.userNum
            return {"avatar": avatar, "nickName": nickName, "tel": tel, "userNum": userNum}
        except Exception:
            return

    @staticmethod
    def get_shareMoneyStatus(orderDetail):
        try:
            return orderDetail.orderUuid.shareMoneyStatus
        except Exception:
            return


    class Meta:
        model = OrderDetail
        fields = ("uuid", "shareMoney", "goodsPrice", "goodsName", "orderTime", "goodsType", "detailNum",
                  "courseRepreInfo", "shareMoneyStatus")


class WithdrawalSerializer(serializers.ModelSerializer):
    courseRepreInfo = serializers.SerializerMethodField()           # 课代表信息
    withdrawalStatus = serializers.SerializerMethodField()          # 提现状态
    enableMoney = serializers.SerializerMethodField()               # 可提现余额
    totalMoney = serializers.SerializerMethodField()                # 累计分销收入
    income = serializers.SerializerMethodField()                    # 已结算
    idCard = serializers.SerializerMethodField()                    # 身份证号
    realName = serializers.SerializerMethodField()                  # 真实姓名

    @staticmethod
    def get_idCard(withdrawal):
        try:
            return withdrawal.userUuid.idCard
        except Exception:
            return

    @staticmethod
    def get_realName(withdrawal):
        try:
            return withdrawal.userUuid.realName
        except Exception:
            return

    @staticmethod
    def get_enableMoney(withdrawal):
        return withdrawal.userUuid.banlance

    @staticmethod
    def get_withdrawalStatus(withdrawal):
        # 如果是转账失败也显示未通过
        if withdrawal.withdrawalStatus == 4:
            return 3
        return withdrawal.withdrawalStatus

    @staticmethod
    def get_totalMoney(withdrawal):
        # A分销提成累计分销收入
        order = Orders.objects.filter(Q(shareUserUuid=withdrawal.userUuid) & PAY_STATUS_Q & SHARE_MONEY_STATUS_Q).\
            aggregate(nums=Sum('shareMoney'))
        return order['nums']

    @staticmethod
    def get_income(withdrawal):
        # A分销已结算的金额
        order = Orders.objects.filter(Q(shareUserUuid=withdrawal.userUuid) & PAY_STATUS_Q & SHARE_MONEY_STATUS_Q2).\
            aggregate(nums=Sum('shareMoney'))
        return order['nums'] or 0

    @staticmethod
    def get_courseRepreInfo(withdrawal):
        try:
            avatar = withdrawal.userUuid.avatar
            nickName = withdrawal.userUuid.nickName
            tel = withdrawal.userUuid.tel
            userNum = withdrawal.userUuid.userNum
            isShopper = withdrawal.userUuid.isShopper
            return {"avatar": avatar, "nickName": nickName, "tel": tel, "userNum": userNum,
                    "isShopper": isShopper}
        except Exception:
            return

    class Meta:
        model = Withdrawal
        exclude = ("updateTime", "billNum", "wxAccount", "userUuid")


# 财务审核提现
class WithdrawalUpdateSerializer(serializers.Serializer):
    withdrawalStatus = serializers.ChoiceField(choices=WITHDRAWAL_MONEY_CHECK_CHOICES, required=True,
                                               error_messages={"required": "提现状态必填"})
    remarks = serializers.CharField(required=False, max_length=1024, error_messages={"max_length": "超出字数限制"})

    @transaction.atomic
    def updateWithdrawal(self, instance, validated_data, request):
        # 微信付款给用户
        if instance.withdrawalType == 2 and validated_data.get("withdrawalStatus") == 2:
            dataInfo = {
                "device_info": request.user.uuid,               # 设备号， 这里可以存放 操作退款管理员的uuid
                "amount": instance.withdrawalMoney,             # 退款金额 单位分
                "desc": "好呗呗微信提现",                         # 退款备注
                "re_user_name": instance.userUuid.realName,              #
                "spbill_create_ip": get_ip_address(request),    # 操作的ip地址
                "partner_trade_no": instance.uuid,              # 商户订单号
                "openid": instance.wxAccount                    # 退款给用户的openid
            }
            wxboject = WxEnterprisePaymentToWallet.objects.create(
                mch_appid=APPID,
                mchid=MCHID,
                **dataInfo
            )
            res, msg = enterprise_payment_to_wallet(dataInfo)
            # 微信付款失败
            if not res:
                raise ParamError(msg)
            # 企业付款成功到零钱  -》 修改流水表
            Bill.objects.create(
                userUuid=instance.userUuid,                  # 打款给谁
                billType=2,
                remarks="提现支出",
                money=instance.withdrawalMoney,
            )
            wxboject.payment_time = msg["payment_time"]
            instance.arrivalAccountTime = msg["payment_time"]
            wxboject.remark = "提现成功"
            wxboject.payment_no = msg["payment_no"]
            wxboject.save()
            # 打款成功存表
        # 财务不同意
        if validated_data.get("withdrawalStatus") == 3:
            # 退回到余额
            user = User.objects.filter(uuid=instance.userUuid.uuid).first()
            user.banlance = user.banlance + instance.withdrawalMoney
            user.save()

        instance.withdrawalStatus = validated_data.get("withdrawalStatus")
        instance.remarks = validated_data.get("remarks", "")
        instance.save()

        return True










