"""
专门用于存储Filter Q
"""
from datetime import datetime

from django.db.models import Q

from client.clientCommon import datetime_to_unix, get_day_latest_time, get_day_zero_time

# 轮播图筛选
qRange = Q(startTime__lte=datetime_to_unix(datetime.now())) & Q(endTime__gte=datetime_to_unix(datetime.now()))
qRangeToday = Q(createTime__gte=get_day_zero_time(datetime.today()), createTime__lte=get_day_latest_time(datetime.today()))
qRangeCoupons = Q(couponsUuid__endTime__gte=datetime_to_unix(datetime.now()))
qRangeCouponsUse = Q(couponsUuid__startTime__lte=datetime_to_unix(datetime.now())) & Q(couponsUuid__endTime__gte=datetime_to_unix(datetime.now()))
qRangeCouponAll = Q(startTime__lte=datetime_to_unix(datetime.now())) & Q(endTime__gte=datetime_to_unix(datetime.now()))
q = Q(status=1) & qRange
# 首页标签筛选条件
q1 = Q(enable=True) & Q(level=1) & Q(tagType=1)
# 首页模块筛选条件
q2 = Q(enable=True) & Q(sectionType=1) & Q(isShow=True)
# 猜你喜欢筛选条件
q3 = Q(status=1)
# 课程筛选条件
q4 = Q(status=1)
# 用戶筛选基本条件
q5 = Q(status=1)
# 优惠券筛选条件
qRangeEnd = Q(endTime__gte=datetime_to_unix(datetime.now()))
q6 = Q(status=1) & qRangeCouponAll
# 分销记录筛选条件
q7 = Q(enable=False)
# 会员卡筛选条件
q8 = Q(goodsType=3) & Q(status=1)
