import logging
import time

from rest_framework import serializers
from datetime import datetime

from client.models import Comments
from common.models import *
from utils.errors import ParamError
from utils.msg import TIMESTAMP_TO_DATETIME_ERROR, TIME_RANGE_ERROR, DATETIME_TO_TIMESTAMP_ERROR, ENDTIME_RANGE_ERROR
from utils.timeTools import timeChange


class GoodsSimpleSerializer(serializers.ModelSerializer):
    # 销量    商品-》订单详情
    goodsType = serializers.SerializerMethodField()
    salesNum = serializers.SerializerMethodField()
    goodsImg = serializers.SerializerMethodField()

    def get_goodsType(self, obj):
        if obj.goodsType in [4, 6]:
            return "实物商品"
        return "虚拟物品"

    def get_goodsImg(self, obj):
        return obj.icon
        # if obj.goodsType == 1:
        #     course = Courses.objects.filter(uuid=obj.content).first()
        #     if course:
        #         return course.courseBanner

    def get_salesNum(self, obj):
        # 在已有付款的订单中计算总量
        return OrderDetail.objects.filter(goodsUuid_id=obj.uuid, orderUuid__payStatus=2).count()


    class Meta:
        model = Goods
        fields = ("name", "realPrice", "originalPrice", "goodsType",
                  "goodsImg", "salesNum")


class CouponsSerializer(serializers.ModelSerializer):
    startTime = serializers.SerializerMethodField()
    endTime = serializers.SerializerMethodField()
    goodsInfo = serializers.SerializerMethodField()
    goods = serializers.SerializerMethodField()
    isPast = serializers.SerializerMethodField()
    scope = serializers.SerializerMethodField()

    @staticmethod
    def get_scope(coupon):
        if coupon.scope:
            try:
                # "1,2,3"  变为  [1,2,3]
                return [int(x) for x in coupon.scope.split(",")]
            except Exception:
                return
        return []

    @staticmethod
    def get_isPast(coupon):
        # true 过期  false 没有过期
        return coupon.endTime < time.time()*1000

    @staticmethod
    def get_goodsInfo(coupon):
        if coupon.couponType == 1:
            return GoodsSimpleSerializer(coupon.goodsUuid).data

    @staticmethod
    def get_goods(coupon):
        if coupon.couponType == 1:
            return coupon.goodsUuid.uuid

    @staticmethod
    def get_startTime(coupons):
        # 数据库时间戳转成datetime
        if coupons.startTime:
            try:
                time_local = time.localtime(int(coupons.startTime/1000))
                dt = time.strftime("%Y-%m-%dT%H:%M:%S", time_local)
                return dt
            except Exception as e:
                logging.error(str(e))
                raise ParamError(TIMESTAMP_TO_DATETIME_ERROR)

    @staticmethod
    def get_endTime(coupons):
        # 数据库时间戳转成datetime
        if coupons.endTime:
            try:
                time_local = time.localtime(int(coupons.endTime/1000))
                dt = time.strftime("%Y-%m-%dT%H:%M:%S", time_local)
                return dt
            except Exception as e:
                logging.error(str(e))
                raise ParamError(TIMESTAMP_TO_DATETIME_ERROR)

    class Meta:
        model = Coupons
        exclude = ("updateTime", "remarks", "status", "creator", "goodsUuid")


class CouponsPostSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=22, required=True,
                                     error_messages={
                                         'min_length': '优惠卷名字不要小于2个字',
                                         'max_length': '优惠卷名字不要大于22个字',
                                         'required': '优惠卷名字必填'
                                     })
    startTime = serializers.DateTimeField(required=True,
                                         error_messages={
                                             'required': "开始时间必填"
                                         })
    endTime = serializers.DateTimeField(required=True,
                                         error_messages={
                                             'required': "结束时间必填"
                                         })
    couponType = serializers.ChoiceField(choices=COUPONS_TYPE_CHOICES, required=True,
                                         error_messages={
                                             'required': "优惠卷类型必填"
                                         })
    source = serializers.ChoiceField(choices=COUPONS_SOURCE_CHOICES, required=True,
                                     error_messages={
                                         'required': "优惠卷来源必填"
                                     })
    totalNumber = serializers.IntegerField(min_value=1, required=True,
                                     error_messages={
                                         'required': "优惠卷数量必填"
                                     })
    accountMoney = serializers.DecimalField(min_value=0, max_digits=12, decimal_places=2, required=False, allow_null=True)
    money = serializers.DecimalField(min_value=0, required=True, max_digits=12,  decimal_places=2,
                                     error_messages={
                                         'required': "优惠金额必填"
                                     })
    isPromotion = serializers.BooleanField(required=False, allow_null=True)
    scope = serializers.ListField(required=False, allow_null=True)

    # 单品卷此字段必有   品类卷和通用卷没有
    goods = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Goods.objects.filter(status=1))

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        # 优惠卷结束时间早于当前时间
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)
        goodsType = (1,2)
        # 当优惠类型为单品卷的时候，课程不能为空
        if attrs['couponType']==1:
            if not attrs.get("scope"):
                raise ParamError("scope 字段不能为空")
            if len(attrs.get("scope")) != 1 or not set(attrs.get("scope")).issubset(goodsType):
                raise ParamError("scope 字段错误")
            if not attrs.get("goods"):
                raise ParamError("当优惠类型为单品卷的时候，课程不能为空")
        # 当优惠卷为品类卷的时候，必选选择一个单词课 或者 系列课
        if attrs['couponType']==2:
            if not attrs.get("scope"):
                raise ParamError("scope 字段不能为空")
            if not isinstance(attrs.get("scope"), list):
                raise ParamError("scope 格式错误")

            if not set(attrs.get("scope")).issubset(goodsType):
                raise ParamError("scope 中参数错误")

        if attrs['couponType'] == 2 or attrs['couponType'] == 3:
            try:
                if attrs.get("accountMoney"):
                    float(attrs["accountMoney"])
            except Exception as e:
                raise ParamError("accountMoney 字段错误")
            # money必填字段
            try:
                float(attrs["money"])
            except Exception as e:
                raise ParamError("money 字段错误")
        return attrs

    def create_coupons(self, validated_data, request):
        # %Y-%m-%dT%H:%M:%S 字符串格式 转成毫秒的时间戳
        try:
            validated_data["startTime"] = timeChange(validated_data['startTime'], 2)
            validated_data["endTime"] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)
        # 前端传过来的是元  存数据库变为分
        if validated_data.get("accountMoney"):
            validated_data["accountMoney"] = int(float(validated_data["accountMoney"]) * 100 + 0.5)
        validated_data["money"] = int(float(validated_data["money"]) * 100 + 0.5)
        goods = validated_data.pop("goods")
        validated_data["goodsUuid"] = Goods.objects.filter(uuid=goods).first()

        validated_data["creator"] = request.user.uuid
        # [1,2,3]  ->  1,2,3
        scope = [str(x) for x in validated_data["scope"]]
        validated_data["scope"] = ",".join(scope)
        validated_data["usedNumber"] = 0
        validated_data["receivedNumber"] = 0
        coupons = Coupons.objects.create(**validated_data)
        return True

    def update_coupons(self, instance, validated_data):
        if validated_data.get("couponType"):
            if validated_data["couponType"] != instance.couponType:
                raise ParamError("优惠卷类型不能修改")
        try:
            validated_data["startTime"] = timeChange(validated_data['startTime'], 2)
            validated_data["endTime"] = timeChange(validated_data['endTime'], 2)
        except Exception:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)

        instance.name = validated_data["name"]
        instance.startTime = validated_data["startTime"]
        instance.endTime = validated_data["endTime"]
        if validated_data.get("accountMoney"):
            instance.accountMoney = int(float(validated_data["accountMoney"])*100 + 0.5)     # 前端填写的单位元 变 成分
        instance.money = int(float(validated_data["money"])*100 + 0.5)
        instance.totalNumber = validated_data["totalNumber"]

        if instance.couponType == 1:
            # 单品卷, 取goodsUuid
            instance.goodsUuid_id = validated_data["goods"]
        if instance.couponType == 2 or instance.couponType == 1:
            # 品类卷,
            scope = [str(x) for x in validated_data["scope"]]
            validated_data["scope"] = ",".join(scope)
            instance.scope = validated_data["scope"]
        if instance.couponType == 2 or instance.couponType == 3:
            # 通用卷
            instance.isPromotion = validated_data["isPromotion"]

        instance.save()



class UserCouponsSerializer(serializers.ModelSerializer):
    # 优惠卷》订单
    nickName = serializers.SerializerMethodField()
    tel = serializers.SerializerMethodField()
    orderInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_nickName(obj):
        return obj.userUuid.nickName

    @staticmethod
    def get_tel(obj):
        return obj.userUuid.tel

    @staticmethod
    def get_orderInfo(obj):
        if obj.status == 2:
            return {"usedTime":obj.orderUuid.createTime, "orderNum": obj.orderUuid.orderNum}

    class Meta:
        model = UserCoupons
        fields = ("createTime", "status", "nickName", "tel", "couponsUuid", "orderInfo")


class UserSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("uuid", "nickName", "avatar", "tel")


class CourseBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ("uuid", "name")


class CommentsSerializer(serializers.ModelSerializer):
    userInfo = serializers.SerializerMethodField()
    courseInfo = serializers.SerializerMethodField()
    finalCheckStatus = serializers.SerializerMethodField()

    @staticmethod
    def get_userInfo(obj):
        return UserSimpleSerializer(obj.userUuid).data

    @staticmethod
    def get_courseInfo(obj):
        return CourseBasicSerializer(obj.courseUuid).data

    @staticmethod
    def get_finalCheckStatus(obj):
        if obj.checkStatus in [2, 3]:
            return obj.checkStatus
        else:
            return obj.interfaceStatus

    class Meta:
        model = Comments
        exclude = ("updateTime", "isDelete", "replayUuid", "userUuid", "courseUuid")
