import logging
from datetime import datetime, timedelta

import requests
from django.core.cache import caches
from django.contrib.auth.hashers import make_password
from client.tasks import checkPayWorker

from client.clientCommon import get_orderNO, datetime_to_unix
from client.models import *
from parentscourse_server.config import TOKEN_TIMEOUT, ACCESS_TOKEN_TIMEOUT, DEFAULT_AVATAR


def set_user_session(token, user, loginType="PHONE"):
    """
    缓存token和用户信息
    loginType：WECHAT PHONE QQ
    :param token:
    :param user:
    :return:
    """
    try:
        user_info = {
            "uuid": user.uuid,
            "loginType": loginType,
            "userObj": user,
        }
        caches['client'].set(token, user_info, TOKEN_TIMEOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    old_token = caches['client'].get(user.uuid)
    if old_token:
        caches['client'].delete(old_token)
    caches['client'].set(user.uuid, token, TOKEN_TIMEOUT)
    return True


def save_access_token(openid, info):
    """
    缓存access_token
    :param openid:
    :param info:
    :return:
    """
    try:
        caches['client'].set(openid, info, ACCESS_TOKEN_TIMEOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def save_login_log(user, request, loginType):
    """
    存储登陆日志
    :param user:
    :param request:
    :param loginType:
    :return:
    """
    IP = request.META.get("HTTP_X_FORWARDED_FOR")
    try:
        LoginLog.objects.create(
            userUuid=user,
            ipAddr=IP if IP else None,
            loginType=loginType,
        )
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def update_pay_course(data_dict):
    """支付成功，处理订单业务逻辑"""
    try:
        order = Orders.objects.filter(orderNum=data_dict["out_trade_no"]).first()
        if order.payStatus != 2:
            order.payStatus = 2
            order.payAmount = data_dict["total_fee"]
            order.wxPayStatus = data_dict["trade_state"]
            order.save()
            courseUuid = order.orderDetailUuid.first().goodsUuid.content
            course = Courses.objects.filter(uuid=courseUuid).first()
            if order.couponUuid:
                UserCoupons.objects.filter(uuid__in=order.couponUuid.split(",")).update(
                    status=2,
                    orderUuid=order
                )
            Behavior.objects.create(
                userUuid=order.userUuid,
                courseUuid=course,
                behaviorType=5,
                remarks=order.uuid,
            )
            Payment.objects.create(
                orderNum=order,
                payWay="WXPAY",
                payWayName="微信支付",
                payTransNo=data_dict.get("transaction_id", None),
                payStatus=True,
                payAmount=data_dict.get("cash_fee", None),
                payTime=datetime_to_unix(datetime.now()),
                payType=1,
                cardNo=order.couponUuid if order.couponUuid else None,
                expPrice=data_dict.get("cash_fee", None),
            )
            courses = course.relatedCourse.all()
            for c in courses:
                may = MayLike.objects.filter(userUuid__uuid=order.userUuid.uuid, courseUuid__uuid=c.uuid).first()
                if may:
                    may.likeType = 1
                    may.save()
                else:
                    MayLike.objects.create(
                        userUuid=order.userUuid,
                        courseUuid=c,
                        likeType=1,
                    )
            checkPayWorker.apply_async((order.uuid,), eta=datetime.utcnow() + timedelta(days=3))
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def update_pay_zero_course(order):
    """支付成功，处理订单业务逻辑"""
    try:
        if order.payStatus != 2:
            order.payStatus = 2
            order.save()
            courseUuid = order.orderDetailUuid.first().goodsUuid.content
            course = Courses.objects.filter(uuid=courseUuid).first()
            if order.couponUuid:
                UserCoupons.objects.filter(uuid__in=order.couponUuid.split(",")).update(
                    status=2,
                    orderUuid=order
                )
            Behavior.objects.create(
                userUuid=order.userUuid,
                courseUuid=course,
                behaviorType=5,
                remarks=order.uuid,
            )
            courses = course.relatedCourse.all()
            for c in courses:
                may = MayLike.objects.filter(userUuid__uuid=order.userUuid.uuid, courseUuid__uuid=c.uuid).first()
                if may:
                    may.likeType = 1
                    may.save()
                else:
                    MayLike.objects.create(
                        userUuid=order.userUuid,
                        courseUuid=c,
                        likeType=1,
                    )
            checkPayWorker.apply_async((order.uuid,), eta=datetime.utcnow() + timedelta(days=3))
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def update_pay_member(data_dict):
    """支付成功，更新会员业务数据"""
    try:
        order = Orders.objects.filter(orderNum=data_dict["out_trade_no"]).first()
        if order.payStatus != 2:
            order.payStatus = 2
            order.payAmount = data_dict["total_fee"]
            order.save()
            startTime = datetime_to_unix(datetime.now())
            duration = order.orderDetailUuid.first().goodsUuid.duration
            endTime = datetime_to_unix(datetime.now() + timedelta(days=duration))
            UserMember.objects.create(
                userUuid=order.userUuid,
                startTime=startTime,
                endTime=endTime,
            )
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def save_order(user, shareUser, price, oldPrice, coupon, shareMoney, goods):
    """存储订单信息"""
    try:
        order = Orders.objects.create(
            userUuid=user,
            shareUserUuid=shareUser if shareUser and shareUser.uuid != user.uuid else None,
            orderNum=get_orderNO(),
            orderPrice=price,
            orderOrgPrice=oldPrice,
            couponUuid=coupon.uuid if coupon and coupon else "",
            shareMoney=shareMoney,
            shareMoneyStatus=2 if shareMoney else 1,
            buyerName=user.nickName,
        )
        orderDetail = OrderDetail.objects.filter(goodsUuid__uuid=goods.uuid, orderUuid__uuid=order.uuid).first()
        if not orderDetail:
            OrderDetail.objects.create(
                goodsUuid=goods,
                orderUuid=order,
                detailNum=order.orderNum + "_1",
                goodsName=goods.name,
                goodsCount=1,
                shareMoney=shareMoney if shareMoney else None,
                goodsImg=goods.icon,
                originalPrice=goods.originalPrice,
                goodsPrice=goods.realPrice,
                totalPrice=oldPrice,
                couponPrice=coupon.couponsUuid.money if coupon and coupon.couponsUuid else None,
                payPrice=price,
            )
    except Exception as e:
        logging.error(str(e))
        return False
    return order


def wechat_bind_tel(telAuth, user):
    """执行微信绑定手机号"""
    try:
        # 会员信息、购买记录、订单信息、浏览记录、上课记录、流水信息、课程评论、收藏信息、日志信息、收益信息
        UserMember.objects.filter(userUuid__uuid=telAuth.userUuid.uuid).update(userUuid=user, remarks=user.uuid)
        Behavior.objects.filter(userUuid__uuid=telAuth.userUuid.uuid, behaviorType__in=[2, 3, 5]).update(userUuid=user)
        Orders.objects.filter(userUuid__uuid=telAuth.userUuid.uuid).update(userUuid=user)
        Bill.objects.filter(userUuid__uuid=telAuth.userUuid.uuid).update(userUuid=user)
        user.banlance = telAuth.userUuid.banlance
        user.income = telAuth.userUuid.income
        user.save()
        Comments.objects.filter(userUuid__uuid=telAuth.userUuid.uuid).update(userUuid=user)
        LoginLog.objects.filter(userUuid__uuid=telAuth.userUuid.uuid).update(userUuid=user)
        telAuth.userUuid = user
        telAuth.userSource = 3
        telAuth.save()
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def tel_bind_wechat(wechat, user):
    """执行手机号绑定微信逻辑"""
    try:
        # 会员信息、购买记录、订单信息、浏览记录、上课记录、流水信息、课程评论、收藏信息、日志信息、收益信息
        UserMember.objects.filter(userUuid__uuid=wechat.userUuid.uuid).update(userUuid=user, remarks=user.uuid)
        Behavior.objects.filter(userUuid__uuid=wechat.userUuid.uuid, behaviorType__in=[2, 3, 5]).update(userUuid=user)
        Orders.objects.filter(userUuid__uuid=wechat.userUuid.uuid).update(userUuid=user)
        Bill.objects.filter(userUuid__uuid=wechat.userUuid.uuid).update(userUuid=user)
        Comments.objects.filter(userUuid__uuid=wechat.userUuid.uuid).update(userUuid=user)
        LoginLog.objects.filter(userUuid__uuid=wechat.userUuid.uuid).update(userUuid=user)
        wechat.userUuid = user
        wechat.save()
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def if_study_course(course, user, behavior):
    """
    判断用户是否用后课程权限
    :param course:
    :param user:
    :return:
    """
    selfUuid = user.uuid
    ctype = course.coursePermission
    if not ctype:
        return True
    if ctype == 1:
        return True
    elif ctype == 2:
        userMember = UserMember.objects.filter(userUuid__uuid=selfUuid,
                                               startTime__lte=datetime_to_unix(datetime.now()),
                                               endTime__gte=datetime_to_unix(datetime.now())).first()
        if not userMember:
            if not behavior:
                return False
        return True
    elif ctype == 3:
        if not behavior:
            return False
        return True
    else:
        return False


def get_user_role(user, room):
    """确认用户在聊天室身份"""
    selfUuid = user.uuid
    expertUuid = room.expertUuid.userUuid.uuid if room.expertUuid else None
    mcUuid = room.mcUuid.uuid if room.mcUuid else None
    luckList = []
    for luck in room.inviterUuid.all():
        luckList.append(luck.uuid)
    role = "normal"
    if selfUuid == expertUuid:
        role = "expert"
    else:
        if selfUuid == mcUuid:
            role = "compere"
        else:
            if selfUuid in luckList:
                role = "luck"
    return role


def get_avatar(url):
    r = requests.get(url)
    if r.status_code != 200 or not url:
        return DEFAULT_AVATAR
    return url


def save_hbb_user(hbbUserData, tel=None, password=None):
    """存储好呗呗用户数据"""
    try:

        user = User.objects.create(
            tel=hbbUserData.get("tel"),
            nickName=hbbUserData.get("nickName"),
            registerPlatform=4,
            gender=hbbUserData.get("gender", 3),
            avatar=get_avatar(hbbUserData.get("avatar", None)),
            location=hbbUserData.get("location"),
            intro=hbbUserData.get("intro"),
            userRoles=hbbUserData.get("userRoles", 3),
        )
        telInfo = hbbUserData.get("tel", None)
        if telInfo:
            TelAuth.objects.create(
                userUuid=user,
                tel=tel,
                passwd=make_password(password),
                userSource=3,
            )
        unionid = hbbUserData.get("unionid", None)
        if unionid:
            WechatAuth.objects.create(
                userUuid=user,
                name=hbbUserData.get("nickName", tel),
                sex=hbbUserData.get("gender", 3),
                avatar=hbbUserData.get("avatar", DEFAULT_AVATAR),
                unionid=unionid,
            )
    except Exception as e:
        logging.error(str(e))
        return False
    return user
