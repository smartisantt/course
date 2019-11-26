import logging
from datetime import datetime, timedelta

from django.core.cache import caches
from django.db.models import F

from client.clientCommon import get_orderNO, datetime_to_unix
from client.models import *
from parentscourse_server.config import TOKEN_TIMEOUT


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
            "tel": user.tel,
            "loginType": loginType,
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
            order.payStatus = 2,
            order.payAmount = data_dict["total_fee"]
            courseUuid = order.orderDetailUuid.first().goodsUuid.content
            course = Courses.objects.filter(uuid=courseUuid).first()
            order.save()
            if order.couponUuid:
                UserCoupons.objects.filter(uuid__in=order.couponUuid.split(",")).update(
                    status=2
                )
            Behavior.objects.create(
                userUuid=order.userUuid,
                courseUuid=course,
                behaviorType=5,
                remarks=order.uuid,
            )
            courses = course.relatedCourse.all()
            for c in courses:
                MayLike.objects.create(
                    userUuid=order.userUuid,
                    courseUuid=c,
                    likeType=1,
                )
            if order.shareUserUuid and order.goodsFlashUuid.first().goodsUuid.rewardStatus:
                money = order.shareMoney
                shareUser = order.shareUserUuid
                Bill.objects.create(
                    userUuid=shareUser,
                    billType=1,
                    remarks=course.uuid,
                    money=money
                )
                User.objects.filter(uuid=shareUser.uuuid).update(income=F("income") + money,
                                                                 banlance=F("banlance") + money)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def update_pay_member(data_dict):
    """支付成功，更新会员业务数据"""
    try:
        order = Orders.objects.filter(orderNum=data_dict["out_trade_no"]).first()
        if order.payStatus != 2:
            order.payStatus = 2,
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


def save_order(user, shareUser, price, oldPrice, coupon, shareMoney):
    """存储订单信息"""
    try:
        order = Orders.objects.create(
            userUuid=user,
            shareUserUuid=shareUser,
            orderNum=get_orderNO(),
            orderPrice=price,
            payAmount=price,
            orderOrgPrice=oldPrice,
            couponUuid=coupon.uuid if coupon and coupon.uuid else "",
            shareMoney=shareMoney,
            shareMoneyStatus=2 if shareMoney else 1,
        )
    except Exception as e:
        logging.error(str(e))
        return False
    return order


def save_order_detail(goods, order, shareMoney, oldPrice, coupon, price):
    """存储订单详情"""
    orderDetail = OrderDetail.objects.filter(goodsUuid__uuid=goods.uuid, orderUuid__uuid=order.uuid).first()
    if not orderDetail:
        try:
            orderDetail = OrderDetail.objects.create(
                goodsUuid=goods,
                orderUuid=order,
                detailNum="主订单_1",
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
    return orderDetail


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
