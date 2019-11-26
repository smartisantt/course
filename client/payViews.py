import logging
import threading

from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import F
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from client.insertQuery import update_pay_course, update_pay_member, save_order, save_order_detail
from client.serializers import BillsSerializer
from common.models import UserCoupons, Coupons, User, Orders, Goods, Withdrawal, Bill
from parentscourse_server.config import HOST_IP
from utils.clientAuths import ClientAuthentication
from utils.clientPermission import ClientPermission
from utils.funcTools import http_return
from utils.wechatPay import trans_xml_to_dict, get_sign, trans_dict_to_xml, APIKEY, hbb_wx_pay_params, hbb_wx_pay_query


class WXPayParams(APIView):
    """公众号端获取微信支付参数"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        uuid = request.data.get("uuid", None)
        couponUuid = request.data.get("couponUuid", None)
        shareUuid = request.data.get("shareUuid", None)
        if not uuid:
            return http_return(400, "请选择购买商品")
        goods = Goods.objects.filter(uuid=uuid).first()
        if not goods:
            return http_return(400, "未获取到购买商品")
        oldPrice = goods.realPrice
        price = oldPrice
        coupon = None
        if couponUuid:
            coupon = UserCoupons.objects.filter(uuid=couponUuid, status=1).first()
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
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        shareUser = User.objects.filter(uuid=shareUuid).first() if shareUuid else None
        if not goods:
            return http_return(400, "商品信息不存在")
        shareMoney = oldPrice * goods.rewardPercent / 100 if shareUser and goods.rewardStatus else None
        order = save_order(user, shareUser, price, oldPrice, coupon, shareMoney)
        if not order:
            return http_return(400, "订单存储失败")
        orderDetail = save_order_detail(goods, order, shareMoney, oldPrice, coupon, price)
        if not orderDetail:
            return http_return(400, "订单详情存储失败")
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
        data = hbb_wx_pay_params(dataInfo)
        if not data:
            return http_return(400, "下单失败")
        return http_return(200, "成功", {"payData": data, "uuid": order.uuid})


class WXPayResult(APIView):
    """微信会异步回调"""
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data_dict = trans_xml_to_dict(request.body)
        sign = data_dict.pop('sign')
        back_sign = get_sign(data_dict, APIKEY)
        if sign == back_sign and data_dict['return_code'] == 'SUCCESS':
            lock = threading.RLock()
            try:
                lock.acquire()
                deal_type = data_dict['device_info']
                if deal_type in [1, 2]:
                    if not update_pay_course(data_dict):
                        return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
                elif deal_type == 3:
                    if not update_pay_member(data_dict):
                        return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
            except Exception as e:
                logging.error(str(e))
                return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))
            finally:
                lock.release()
        return HttpResponse(trans_dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))


class WXPayQuery(APIView):
    """支付结果查询"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要查看支付结果的订单")
        order = Orders.objects.filter(uuid=uuid).first()
        if not order:
            return http_return(400, "未查询到支付订单")
        if order.payStatus != 2:
            data_dict = hbb_wx_pay_query(order.orderNum)
            sign = data_dict.pop('sign')
            back_sign = get_sign(data_dict, APIKEY)
            if sign == back_sign and data_dict['return_code'] == 'SUCCESS':
                try:
                    deal_type = data_dict['device_info']
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
            else:
                return http_return(400, "查询失败")
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
        if money > 500:
            return http_return(400, "提现金额超过限制")
        if not check_password(tradPwd, user.tradePwd):
            return http_return(400, "提现密码错误")
        if not all([user.realName, user.idCard, user.tradPws]):
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
                realName=user.realName,
                idCard=user.idCard,
                wxAccount=user.userWechatUuid.first().openid
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
        return Response(BillsSerializer(bills, many=True).data)
