import logging
from datetime import datetime

from django.db.models import F
from rest_framework import serializers

from client.clientCommon import match_tel, get_default_name, datetime_to_unix, unix_time_to_datetime
from client.insertQuery import if_study_course
from client.models import *
from client.queryFilter import q6, qRange, q4
from client.search_indexes import CoursesIndex
from utils.errors import ParamError
from drf_haystack.serializers import HaystackSerializer


class BannerSerializer(serializers.ModelSerializer):
    """轮播图序列化"""

    class Meta:
        model = Banner
        fields = ("uuid", "name", "icon", "type", "target")


class TagsSerializer2(serializers.ModelSerializer):
    """标签序列化"""

    class Meta:
        model = Tags
        fields = ("name", "uuid")


class TagsSerializer(serializers.ModelSerializer):
    """标签序列化"""
    children = serializers.SerializerMethodField(read_only=True)

    def get_children(self, obj):
        objInfo = obj.children.filter(enable=True).order_by("-weight")
        if objInfo:
            return TagsSerializer2(objInfo, many=True).data
        else:
            return None

    class Meta:
        model = Tags
        fields = ("name", "uuid", "children")


class IndexExpertSerializer(serializers.ModelSerializer):
    """专家序列化"""

    class Meta:
        model = Experts
        fields = ("name", "uuid", "hospital", "avatar", "department", "jobTitle")


class CourseListSerializer(serializers.ModelSerializer):
    """首页显示课程序列化"""
    icon = serializers.CharField(source="courseBanner")
    intro = serializers.CharField(source="briefIntro")
    expert = serializers.SerializerMethodField()
    originalPrice = serializers.SerializerMethodField(read_only=True)
    realPrice = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField(read_only=True)
    startTime = serializers.SerializerMethodField(read_only=True)
    endTime = serializers.SerializerMethodField(read_only=True)
    chapterStyle = serializers.SerializerMethodField(read_only=True)

    def get_chapterStyle(self, obj):
        return obj.chapterCourseUuid.first().chapterStyle if obj.chapterCourseUuid.first() else 2

    def get_startTime(self, obj):
        if obj.chapterCourseUuid.first() and obj.chapterCourseUuid.first().chapterStyle == 1:
            return obj.startTime
        return None

    def get_endTime(self, obj):
        if obj.chapterCourseUuid.first() and obj.chapterCourseUuid.first().chapterStyle == 1:
            return obj.endTime
        return None

    @staticmethod
    def get_expert(obj):
        if not obj:
            return None
        queryset = obj.expertUuid
        if not queryset:
            queryset = obj.chapterCourseUuid.first()
            if not queryset:
                return None
            queryset = queryset.expertUuid
        return IndexExpertSerializer(queryset).data

    def get_originalPrice(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return 0
        if goods and not goods.originalPrice:
            return 0
        return goods.originalPrice

    def get_realPrice(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return 0
        if goods and not goods.realPrice:
            return 0
        return goods.realPrice

    def get_discount(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return 1
        return goods.discount

    class Meta:
        model = Courses
        fields = (
            "name", "startTime", "endTime", "icon", "intro", "originalPrice", "realPrice", "courseType", "duration",
            "expert", "uuid", "vPopularity", "discount", "chapterStyle")


class SectionSerializer(serializers.ModelSerializer):
    """首页模块序列化"""
    # sectioncourses = IndexCourseSerializer(many=True)
    courses = serializers.SerializerMethodField()

    @staticmethod
    def get_courses(obj):
        queryset = obj.sectionCourseUuid.filter(status=1).order_by("-weight").all()[0:obj.showNum]
        newQueryset = []
        for qu in queryset:
            newQueryset.append(qu.courseUuid)
        return CourseListSerializer(newQueryset, many=True).data

    class Meta:
        model = Section
        fields = ("name", "uuid", "courses", "showType")
        depth = 3


class CourseSourceSerializer(serializers.ModelSerializer):
    """课件序列化"""
    url = serializers.CharField(source="sourceUrl")

    class Meta:
        model = CourseSource
        fields = ("uuid", "name", "url", "sourceType", "fileSize", "duration")


class ChaptersSerializer(serializers.ModelSerializer):
    """章节序列化"""
    tryInfo = serializers.SerializerMethodField(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)
    isTry = serializers.SerializerMethodField(read_only=True)

    def get_duration(self, obj):
        if obj.courseSourceUuid and obj.courseSourceUuid.duration:
            return obj.courseSourceUuid.duration
        return 0

    def get_isTry(self, obj):
        if obj.tryInfoUuid or obj.isTry == 1:
            return True
        return False

    @staticmethod
    def get_tryInfo(obj):
        objInfo = obj.tryInfoUuid
        if not objInfo and obj.isTry == 1:
            objInfo = obj.courseSourceUuid
        if not objInfo:
            return None
        return CourseSourceSerializer(objInfo).data

    class Meta:
        model = Chapters
        fields = (
            "uuid", "name", "tryInfo", "serialNumber", "chapterStyle", "duration", "startTime", "endTime",
            "chapterBanner", "info", "isTry")


class CouponsSerializer(serializers.ModelSerializer):
    """优惠券序列化"""

    class Meta:
        model = Coupons
        fields = ("uuid", "name", "source", "remarks", "accountMoney", "money", "startTime", "endTime")


class CourseSerializer(CourseListSerializer):
    """课程详情序列化"""
    chapters = serializers.SerializerMethodField(read_only=True)
    coupons = serializers.SerializerMethodField(read_only=True)
    canStudy = serializers.SerializerMethodField(read_only=True)
    isLike = serializers.SerializerMethodField(read_only=True)
    share = serializers.SerializerMethodField(read_only=True)
    originalPrice = serializers.SerializerMethodField(read_only=True)
    realPrice = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField(read_only=True)
    goodsUuid = serializers.SerializerMethodField(read_only=True)
    haveTry = serializers.SerializerMethodField(read_only=True)

    def get_haveTry(self, obj):
        for chapter in obj.chapterCourseUuid.all():
            if chapter.tryInfoUuid or chapter.isTry == 1:
                return True
        return False

    def get_goodsUuid(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        else:
            return goods.uuid

    def get_originalPrice(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        return goods.originalPrice

    def get_realPrice(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        return goods.realPrice

    def get_discount(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        return goods.discount

    def get_isLike(self, obj):
        behavior = Behavior.objects.filter(userUuid__uuid=self.context["request"].user.get("uuid"),
                                           courseUuid__uuid=obj.uuid, isDelete=False, behaviorType=2).first()
        if not behavior:
            return False
        return True

    def get_chapters(self, obj):
        objInfo = obj.chapterCourseUuid.filter(status=1).order_by("serialNumber")
        return ChaptersSerializer(objInfo, many=True,
                                  context={"selfUuid": self.context["request"].user.get("uuid")}).data

    def get_coupons(self, obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        objInfo = goods.goodsCouponsUuid.filter(q6).filter(couponType=1, totalNumber__gt=F("receivedNumber")).first()
        if not objInfo:
            return None
        return CouponsSerializer(objInfo, many=False, context={"request": self.context["request"]}).data

    def get_canStudy(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        user = User.objects.filter(uuid=selfUuid).first()
        behavior = Behavior.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=obj.uuid, behaviorType=5).first()
        if not if_study_course(obj, user, behavior):
            return False
        return True

    def get_share(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        user = User.objects.filter(uuid=selfUuid).first()
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods or not goods.rewardStatus:
            return None
        data = {
            "shareUrl": obj.shareUrl,
            "shareImg": obj.shareImg,
            "avatar": user.avatar,
            "userUuid": user.uuid,
            "nickName": user.nickName,
            "realPrice": goods.realPrice,
            "rewardPercent": goods.rewardPercent,
            "courseUuid": obj.uuid
        }
        return data

    class Meta:
        model = Courses
        fields = (
            "name", "startTime", "endTime", "icon", "intro", "originalPrice", "realPrice", "courseType", "duration",
            "expert", "uuid", "vPopularity", "chapters", "coupons", "info", "canStudy", "haveTry",
            "isLike", "share", "discount", "goodsUuid", "infoType", "coursePermission", "preChapter")
        depth = 4


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    nickName = serializers.SerializerMethodField(read_only=True)
    role = serializers.CharField(source="userRoles")
    member = serializers.SerializerMethodField(read_only=True)
    banlance = serializers.SerializerMethodField(read_only=True)
    income = serializers.SerializerMethodField(read_only=True)
    telInfo = serializers.SerializerMethodField(read_only=True)
    wechatInfo = serializers.SerializerMethodField(read_only=True)
    isReal = serializers.SerializerMethodField(read_only=True)

    def get_isReal(self, obj):
        if not all([obj.realName, obj.idCard, obj.tradePwd]):
            return False
        return True

    def get_telInfo(self, obj):
        if not obj.userTelUuid.first():
            return None
        info = {
            "tel": obj.userTelUuid.first().tel,
            "uuid": obj.userTelUuid.first().uuid,
            "havePwd": True if obj.userTelUuid.first().passwd else False,
        }
        return info

    def get_wechatInfo(self, obj):
        if not obj.userWechatUuid.first():
            return None
        info = {
            "uuid": obj.userWechatUuid.first().uuid,
            "nickName": obj.userWechatUuid.first().name,
            "sex": obj.userWechatUuid.first().sex,
            "avatar": obj.userWechatUuid.first().avatar,
        }
        return info

    def get_banlance(self, obj):
        return obj.banlance if obj.banlance else 0

    def get_income(self, obj):
        return obj.income if obj.income else 0

    def get_nickName(self, obj):
        name = obj.nickName
        if match_tel(name):
            name = get_default_name(name)
        return name

    def get_member(self, obj):
        member = obj.userMemberInfo.filter(qRange).first()
        if not member:
            return None
        return {"startTime": member.startTime, "endTime": member.endTime,
                "days": (unix_time_to_datetime(member.endTime) - datetime.now()).days + 1}

    class Meta:
        model = User
        fields = (
            "uuid", "nickName", "avatar", "gender", "intro", "birthday", "point", "remark", "role", "location",
            "income", "banlance", "member", "tel", "telInfo", "wechatInfo", "isReal")


class CommentUserSerializer(UserSerializer):
    """课程评论序列化"""

    class Meta:
        model = User
        fields = (
            "uuid", "nickName", "avatar")


class CommentsSerializer(serializers.ModelSerializer):
    """评论序列化"""
    replay = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    createTime = serializers.SerializerMethodField(read_only=True)
    isLike = serializers.SerializerMethodField(read_only=True)
    likeCount = serializers.SerializerMethodField(read_only=True)
    isMyself = serializers.SerializerMethodField(read_only=True)

    def get_replay(self, obj):
        # if not obj.replayUuid: 目前只做一级评论
        return None

    def get_user(self, obj):
        return CommentUserSerializer(obj.userUuid).data

    def get_isLike(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        commentLike = CommentsLike.objects.filter(userUuid__uuid=selfUuid, commentUuid__uuid=obj.uuid,
                                                  status=1).first()
        if commentLike:
            return True
        return False

    def get_createTime(self, obj):
        return datetime_to_unix(obj.createTime)

    def get_likeCount(self, obj):
        return obj.commentLikeUserUuid.filter(status=1).count()

    def get_isMyself(self, obj):
        if obj.userUuid.uuid == self.context["request"].user.get("uuid"):
            return True
        return False

    class Meta:
        model = Comments
        fields = ("uuid", "content", "createTime", "replay", "user", "isLike", "likeCount", "isMyself")
        depth = 3


class CommentPostSerializer(serializers.Serializer):
    """校验提交的评论"""
    content = serializers.CharField(min_length=1, max_length=60, required=True,
                                    error_messages={
                                        'min_length': '评论内容不能为空',
                                        'max_length': '评论内容超过长度，请重新输入',
                                        'required': '请输入要评论的内容'
                                    })
    uuid = serializers.CharField(required=True, error_messages={'required': '请选择要评论的课程'})

    def validate_course(self, value):
        course = Courses.objects.filter(uuid=value).first()
        if not course:
            raise ParamError("课程信息不存在")
        return value

    def create_comment(self, validated_data, user, request):
        uuid = validated_data.pop("uuid")
        validated_data["courseUuid"] = Courses.objects.filter(uuid=uuid).first()
        validated_data["userUuid"] = user
        comment = Comments.objects.create(**validated_data)
        return comment


class CommentLikeSerializer(serializers.ModelSerializer):
    """评论点赞列化"""

    class Meta:
        model = CommentsLike
        fields = ("uuid",)


class CommentLikePostSerializer(serializers.Serializer):
    """评论点赞校验"""
    uuid = serializers.CharField(required=True, error_messages={'required': '请选择点赞的评论'})

    def validate(self, attrs):
        uuid = attrs.get("uuid")
        comment = Comments.objects.filter(uuid=uuid).first()
        if not comment:
            raise ParamError("评论不存在")
        return attrs

    def create_comment_like(self, validate_data, request):
        uuid = validate_data.pop("uuid")
        validate_data["commentUuid"] = Comments.objects.filter(uuid=uuid).first()
        validate_data["userUuid"] = User.objects.filter(uuid=request.user.get("uuid")).first()
        commentLike = CommentsLike.objects.filter(userUuid__uuid=request.user.get("uuid"), commentUuid__uuid=uuid,
                                                  status=1).first()
        if commentLike:
            commentLike.status = 2
            try:
                commentLike.save()
            except Exception as e:
                logging.error(str(e))
                raise ParamError("取消失败")
        else:
            try:
                commentLike = CommentsLike.objects.create(**validate_data)
            except Exception as e:
                logging.error(str(e))
                raise ParamError("点赞失败")
        return commentLike


class ChatsSerializer(serializers.ModelSerializer):
    """专家发言序列化"""
    isRead = serializers.SerializerMethodField(read_only=True)

    def get_isRead(self, obj):
        read = UserReadChats.objects(chatUuid__uuid=obj.uuid,
                                     userUuid__uuid=self.context["request"].user.get("uuid")).first()
        if read:
            return True
        return False

    class Meta:
        model = Chats
        fields = ("uuid", "userRole", "talkType", "content", "duration", "msgTime", "msgSeq", "isRead")


class DiscussSerializer(serializers.ModelSerializer):
    """用户讨论序列化器"""
    user = serializers.SerializerMethodField(read_only=True)
    isMyself = serializers.SerializerMethodField(read_only=True)

    def get_isMyself(self, obj):
        if obj.userUuid.uuid == self.context["request"].user.get("uuid"):
            return True
        return False

    def get_user(self, obj):
        return UserSerializer(obj.userUuid).data

    class Meta:
        model = Discuss
        fields = ("uuid", "content", "msgTime", "msgSeq", "isQuestion", "isAnswer", "user", "isMyself")


class LiveCourseBannerSerializer(serializers.ModelSerializer):
    """聊天室轮播图"""
    url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_url(obj):
        objInfo = obj.sourceUrl
        if obj.sourceUrl == None and obj.sourceType == 3:
            listInfo = []
            for bi in obj.courseSourcePpt.filter(enable=True).order_by("sortNum").all():
                listInfo.append(bi.imgUrl)
            objInfo = ",".join(listInfo)
        return objInfo

    class Meta:
        model = LiveCourseBanner
        fields = ("uuid", "url", "sourceType", "fileSize", "duration", "pages")


class RoomSerializer(serializers.ModelSerializer):
    """聊天室序列化"""
    courseSource = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)

    def get_role(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        expertUuid = obj.expertUuid.userUuid.uuid if obj.expertUuid else None
        mcUuid = obj.mcUuid.uuid
        luckList = []
        for luck in obj.inviterUUid:
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

    def get_courseware(self, obj):
        if obj.liveCourseUuid and obj.liveCourseUuid.enable:
            return LiveCourseBannerSerializer(obj.liveCourseUuid.liveCourseBannerUuid, many=False).data
        return None

    class Meta:
        model = ChatsRoom
        fields = (
            "uuid", "name", "startTime", "endTime", "banner", "studyNum", "courseSource", "role")


class ChapterListSerializer(serializers.ModelSerializer):
    """课件播放列表序列化"""
    source = serializers.SerializerMethodField(read_only=True)

    def get_source(self, obj):
        """获取课程资源"""
        return CourseSourceSerializer(obj.courseSourceUuid, many=False).data

    class Meta:
        model = Chapters
        fields = ("uuid", "name", "chapterStyle", "source")
        depth = 3


class HotSearchSerializer(serializers.ModelSerializer):
    """热搜词序列化器"""

    class Meta:
        model = HotSearch
        fields = ("uuid", "keyword", "icon")


class SearchHistorySerializer(serializers.ModelSerializer):
    """搜索历史序列化器"""

    class Meta:
        model = UserSearch
        fields = ("keyword",)


class CouponsSerializer(serializers.ModelSerializer):
    """优惠券序列化器"""
    price = serializers.SerializerMethodField(read_only=True)
    isReceive = serializers.SerializerMethodField(read_only=True)
    scope = serializers.SerializerMethodField(read_only=True)

    def get_scope(self, obj):
        targetDict = {
            "1": "单次课",
            "2": "系列课"
        }
        scopeList = obj.scope.split(",")

        newList = []
        if len(scopeList) > 0:
            for sc in scopeList:
                if sc != "":
                    newList.append(targetDict[sc])
        return "、".join(newList)

    def get_isReceive(self, obj):
        checkRe = UserCoupons.objects.filter(userUuid_id=self.context["request"].user.get("uuid"),
                                             couponsUuid__uuid=obj.uuid).first()
        if checkRe:
            return True
        return False

    def get_price(self, obj):
        if obj.couponType != 1:
            return None
        return obj.goodsUuid.realPrice

    class Meta:
        model = Coupons
        fields = (
            "uuid", "name", "startTime", "endTime", "couponType", "accountMoney", "money", "price", "isReceive",
            "scope")


class UserCouponsSerializer(serializers.ModelSerializer):
    """用户优惠券序列化"""
    coupon = serializers.SerializerMethodField(read_only=True)
    target = serializers.SerializerMethodField(read_only=True)
    ctype = serializers.SerializerMethodField(read_only=True)

    def get_target(self, obj):
        if obj.couponsUuid.couponType == 1:
            return obj.couponsUuid.goodsUuid.content
        return None

    def get_ctype(self, obj):
        return obj.couponsUuid.couponType

    def get_coupon(self, obj):
        return CouponsSerializer(obj.couponsUuid, context={"request": self.context["request"]}).data

    class Meta:
        model = UserCoupons
        fields = ("uuid", "status", "coupon", "target", "ctype")


class UserCouponsPostSerializer(serializers.Serializer):
    """用户领用优惠券校验"""
    couponsUuid = serializers.CharField(required=True, error_messages={'required': '请选择要领用的优惠券'})

    def validate_couponsUuid(self, value):
        coupon = Coupons.objects.filter(uuid=value).filter(q6).filter(totalNumber__gt=F("receivedNumber")).first()
        if not coupon:
            raise ParamError("优惠券无法领取")
        return coupon

    def create_user_coupon(self, validated_data, request):
        selfUuid = request.user.get("uuid")
        user = User.objects.filter(uuid=selfUuid).first()
        validated_data["userUuid"] = user
        userCoupon = UserCoupons.objects.filter(userUuid__uuid=selfUuid,
                                                couponsUuid__uuid=validated_data["couponsUuid"].uuid).first()
        if not userCoupon:
            try:
                userCoupon = UserCoupons.objects.create(**validated_data)
            except Exception as e:
                logging.error(str(e))
                raise ParamError("领取优惠券失败")
        return UserCouponsSerializer(userCoupon, context={"request": request}, many=False).data


class ExpertSerializer(serializers.ModelSerializer):
    """专家序列化"""
    followCount = serializers.SerializerMethodField(read_only=True)
    isFollower = serializers.SerializerMethodField(read_only=True)

    def get_followCount(self, obj):
        return obj.expertFollowUuid.filter(status=1).count()

    def get_isFollower(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        follow = FollowExpert.objects.filter(userUuid__uuid=selfUuid, expertUuid__uuid=obj.uuid, status=1).first()
        if not follow:
            return False
        return True

    class Meta:
        model = Experts
        fields = ("name", "uuid", "hospital", "avatar", "department", "jobTitle", "intro", "specialty", "followCount",
                  "isFollower")


class SearchLikeSerializer(serializers.ModelSerializer):
    """搜索模糊匹配"""
    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        keyword = self.context["request"].query_params.get("keyword")
        res = obj.name.replace(keyword, "<font color='#F9626A'>" + keyword + "</font>")
        return res

    class Meta:
        model = Courses
        fields = ("uuid", "name")


class BehaviorPostSerializer(serializers.Serializer):
    """用户领用优惠券校验"""
    courseUuid = serializers.CharField(required=True, error_messages={'required': '请选择课程'})
    behaviorType = serializers.IntegerField(required=True, min_value=1, max_value=3,
                                            error_messages={'required': '请选择行为类型'})

    def create_behavior(self, validated_data, request):
        courseUuid = validated_data.pop("courseUuid")
        selfUuid = request.user.get("uuid")
        checkBehavior = Behavior.objects.filter(userUuid__uuid=selfUuid, courseUuid__uuid=courseUuid,
                                                behaviorType=validated_data["behaviorType"]).first()
        if not checkBehavior:
            course = Courses.objects.filter(uuid=courseUuid).filter(q4).first()
            if not course:
                raise ParamError("课程信息不存在")
            user = User.objects.filter(uuid=selfUuid).first()
            validated_data["userUuid"] = user
            validated_data["courseUuid"] = course
            try:
                checkBehavior = Behavior.objects.create(**validated_data)
            except Exception as e:
                logging.error(str(e))
                raise ParamError("失败")
        else:
            if checkBehavior.isDelete == True:
                checkBehavior.isDelete = False
                try:
                    checkBehavior.save()
                except Exception as e:
                    logging.error(str(e))
                    raise ParamError("失败")
        return checkBehavior

    def update_behavior(self, validated_data, request):
        """取消行为信息"""
        courseUuid = validated_data.pop("courseUuid")
        selfUuid = request.user.get("uuid")
        try:
            Behavior.objects.filter(userUuid__uuid=selfUuid, courseUuid__uuid=courseUuid,
                                    behaviorType=validated_data["behaviorType"], isDelete=False).update(isDelete=True)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("失败")
        return


class ShareSerializer(serializers.ModelSerializer):
    """分享记录序列化"""

    class Meta:
        model = Shares
        fields = ("uuid", "shareUrl", "realPrice", "rewardPercent")


class SharesPostSerializer(serializers.Serializer):
    """分享记录校验"""
    courseUuid = serializers.CharField(required=True, error_messages={'required': '请选择课程'})
    shareUrl = serializers.CharField(required=True, error_messages={'required': '未获取到分享链接'})
    realPrice = serializers.CharField(required=True, error_messages={'required': '未获取到课程价格'})
    rewardPercent = serializers.CharField(required=True, error_messages={'required': '未获取到分销比例'})

    def create_share(self, validated_data, request):
        """添加分销记录"""
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        courseUuid = validated_data.pop("courseUuid")
        course = Courses.objects.filter(uuid=courseUuid).first()
        if not course:
            raise ParamError("课程信息不存在")
        validated_data["courseUuid"] = course
        validated_data["userUuid"] = user
        try:
            share = Shares.objects.create(**validated_data)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("添加分销记录失败")
        return share


class LivesSerializer(serializers.ModelSerializer):
    """大咖直播序列化"""
    courseUuid = serializers.SerializerMethodField(read_only=True)

    def get_courseUuid(self, obj):
        return obj.courseUuid.uuid

    class Meta:
        model = CourseLive
        fields = ("uuid", "icon", "courseUuid")


class MemberCardSerializer(serializers.ModelSerializer):
    """会员卡序列化"""

    class Meta:
        model = Goods
        fields = ("uuid", "name", "icon", "content", "realPrice", "discount")


class FeedbackSerializer(serializers.ModelSerializer):
    """用户反馈列化"""

    class Meta:
        model = Feedback
        fields = ("uuid", "type", "icon", "content", "replyInfo", "isRead")


class FeedbackPostSerializer(serializers.Serializer):
    """用户反馈序列化"""

    content = serializers.CharField(required=True, error_messages={'required': '请输入反馈内容'})
    icon = serializers.ListField(child=serializers.CharField(required=False), required=False)

    def create_feedback(self, validated_data, request):
        if validated_data.get("icon", None):
            icon = validated_data.pop("icon")
            validated_data["icon"] = ",".join(icon)
        validated_data["userUuid"] = User.objects.filter(uuid=request.user.get("uuid")).first()
        try:
            feedback = Feedback.objects.create(**validated_data)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("反馈失败")
        return feedback


class CoursesIndexSerializer(HaystackSerializer):
    """
    课程索引结果数据序列化器
    """
    object = CourseListSerializer(read_only=True)

    class Meta:
        index_classes = [CoursesIndex]
        fields = ("text", "object")


class CashAccountSerializer(serializers.ModelSerializer):
    """提现账户反馈序列化"""

    class Meta:
        model = CashAccount
        fields = ("uuid", "name", "accountType", "accountNO")


class CashAccountPostSerializer(serializers.Serializer):
    """提现账户反馈序列化"""
    name = serializers.CharField(required=True, error_messages={'required': '请输入账户名称'})
    accountType = serializers.IntegerField(required=True, error_messages={'required': '请选择账号类型'})
    accountNO = serializers.IntegerField(required=True, error_messages={'required': '请输入账号'})

    def validate(self, attrs):
        if CashAccount.objects.filter(accountType=attrs["accountType"], accountNO=attrs["accountNO"]).first():
            raise ParamError("账户信息已存在")
        return attrs

    def create_cash_account(self, validated_data, request):
        """添加账户"""
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        validated_data["userUuid"] = user
        try:
            cashAccount = CashAccount.objects.create(**validated_data)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("新建失败")
        return cashAccount

    def update_cash_account(self, instance, validated_data):
        """修改账户"""
        name = validated_data.get("name", None)
        accountType = validated_data.get("accountType", None)
        accountNO = validated_data.get("accountNO", None)
        try:
            if name:
                instance.name = name
            if accountNO:
                instance.accountNO = accountNO
            if accountType:
                instance.accountType = accountType
            instance.save()
        except Exception as e:
            logging.error(str(e))
            raise ParamError("更新失败")
        return instance


class PromoteSerializer(CourseListSerializer):
    """推广中心序列化"""
    share = serializers.SerializerMethodField(read_only=True)
    coupons = serializers.SerializerMethodField(read_only=True)

    def get_share(self, obj):
        selfUuid = self.context["request"].user.get("uuid")
        user = User.objects.filter(uuid=selfUuid).first()
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods or not goods.rewardStatus:
            return None
        data = {
            "shareUrl": obj.shareUrl,
            "shareImg": obj.shareImg,
            "avatar": user.avatar,
            "userUuid": user.uuid,
            "nickName": user.nickName,
            "realPrice": goods.realPrice,
            "rewardPercent": goods.rewardPercent,
            "courseUuid": obj.uuid
        }
        return data

    @staticmethod
    def get_coupons(obj):
        goods = Goods.objects.filter(content=obj.uuid).first()
        if not goods:
            return None
        objInfo = goods.goodsCouponsUuid.filter(q6).filter(couponType=1, totalNumber__gt=F("receivedNumber")).first()
        if not objInfo:
            return None
        return CouponsSerializer(objInfo, many=False).data

    class Meta:
        model = Courses
        fields = (
            "name", "startTime", "endTime", "icon", "intro", "originalPrice", "realPrice", "courseType", "duration",
            "expert", "uuid", "vPopularity", "discount", "chapterStyle", "share", "coupons")


class PromoteCouponsSerializer(CouponsSerializer):
    course = serializers.SerializerMethodField(read_only=True)

    def get_course(self, obj):
        uuid = obj.goodsUuid.content
        course = Courses.objects.filter(uuid=uuid).first()
        if not course:
            return None
        return CourseListSerializer(course, many=False).data

    class Meta:
        model = Coupons
        fields = (
            "uuid", "name", "startTime", "endTime", "couponType", "accountMoney", "money", "price", "isReceive",
            "course")


class StudyHistoryCourseSerializer(CourseListSerializer):
    class Meta:
        model = Courses
        fields = ("uuid", "name", "intro")


class StudyHistorySerializer(serializers.ModelSerializer):
    """学习历史序列化"""
    course = serializers.SerializerMethodField(read_only=True)
    createTime = serializers.SerializerMethodField(read_only=True)

    def get_createTime(self, obj):
        return datetime_to_unix(obj.createTime)

    def get_course(self, obj):
        return StudyHistoryCourseSerializer(obj.courseUuid).data

    class Meta:
        model = Behavior
        fields = ("uuid", "createTime", "course")


class BuyCoursesSerializer(serializers.ModelSerializer):
    """学习历史序列化"""
    course = serializers.SerializerMethodField(read_only=True)
    createTime = serializers.SerializerMethodField(read_only=True)

    def get_createTime(self, obj):
        return datetime_to_unix(obj.createTime)

    def get_course(self, obj):
        return CourseListSerializer(obj.courseUuid).data

    class Meta:
        model = Behavior
        fields = ("uuid", "createTime", "course")


class BillsCoursesSerializer(CourseListSerializer):
    class Meta:
        model = Courses
        fields = ("name", "expert", "uuid", "coursePermission")


class BillsSerializer(serializers.ModelSerializer):
    """流水序列化"""
    course = serializers.SerializerMethodField(read_only=True)
    wechatName = serializers.SerializerMethodField(read_only=True)
    createTime = serializers.SerializerMethodField(read_only=True)

    def get_course(self, obj):
        if obj.billType == 1:
            courseInfo = Courses.objects.filter(uuid=obj.remarks).first()
            return BillsCoursesSerializer(courseInfo, many=False).data
        return None

    def get_wechatName(self, obj):
        if obj.billType == 2:
            return obj.userUuid.userWechatUuid.first().name
        return None

    def get_createTime(self, obj):
        return datetime_to_unix(obj.createTime)

    class Meta:
        model = Bill
        fields = ("uuid", "billType", "money", "wechatName", "course", "createTime")
