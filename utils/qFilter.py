
from django.db.models import Q

# USER表 【普通用户正常 禁止登录 禁止发言】
USER_Q = Q(status__in=[1, 3, 4])

# Orders表  【用户成功购买 没有退款】 筛选条件
PAY_STATUS_Q = Q(payStatus__in=[2])

# Orders表  【有分销提成，累计分销收入】   2 待结算 ,3 已结算   筛选条件
SHARE_MONEY_STATUS_Q = Q(shareMoneyStatus__in=[2, 3])

# Orders表  【已结算】 3 已结算筛选条件
SHARE_MONEY_STATUS_Q2 = Q(shareMoneyStatus__in=[3])

# OrderDetail表   分销提成金额不为空 分销提成金额大于0   同时支付状态是已支付状态  分销金额状态是有分销状态 筛选条件
# 分销金额>0
DISTRIBUTE_Q = Q(shareMoney__isnull=False, shareMoney__gt=0, orderUuid__payStatus=2, orderUuid__shareMoneyStatus__in=[2, 3])


# OrderDetail表   分销提成金额不为空 分销提成金额大于0   同时支付状态是已支付状态  分销金额状态是有分销状  分销金额可以为0  筛选条件
# 分销金额可以为0
DISTRIBUTE_Q2 = Q(shareMoney__isnull=False, orderUuid__payStatus=2, orderUuid__shareMoneyStatus__in=[2, 3, 4])

# User表  只是正常用户
NORMAL_USER_Q = Q(status__in=[1])

# Banner 表 状态正常 和 禁用的
BANNER_Q = Q(status__in=[1, 2])

# HotSearch 表 状态正常 和 禁用的
HOT_SEARCH_Q = Q(status__in=[1, 2])

# CourseLive 表 状态正常 和 禁用的
COURSE_LIVE_Q = Q(status__in=[1, 2])

# MayLike 表 状态正常 和 禁用的, 是后台配置的
MAY_LIKE_Q = Q(status__in=[1, 2], likeType=3)

# Course 表 状态正常 和 禁用的
COURSE_Q = Q(status__in=[1, 2])

# Good 表 状态正常 和 可以使用优惠卷 可以被分销
GOODS_DISTRIBUTION_Q = Q(status=1, isCoupon=True)

# Courses 表 状态正常 是单次课 而且是直播课
COURSE_LIVE_SEARCH_Q = Q(status=1, courseType=1, chapterCourseUuid__chapterStyle=1)
