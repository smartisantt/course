import logging
from datetime import datetime, timedelta

from django.contrib.auth.hashers import check_password
from django.core.cache import caches
from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from django.http import HttpResponse

from client.clientCommon import MyPageNumberPagination
from client.insertQuery import update_pay_course, update_pay_member, save_order, update_pay_zero_course
from client.models import Behavior
from client.queryFilter import qRangeCouponsUse
from client.serializers import BillsSerializer
from common.models import UserCoupons, Coupons, User, Orders, Goods, Withdrawal, Bill
from parentscourse_server.config import HOST_IP, ORDER_TIMEOUT
from utils.clientAuths import ClientAuthentication
from utils.clientPermission import ClientPermission
from utils.funcTools import http_return
from utils.wechatPay import trans_xml_to_dict, get_sign, trans_dict_to_xml, APIKEY, hbb_wx_pay_params, hbb_wx_pay_query
from client.tasks import checkOrder


class WXPayParams(APIView):
    """公众号端获取微信支付参数"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def post(self, request):
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        if not user.userWechatUuid.first():
            return http_return(400, "请绑定微信后购买")
        uuid = request.data.get("uuid", None)
        couponUuid = request.data.get("couponUuid", None)
        shareUuid = request.data.get("shareUuid", None)
        if not uuid:
            return http_return(400, "请选择购买商品")
        goods = Goods.objects.filter(uuid=uuid).first()
        if not goods:
            return http_return(400, "未获取到购买商品")
        behavior = Behavior.objects.filter(userUuid__uuid=request.user.get("uuid"), courseUuid__uuid=goods.content,
                                           behaviorType=5, isDelete=False).first()
        if behavior:
            return http_return(400, "你已购买过该课程")
        oldPrice = goods.realPrice
        price = oldPrice
        coupon = None
        if couponUuid and goods.isCoupon:
            coupon = UserCoupons.objects.filter(uuid=couponUuid, status=1).filter(qRangeCouponsUse).first()
            if not coupon:
                return http_return(400, "优惠券不可用")
            couponInfo = coupon.couponsUuid
            couponType = couponInfo.couponType
            if couponType == 1:
                price = oldPrice - couponInfo.money
            elif couponType == 2:
                scopeList = couponInfo.scope.split(",")
                if str(goods.goodsType) not in scopeList:
                    return http_return(400, "优惠券类型不符合课程类型")
                if couponInfo.accountMoney and couponInfo.accountMoney < float(oldPrice):
                    return http_return(400, "优惠券未达到满减要求")
                price = oldPrice - couponInfo.money
            elif couponType == 3:
                if couponInfo.accountMoney and couponInfo.accountMoney < float(oldPrice):
                    return http_return(400, "优惠券未达到满减要求")
                price = oldPrice - couponInfo.money
            try:
                Coupons.objects.filter(uuid=coupon.couponsUuid.uuid).update(usedNumber=F("usedNumber") + 1)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "更新优惠券使用数量失败")
        if price <= 0:
            return http_return(400, "价格错误")
        shareUser = User.objects.filter(uuid=shareUuid).first() if shareUuid else None
        if not goods:
            return http_return(400, "商品信息不存在")
        shareMoney = int(oldPrice * goods.rewardPercent / 1000) * 10 if shareUser and goods.rewardStatus else None
        order = save_order(user, shareUser, price, oldPrice, coupon, shareMoney, goods)
        if not order:
            return http_return(400, "订单存储失败")
        resData = caches['client'].get(order.uuid, None)
        if not resData:
            """统一下单"""
            dataInfo = {
                "body": goods.name,
                "orderNo": order.orderNum,
                "price": order.orderPrice,
                "userIP": HOST_IP,
                "goodsID": goods.uuid,
                "openid": user.userWechatUuid.first().openid,
                "device_info": goods.goodsType
            }
            data = hbb_wx_pay_params(dataInfo, request)
            if not data:
                return http_return(400, "下单失败")
            resData = {"payData": data, "uuid": order.uuid}
            try:
                caches['client'].set(order.uuid, resData, ORDER_TIMEOUT)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "服务器缓存错误")
        # 定时任务，半小时后如果订单未支付，则超时
        checkOrder.apply_async((order.uuid,), eta=datetime.utcnow() + timedelta(minutes=30))
        return http_return(200, "成功", resData)


class WXPayResult(APIView):
    """微信会异步回调"""
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request):
        data_dict = trans_xml_to_dict(request.body)
        sign = data_dict.pop('sign')
        back_sign = get_sign(data_dict, APIKEY)
        if sign == back_sign and data_dict['return_code'] == 'SUCCESS':
            try:
                deal_type = data_dict['device_info']
                if deal_type in [1, 2]:
                    if not update_pay_course(data_dict):
                        return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
                elif deal_type == 3:
                    if not update_pay_member(data_dict):
                        return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
                else:
                    return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
            except Exception as e:
                logging.error(str(e))
                return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
        return HttpResponse(trans_dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))


class WXPayQuery(APIView):
    """支付结果查询"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def get(self, request):
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要查看支付结果的订单")
        order = Orders.objects.filter(uuid=uuid).first()
        if not order:
            return http_return(400, "未查询到支付订单")
        if order.payStatus != 2:
            data_dict = hbb_wx_pay_query(order.orderNum)
            tradeState = data_dict.get('trade_state', None)
            if not tradeState:
                return http_return(400, "查询失败")
            deal_type = int(data_dict['device_info'])
            if tradeState == 'SUCCESS':
                try:
                    if deal_type in [1, 2]:
                        if not update_pay_course(data_dict):
                            return http_return(400, "更新订单信息失败")
                    elif deal_type == 3:
                        if not update_pay_member(data_dict):
                            return http_return(400, "更新会员信息失败")
                    else:
                        return http_return(400, "未知商品类型")
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, "更新支付结果失败")
            elif tradeState in ['REFUND', 'NOTPAY', 'CLOSED', 'REVOKED', 'USERPAYING', 'PAYERROR']:
                if deal_type in [1, 2]:
                    order.wxPayStatus = tradeState
                    if tradeState == "REFUND":
                        order.payStatus = 3
                    try:
                        order.save()
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, "更新支付结果失败")
                    returnDict = {
                        "REFUND": "退款中",
                        "NOTPAY": "未支付",
                        "CLOSED": "支付已关闭",
                        "REVOKED": "支付已撤销",
                        "USERPAYING": "用户支付中",
                        "PAYERROR": "支付失败"
                    }
                    return http_return(400, returnDict[tradeState])
                else:
                    return http_return(400, "未知错误")
        return http_return(200, "支付成功")


class CashRequest(APIView):
    """提现请求"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def post(self, request):
        """提现申请"""
        money = request.data.get("money", None)
        if not money:
            return http_return(400, "请输入提现金额")
        tradPwd = request.data.get("tradPwd", None)
        if not tradPwd:
            return http_return(400, "请输入提现密码")
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        if user.banlance < money:
            return http_return(400, "余额不足，无法提现")
        if money > 50000:
            return http_return(400, "提现金额超过限制")
        if money <= 0:
            return http_return(400, "提现金额不能小于零")
        if not check_password(tradPwd, user.tradePwd):
            return http_return(400, "提现密码错误")
        if not all([user.realName, user.idCard, user.tradePwd]):
            return http_return(400, "未实名认证")
        if not user.userTelUuid.first():
            return http_return(400, "请绑定手机号")
        if not user.userWechatUuid.first():
            return http_return(400, "请绑定微信账号")
        try:
            user.banlance = user.banlance - money
            user.save()
            Withdrawal.objects.create(
                userUuid=user,
                withdrawalMoney=money,
                withdrawalType=2,
                withdrawalStatus=1,
                preArrivalAccountTime=datetime.now() + timedelta(days=3),
                wxAccount=user.userWechatUuid.first().openid,
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "提现申请失败")
        return http_return(200, "提现申请成功")


class BillListView(APIView):
    """
    流水列表
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        bills = Bill.objects.filter(userUuid__uuid=request.user.get("uuid")).order_by("-createTime").all()
        pg = MyPageNumberPagination()
        pager_bills = pg.paginate_queryset(queryset=bills, request=request, view=self)
        ser = BillsSerializer(instance=pager_bills, many=True)
        return pg.get_paginated_response(ser.data)


class PayZeroView(APIView):
    """
    流水列表
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def post(self, request):
        uuid = request.data.get("uuid", None)
        couponUuid = request.data.get("couponUuid", None)
        shareUuid = request.data.get("shareUuid", None)
        if not uuid:
            return http_return(400, "请选择购买课程")
        goods = Goods.objects.filter(content=uuid).first()
        if not goods:
            return http_return(400, "未获取到购买课程信息")
        user = request.user.get("userObj")
        behavior = Behavior.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=goods.content,
                                           behaviorType=5, isDelete=False).first()
        if behavior:
            return http_return(400, "你已购买过该课程")
        oldPrice = goods.realPrice
        price = oldPrice
        coupon = None
        if couponUuid and goods.isCoupon:
            coupon = UserCoupons.objects.filter(uuid=couponUuid, status=1).filter(qRangeCouponsUse).first()
            if not coupon:
                return http_return(400, "优惠券不可用")
            couponInfo = coupon.couponsUuid
            couponType = couponInfo.couponType
            if couponType == 1:
                price = oldPrice - couponInfo.money
            elif couponType == 2:
                scopeList = couponInfo.scope.split(",")
                if str(goods.goodsType) not in scopeList:
                    return http_return(400, "优惠券类型不符合课程类型")
                if couponInfo.accountMoney and couponInfo.accountMoney < float(oldPrice):
                    return http_return(400, "优惠券未达到满减要求")
                price = oldPrice - couponInfo.money
            elif couponType == 3:
                if couponInfo.accountMoney and couponInfo.accountMoney < float(oldPrice):
                    return http_return(400, "优惠券未达到满减要求")
                price = oldPrice - couponInfo.money
            try:
                Coupons.objects.filter(uuid=coupon.couponsUuid.uuid).update(usedNumber=F("usedNumber") + 1)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "更新优惠券使用数量失败")
        if price != 0:
            return http_return(400, "价格不等于零")
        shareUser = User.objects.filter(uuid=shareUuid).first() if shareUuid else None
        if not goods:
            return http_return(400, "商品信息不存在")
        shareMoney = int(oldPrice * goods.rewardPercent / 1000) * 10 if shareUser and goods.rewardStatus else None
        order = save_order(user, shareUser, price, oldPrice, coupon, shareMoney, goods)
        if not update_pay_zero_course(order):
            return http_return(400, "购买失败")
        return http_return(200, "购买成功")
