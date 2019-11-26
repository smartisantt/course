import threading

from rest_framework import serializers
import time
from client.models import Chats
from common.models import *
from common.rePattern import TEL_PATTERN, CheckPhone
from manager.serializers import LiveCourseBannerPostSerializer, LiveCourseBannerSerializer
from utils.errors import ParamError
from utils.msg import *
from utils.ppt2png import get_sts_token, change, get_res
from utils.timeTools import timeChange
from django.db import transaction
from django.db.models.aggregates import Count, Sum, Max


class ExpertNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experts
        fields = (
            "uuid", "avatar", "name")


class CourseSourceUrlSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseSource
        fields = ("uuid", "name", "sourceUrl")


class LiveCourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiveCourse
        fields = ("uuid", "name")


class CourseSelectSerializer(serializers.ModelSerializer):
    chapters = serializers.SerializerMethodField()
    experts = serializers.SerializerMethodField()
    chapterStyle = serializers.SerializerMethodField()
    startTime = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    realPrice = serializers.SerializerMethodField()
    preChapter = serializers.SerializerMethodField()
    courseSource = serializers.SerializerMethodField()


    @staticmethod
    def get_chapters(obj):
        queryset = Chapters.objects.filter(courseUuid=obj.uuid).all().count()
        return queryset

    @staticmethod
    def get_experts(obj):
        queryset = Experts.objects.filter(uuid=obj.expertUuid_id).first()
        if queryset:
            return ExpertNameSerializer(queryset).data
        return None

    @staticmethod
    def get_chapterStyle(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).first()
        if queryset:
            return queryset.chapterStyle
        return ""

    @staticmethod
    def get_startTime(obj):
        try:
            queryset = timeChange(obj.startTime, 1)
        except:
            queryset = None
        return queryset

    @staticmethod
    def get_duration(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).aggregate(nums=Sum("duration"))
        return queryset["nums"]

    @staticmethod
    def get_realPrice(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.realPrice
        return None

    @staticmethod
    def get_preChapter(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).count()
        if queryset:
            return queryset
        return None


    @staticmethod
    def get_courseSource(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).first()
        if queryset:
            courseSource = queryset.courseSourceUuid
            return CourseSourceUrlSerializer(courseSource).data
        return None


    @staticmethod
    def get_liveCourseUuid(obj):
        chapter = Chapters.objects.filter(courseUuid=obj).first()
        if not chapter:
            return None
        return None


    class Meta:
        model = Courses
        fields = (
            "uuid", "courseType", "createTime", "updateTime", "courseBanner", "name", "coursePermission",
            "updateStatus", "preChapter",
            "experts",
            "realPrice", "status", "startTime", "chapters", "chapterStyle", "duration","courseSource")


class courseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("uuid",)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("uuid", "nickName")


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("uuid", "name")


class CourseBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ("uuid", "name")


class CourseSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSource
        fields = ("uuid", "name")


class SectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("uuid", "name")


class CourseInfoSerializer(serializers.ModelSerializer):
    # courseSection = courseSectionSerializer("courseSections",many=True)
    mc = serializers.SerializerMethodField()
    chapterStyle = serializers.SerializerMethodField()
    inviter = serializers.SerializerMethodField()
    courseSourceUuid = serializers.SerializerMethodField()
    tags = TagsSerializer('tags', many=True)
    relatedCourse = CourseBasicSerializer('relatedCourse', many=True)
    isCoupon = serializers.SerializerMethodField()
    tryInfoUuid = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    startTime = serializers.SerializerMethodField()
    experts = serializers.SerializerMethodField()
    rewardStatus = serializers.SerializerMethodField()
    rewardPercent = serializers.SerializerMethodField()
    originalPrice = serializers.SerializerMethodField()
    realPrice = serializers.SerializerMethodField()
    courseSection = serializers.SerializerMethodField()
    liveCourseUuid = serializers.SerializerMethodField()
    liveCourseBanner = serializers.SerializerMethodField()

    @staticmethod
    def get_mc(obj):
        queryset = ChatsRoom.objects.filter(roomChapterUuid__courseUuid=obj).first()
        if queryset:
            return UserSerializer(queryset.mcUuid).data
        return {}

    @staticmethod
    def get_startTime(obj):
        try:
            queryset = timeChange(obj.startTime, 1)
        except:
            queryset = None
        return queryset

    @staticmethod
    def get_chapterStyle(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).first()
        if queryset:
            return queryset.chapterStyle
        return ""

    @staticmethod
    def get_inviter(obj):
        queryset = ChatsRoom.objects.filter(roomChapterUuid__courseUuid=obj).first()
        if queryset:
            return UserSerializer(queryset.inviterUuid, many=True).data
        return []

    @staticmethod
    def get_courseSourceUuid(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).first()
        if queryset:
            return CourseSourceSerializer(queryset.courseSourceUuid).data
        return {}

    @staticmethod
    def get_liveCourseUuid(obj):
        chapter = Chapters.objects.filter(courseUuid=obj).first()
        if not chapter:
            return None
        if not chapter.roomUuid:
            return None
        if not chapter.roomUuid.liveCourseUuid:
            return None
        if not chapter.roomUuid.liveCourseUuid.uuid:
            return None
        return LiveCourseSerializer(chapter.roomUuid.liveCourseUuid).data

    @staticmethod
    def get_liveCourseBanner(obj):
        chapter = Chapters.objects.filter(courseUuid=obj).first()
        if not chapter:
            return None
        if not chapter.roomUuid:
            return None
        if not chapter.roomUuid.liveCourseUuid:
            return None
        if not chapter.roomUuid.liveCourseUuid.liveCourseBannerUuid:
            return None
        return LiveCourseBannerSerializer(chapter.roomUuid.liveCourseUuid.liveCourseBannerUuid).data

    @staticmethod
    def get_isCoupon(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.isCoupon
        return ""

    @staticmethod
    def get_tryInfoUuid(obj):
        queryset = Chapters.objects.filter(courseUuid=obj).first()
        if queryset:
            return CourseSourceSerializer(queryset.tryInfoUuid).data
        return {}

    @staticmethod
    def get_keywords(obj):
        keywords = obj.keywords
        if keywords:
            return keywords.split(',')
        return []

    @staticmethod
    def get_experts(obj):
        queryset = Experts.objects.filter(uuid=obj.expertUuid_id).first()
        if queryset:
            return ExpertNameSerializer(queryset).data
        return None

    @staticmethod
    def get_rewardStatus(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.rewardStatus
        return None

    @staticmethod
    def get_rewardPercent(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.rewardPercent
        return None

    @staticmethod
    def get_originalPrice(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.originalPrice
        return None

    @staticmethod
    def get_realPrice(obj):
        queryset = Goods.objects.filter(content=obj.uuid).first()
        if queryset:
            return queryset.realPrice
        return None

    @staticmethod
    def get_courseSection(obj):
        queryset = Section.objects.filter(courses=obj).all()
        if queryset:
            return SectionBasicSerializer(queryset, many=True).data
        return None

    class Meta:
        model = Courses
        fields = (
            "courseType", "name", "subhead", "briefIntro", "chapterStyle", "startTime", "experts", "mc",
            "preChapter", "inviter", "courseSourceUuid", "courseBanner", "courseThumbnail", "shareImg", "infoType",
            "info", "tags", "coursePermission", "originalPrice", "realPrice", "rewardStatus", "rewardPercent", "gifts",
            "keywords", "vPopularity", "courseSection", "relatedCourse", "mustRead", "isCoupon",
            "tryInfoUuid", "liveCourseUuid", "liveCourseBanner")


class CourseSaveSerializer(serializers.ModelSerializer):
    courseType = serializers.ChoiceField(choices=COURSE_TYPE_CHOICES, required=True,
                                         error_messages={"required": "课程类型必填", "choices": "课程类型有误"})
    name = serializers.CharField(min_length=2,
                                 max_length=20,
                                 required=True,
                                 error_messages={
                                     'min_length': "标题最少两个字符",
                                     'max_length': "标题最多20个字符"})
    subhead = serializers.CharField(max_length=30,
                                    required=False,
                                    allow_null=True,
                                    error_messages={
                                        'max_length': "副标题最多30个字符"
                                    })
    expertUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid", required=True,
                                              queryset=Experts.objects.filter(enable=1),
                                              error_messages={"does_not_exist": "对象不可选或不存在"})
    briefIntro = serializers.CharField(max_length=200,
                                       required=False,
                                       allow_null=True,
                                       error_messages={
                                           "max_length": "简介最多200个字"
                                       })
    preChapter = serializers.IntegerField(min_value=0,
                                          required=False,
                                          allow_null=True,
                                          error_messages={'required': "预计章节数量必填",
                                                          "min_value": "最小章节数0"
                                                          })
    chapterStyle = serializers.ChoiceField(choices=COURSE_STYLE_CHOICES, required=False,allow_null=True,)  # 上课形式，1直播，2音频，3视频
    startTime = serializers.DateTimeField(required=False, allow_null=True)
    mc = serializers.SlugRelatedField(required=False, slug_field="uuid", queryset=User.objects.filter(status=1),
                                      allow_null=True, error_messages={"does_not_exist": "对象不可选或不存在"})
    inviter = serializers.SlugRelatedField(required=False, many=True, slug_field="uuid",
                                           queryset=User.objects.filter(status=1),
                                           allow_null=True, error_messages={"does_not_exist": "对象不可选或不存在"})
    courseSourceUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                    queryset=CourseSource.objects.filter(enable=1),
                                                    error_messages={"does_not_exist": "对象不可选或不存在"})
    tryInfoUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                               queryset=CourseSource.objects.filter(enable=1),
                                               error_messages={"does_not_exist": "对象不可选或不存在"})
    # 直播课课件 和 直播课banner #########################################
    liveCourseUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                  queryset=LiveCourse.objects.filter(enable=1),
                                                  error_messages={"does_not_exist": "对象不可选或不存在"})

    liveCourseBanner = serializers.DictField(required=False, allow_null=True)
    ######################################################

    courseBanner = serializers.CharField(required=True, max_length=1024, min_length=32,
                                         error_messages={"required": "封面信息必填",
                                                         "max_length": "封面信息有误",
                                                         "min_length": "封面信息有误"})
    courseThumbnail = serializers.CharField(required=True, max_length=1024, min_length=32,
                                            error_messages={"required": "缩略图必填",
                                                            "max_length": "缩略图信息有误",
                                                            "min_length": "缩略图信息有误"})
    shareImg = serializers.CharField(required=False, max_length=1024, min_length=16,
                                     error_messages={"max_length": "分享图信息有误",
                                                     "min_length": "分享图信息有误"},allow_null=True)
    infoType = serializers.ChoiceField(choices=INFO_TYPE_CHOICES, required=True)
    info = serializers.CharField(required=True, error_messages={"required": "课程介绍必填"})
    tags = serializers.SlugRelatedField(many=True, allow_null=False, required=True, slug_field="uuid",
                                        queryset=Tags.objects.filter(tagType=1),
                                        error_messages={"does_not_exist": "对象不可选或不存在"})
    coursePermission = serializers.ChoiceField(choices=COURSES_PERMISSION_CHOICES, required=True,

                                               error_messages={"required": "上课权限必填", "choices": "权限类型有误"})
    originalPrice = serializers.IntegerField(min_value=0, required=True,
                                             error_messages={"min_value": "价格设置有误", "required": "划线价必填"})
    realPrice = serializers.IntegerField(min_value=0, required=True,
                                         error_messages={"min_value": "价格设置有误", "required": "真实价格必填"})
    rewardStatus = serializers.NullBooleanField(required=True, error_messages={"required": "是否分销必填"})
    rewardPercent = serializers.IntegerField(max_value=100, min_value=0,
                                             error_messages={"required": "分销比例必填", "min_value": "分销比列有误",
                                                             "max_value": "分销比列有误"})
    gifts = serializers.SlugRelatedField(required=True, many=True, slug_field="uuid", allow_null=True,
                                         queryset=Goods.objects.filter(isGift=True),
                                         error_messages={"does_not_exist": "对象不可选或不存在"})
    keywords = serializers.ListField(child=serializers.CharField(), max_length=10)
    vPopularity = serializers.IntegerField(default=0, required=False, min_value=0,
                                           error_messages={"min_value": "虚拟人气值有误"},allow_null=True)
    relatedCourse = serializers.SlugRelatedField(many=True, slug_field="uuid", allow_null=True, required=False,  # 关联课程
                                                 queryset=Courses.objects.exclude(status=4),
                                                 error_messages={"does_not_exist": "对象不可选或不存在"})
    courseSection = serializers.SlugRelatedField(many=True, slug_field="uuid", allow_null=False, required=True,
                                                 queryset=Section.objects.filter(),
                                                 error_messages={"does_not_exist": "对象不可选或不存在"})

    mustRead = serializers.CharField(required=True)
    isCoupon = serializers.NullBooleanField(required=True)

    def validate(self, data):
        courseType = data["courseType"]  # 课程类型
        preChapter = data.get("preChapter", None)
        chapterStyle = data.get("chapterStyle", None)
        startTime = data.get("startTime", None)
        mc = data.get("mc", None)
        courseSourceUuid = data.get("courseSourceUuid", None)
        coursePermission = data["coursePermission"]
        originalPrice = data["originalPrice"]
        realPrice = data["realPrice"]
        rewardStatus = data["rewardStatus"]
        rewardPercent = data["rewardPercent"]
        if coursePermission == 1:
            # 校验课程价格
            if originalPrice != 0 or realPrice != 0:
                raise ParamError(COURSE_PRICE_ERROR)
        if originalPrice < realPrice:
            raise ParamError(COURSE_PRICE_ERROR)
        if not rewardStatus:
            # 校验分销比例
            if rewardPercent != 0:
                raise ParamError(REWARDS_PERCENT_ERROR)
        if int(courseType) == 2:
            # 校验系列课
            if not preChapter:
                raise ParamError(PRE_CHAPTER_ERROR)
        elif int(courseType) == 1:
            # 校验单次课相关
            if not chapterStyle:
                raise ParamError(CHAPTER_STYLE_NULL_ERROR)
            if chapterStyle == 1:
                if not startTime or not mc:
                    raise ParamError(START_MC_ERROR)
                nowTime = time.time() * 1000
                if timeChange(startTime, 3) - nowTime < 595:
                    raise ParamError(START_TIME_ERROR)
                ########################################################
                if not data.get("liveCourseUuid"):
                    raise ParamError(LIVE_COURSE_NOT_EXISTS)
                if data.get("liveCourseBanner"):
                    a = LiveCourseBannerPostSerializer(data=data['liveCourseBanner'])
                    a.is_valid(raise_exception=True)
                ########################################################
            if chapterStyle == 2:
                if not courseSourceUuid:
                    raise ParamError(COURSE_SOURCE_ERROR)
                # 校验课件类型
                if courseSourceUuid.sourceType != 2:
                    raise ParamError(COURSE_SOURCE_TYPE_ERROR)
            if chapterStyle == 3:
                # 校验课件类型
                if not courseSourceUuid:
                    raise ParamError(COURSE_SOURCE_ERROR)
                if courseSourceUuid.sourceType != 1:
                    raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        return data

    def create_chat_room(self, validated_data):
        """
        创建聊天室
        """
        chatRoom_dict = {}
        chatRoom_dict["name"] = validated_data["name"]
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
        chatRoom_dict["startTime"] = startTime
        chatRoom_dict["banner"] = validated_data["courseBanner"]
        chatRoom_dict["liveCourseUuid"] = validated_data["liveCourseUuid"]
        chatRoom_dict["mcUuid"] = validated_data.get("mc", None)
        chatRoom_dict["studyNum"] = validated_data.get("vPopularity", 0)
        chatRoom_dict["expertUuid"] = validated_data.get("expertUuid", None)
        chat_room = ChatsRoom.objects.create(**chatRoom_dict)
        inviter = validated_data.get("inviter", None)
        if inviter:
            chat_room.inviterUuid.set(inviter)
        return chat_room

    #########################################################
    def update_live_course(self, validated_data):
        if validated_data.get("liveCourseBanner"):
            liveCourse = validated_data["liveCourseUuid"]
            liveCourseBanner = LiveCourseBanner.objects.create(
                name=validated_data["liveCourseBanner"]["name"],
                sourceUrl=validated_data["liveCourseBanner"]["sourceUrl"],
                sourceType=validated_data["liveCourseBanner"]["sourceType"],
                fileSize=validated_data["liveCourseBanner"]["fileSize"],
                duration=validated_data["liveCourseBanner"]["duration"]
            )
            if validated_data["liveCourseBanner"]["sourceType"] == 3:
                cli = get_sts_token()
                taskid = change(cli, validated_data["liveCourseBanner"]["sourceUrl"].split("/")[-1],
                                validated_data["liveCourseBanner"]["sourceUrl"].split("/")[2].split(".")[0])
                t = threading.Thread(target=get_res,
                                     args=(
                                         cli,
                                         taskid,
                                         validated_data["liveCourseBanner"]["sourceUrl"],
                                         liveCourseBanner.uuid)
                                     )
                t.start()
            liveCourse.liveCourseBannerUuid = liveCourseBanner
            liveCourse.save()
            return liveCourse
    #########################################################

    def create_chapter(self, validated_data, instance, chat_room):
        """
        创建章节
        """
        chapter_dict = {}
        chapter_dict["duration"] = instance.duration
        chapter_dict["courseUuid"] = instance
        chapter_dict["courseSourceUuid"] = validated_data.get("courseSourceUuid", None)
        chapter_dict["expertUuid"] = instance.expertUuid
        chapter_dict["tryInfoUuid"] = validated_data.get("tryInfoUuid", None)
        chapter_dict["name"] = instance.name
        chapter_dict["chapterStyle"] = validated_data.get("chapterStyle", None)
        chapter_dict["roomUuid"] = chat_room
        chapter_dict["startTime"] = instance.startTime
        chapter_dict["chapterBanner"] = instance.courseBanner
        chapter_dict["info"] = instance.info
        chapter_dict["keywords"] = instance.keywords
        coursePermission = instance.coursePermission
        if chapter_dict["chapterStyle"] in [2, 3]:
            chapter_dict["updateStatus"] = 1
        chapter_dict["isTry"] = 1
        if coursePermission == 1:
            chapter_dict["isTry"] = 2
        chapter = Chapters.objects.create(**chapter_dict)
        return chapter

    def create_goods(self, validated_data, instance):
        goods_dict = {}
        goods_dict["name"] = instance.name
        goods_dict["content"] = instance.uuid
        goods_dict["icon"] = instance.courseBanner
        goods_dict["originalPrice"] = int(validated_data["originalPrice"]) * 100
        goods_dict["realPrice"] = int(validated_data["realPrice"]) * 100
        goods_dict["goodsType"] = instance.courseType
        goods_dict["inventory"] = 1000000
        goods_dict["rewardStatus"] = validated_data["rewardStatus"]
        goods_dict["rewardPercent"] = int(validated_data["rewardPercent"])
        goods_dict["isCoupon"] = validated_data["isCoupon"]

        goods = Goods.objects.create(**goods_dict)
        return goods

    def create(self, validated_data):
        course_dict = {}
        courseSource = validated_data.get("courseSourceUuid", None)
        if courseSource:
            course_dict["duration"] = courseSource.duration
        course_dict["courseType"] = validated_data["courseType"]  # 课程类型
        chapterStyle = validated_data.get("chapterStyle", None)  # 课程类型
        course_dict["name"] = validated_data["name"]
        course_dict["subhead"] = validated_data.get("subhead", None)
        course_dict["expertUuid"] = validated_data["expertUuid"]
        course_dict["briefIntro"] = validated_data.get("briefIntro", None)
        course_dict["preChapter"] = validated_data.get("preChapter", None)
        course_dict["courseBanner"] = validated_data["courseBanner"]
        course_dict["courseThumbnail"] = validated_data["courseThumbnail"]
        course_dict["shareImg"] = validated_data.get("shareImg", None)
        course_dict["infoType"] = validated_data["infoType"]
        course_dict["info"] = validated_data["info"]
        course_dict["coursePermission"] = validated_data["coursePermission"]
        if course_dict["courseType"] == 1:
            if chapterStyle in [2, 3]:
                course_dict["updateStatus"] = 1
        elif course_dict["courseType"] == 2:
            course_dict["updateStatus"] = 2
        keywords = validated_data.get("keywords", None)
        if keywords:
            course_dict["keywords"] = ",".join(keywords)
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
            course_dict["startTime"] = startTime
        course_dict["vPopularity"] = validated_data.get("vPopularity", None)
        course_dict["mustRead"] = validated_data["mustRead"]
        max_weight = Courses.objects.exclude(status=4).all().aggregate(Max('weight'))["weight__max"]
        course_dict["weight"] = max_weight + 1
        # 创建课程
        course = Courses.objects.create(**course_dict)
        gifts = validated_data["gifts"]
        tags = validated_data["tags"]
        # 关联礼物
        course.gifts.set(gifts)
        # 关联标签、相关课程，栏目
        course.tags.set(tags)
        isrelated = validated_data.get("relatedCourse", None)
        if isrelated:
            course.relatedCourse.set(isrelated)
        courseSection = validated_data["courseSection"]
        courseSection_list = []
        for i in courseSection:
            courseSection_list.append(SectionCourse(courseUuid=course, sectionUuid=i))
        SectionCourse.objects.bulk_create(courseSection_list)
        return course

    class Meta:
        model = Courses
        fields = (
            "uuid", "courseType", "courseSection", "mc", "originalPrice", "info", "gifts", "name", "subhead",
            "expertUuid",
            "briefIntro", "preChapter", "chapterStyle", "startTime", "inviter", "courseSourceUuid", "courseBanner",
            "courseThumbnail", "shareImg", "infoType", "tags", "coursePermission", "realPrice", "rewardStatus",
            "rewardPercent", "keywords", "vPopularity", "relatedCourse", "courseSection", "mustRead", "isCoupon",
            "tryInfoUuid", "liveCourseUuid", "liveCourseBanner")


class CourseUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2,
                                 max_length=20,
                                 required=True,
                                 error_messages={
                                     'min_length': "标题最少两个字符",
                                     'max_length': "标题最多20个字符"})
    subhead = serializers.CharField(max_length=30,
                                    required=False,
                                    allow_null=True,
                                    error_messages={
                                        'max_length': "副标题最多30个字符"
                                    })
    expertUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid", required=True,
                                              queryset=Experts.objects.filter(enable=1),
                                              error_messages={"required": "主讲专家有误", "does_not_exist": "对象不可选或不存在"})
    briefIntro = serializers.CharField(max_length=200,
                                       required=False,
                                       allow_null=True,
                                       error_messages={
                                           "max_length": "简介最多200个字"
                                       })
    preChapter = serializers.IntegerField(min_value=0,
                                          required=False,
                                          allow_null=True,
                                          error_messages={'required': "预计章节数量必填",
                                                          "min_value": "最小章节数0"
                                                          })
    startTime = serializers.DateTimeField(required=False,allow_null=True)
    mc = serializers.SlugRelatedField(required=False, slug_field="uuid", queryset=User.objects.filter(status=1),
                                      allow_null=True, error_messages={"does_not_exist": "对象不可选或不存在"})
    inviter = serializers.SlugRelatedField(required=False, many=True, slug_field="uuid",
                                           queryset=User.objects.filter(status=1),
                                           allow_null=True, error_messages={"does_not_exist": "对象不可选或不存在"})
    courseSourceUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                    queryset=CourseSource.objects.filter(enable=1),
                                                    error_messages={"does_not_exist": "对象不可选或不存在"})
    tryInfoUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                               queryset=CourseSource.objects.filter(enable=1),
                                               error_messages={"does_not_exist": "对象不可选或不存在"})

    courseBanner = serializers.CharField(required=True, max_length=1024, min_length=32,
                                         error_messages={"required": "封面信息必填",
                                                         "max_length": "封面信息有误",
                                                         "min_length": "封面信息有误"})
    courseThumbnail = serializers.CharField(required=True, max_length=1024, min_length=32,
                                            error_messages={"required": "缩略图必填",
                                                            "max_length": "缩略图信息有误",
                                                            "min_length": "缩略图信息有误"})
    shareImg = serializers.CharField(required=False, max_length=1024, min_length=16,allow_null=True,
                                     error_messages={"max_length": "分享图信息有误",
                                                     "min_length": "分享图信息有误"})
    infoType = serializers.ChoiceField(choices=INFO_TYPE_CHOICES, required=True)
    info = serializers.CharField(required=True, error_messages={"required": "课程介绍必填"})
    tags = serializers.SlugRelatedField(many=True, allow_null=False, required=True, slug_field="uuid",
                                        queryset=Tags.objects.filter(tagType=1),
                                        error_messages={"does_not_exist": "对象不可选或不存在"})
    coursePermission = serializers.ChoiceField(choices=COURSES_PERMISSION_CHOICES, required=True,
                                               error_messages={"required": "上课权限必填", "choices": "权限类型有误"})
    originalPrice = serializers.IntegerField(min_value=0, required=True,
                                             error_messages={"min_value": "价格设置有误", "required": "划线价必填"})
    realPrice = serializers.IntegerField(min_value=0, required=True,
                                         error_messages={"min_value": "价格设置有误", "required": "真实价格必填"})
    rewardStatus = serializers.NullBooleanField(required=True, error_messages={"required": "是否分销必填"})
    rewardPercent = serializers.IntegerField(max_value=100, min_value=0,
                                             error_messages={"required": "分销比例必填", "min_value": "分销比列有误",
                                                             "max_value": "分销比列有误"})
    gifts = serializers.SlugRelatedField(required=True, many=True, slug_field="uuid", allow_null=True,
                                         queryset=Goods.objects.filter(isGift=True),
                                         error_messages={"does_not_exist": "对象不可选或不存在"})
    # keywords = serializers.CharField(max_length=512, required=False, error_messages={"max_length": "关键词长度有误"})
    keywords = serializers.ListField(child=serializers.CharField(), max_length=10)
    vPopularity = serializers.IntegerField(default=0, required=False,allow_null=True, min_value=0,
                                           error_messages={"min_value": "虚拟人气值有误"})
    relatedCourse = serializers.SlugRelatedField(many=True, slug_field="uuid", allow_null=True,  # 关联课程
                                                 queryset=Courses.objects.exclude(status=4),
                                                 error_messages={"does_not_exist": "对象不可选或不存在"})
    courseSection = serializers.SlugRelatedField(many=True, slug_field="uuid", allow_null=False, required=True,
                                                 queryset=Section.objects.filter(),
                                                 error_messages={"does_not_exist": "对象不可选或不存在"})

    mustRead = serializers.CharField(required=True)
    isCoupon = serializers.NullBooleanField(required=True)
    # 直播课课件 和 直播课banner #########################################
    liveCourseUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                  queryset=LiveCourse.objects.filter(enable=1),
                                                  error_messages={"does_not_exist": "对象不可选或不存在"})

    liveCourseBanner = serializers.DictField(required=False, allow_null=True)
    ######################################################

    def check_params(self, instance, data):
        chapter = Chapters.objects.filter(courseUuid=instance).first()
        preChapter = data.get("preChapter", None)
        startTime = data.get("startTime", None)
        mc = data.get("mc", None)
        courseSourceUuid = data.get("courseSourceUuid", None)
        coursePermission = data["coursePermission"]
        originalPrice = data["originalPrice"]
        realPrice = data["realPrice"]
        rewardStatus = data["rewardStatus"]
        rewardPercent = data["rewardPercent"]
        if coursePermission == 1:
            # 校验课程价格
            if originalPrice != 0 or realPrice != 0:
                raise ParamError(COURSE_PRICE_ERROR)
        if originalPrice < realPrice:
            raise ParamError(COURSE_PRICE_ERROR)
        if not rewardStatus:
            # 校验分销比例
            if rewardPercent != 0:
                raise ParamError(REWARDS_PERCENT_ERROR)
        if instance.courseType == 2:
            # 校验系列课
            if not preChapter:
                raise ParamError(PRE_CHAPTER_ERROR)
        elif instance.courseType == 1:
            if not chapter:
                raise ParamError(CHAPTER_NOT_EXISTS)
            # 校验单次课相关
            if chapter.chapterStyle == 1:
                # 校验章节类型
                if not startTime or not mc:
                    raise ParamError(START_MC_ERROR)
                nowTime = time.time() * 1000
                if timeChange(startTime, 3) - nowTime < 595:
                    raise ParamError(START_TIME_ERROR)
                if chapter.startTime - nowTime <= 595:
                    raise ParamError(START_TIME_FORBIDDEN)
                #####################################################
                if data.get("liveCourseBanner"):
                    a = LiveCourseBannerPostSerializer(data=data['liveCourseBanner'])
                    a.is_valid(raise_exception=True)
                if not data.get("liveCourseUuid"):
                    raise ParamError(LIVE_COURSE_NOT_EXISTS)
                #####################################################
            if chapter.chapterStyle == 2:
                # 校验课件类型
                if not courseSourceUuid:
                    raise ParamError(COURSE_SOURCE_ERROR)
                if courseSourceUuid.sourceType != 2:
                    raise ParamError(COURSE_SOURCE_TYPE_ERROR)
            if chapter.chapterStyle == 3:
                # 校验课件类型
                if not courseSourceUuid:
                    raise ParamError(COURSE_SOURCE_ERROR)
                elif courseSourceUuid.sourceType != 1:
                    raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        return data

    ############################################################
    def update_live_course(self, validated_data):
        if validated_data.get("liveCourseBanner"):
            liveCourse = validated_data["liveCourseUuid"]
            liveCourseBanner = LiveCourseBanner.objects.create(
                name=validated_data["liveCourseBanner"]["name"],
                sourceUrl=validated_data["liveCourseBanner"]["sourceUrl"],
                sourceType=validated_data["liveCourseBanner"]["sourceType"],
                fileSize=validated_data["liveCourseBanner"]["fileSize"],
                duration=validated_data["liveCourseBanner"]["duration"]
            )
            # ppt转图片
            if validated_data["liveCourseBanner"]["sourceType"] == 3:
                cli = get_sts_token()
                taskid = change(cli, validated_data["liveCourseBanner"]["sourceUrl"].split("/")[-1],
                                validated_data["liveCourseBanner"]["sourceUrl"].split("/")[2].split(".")[0])
                t = threading.Thread(target=get_res,
                                     args=(
                                         cli,
                                         taskid,
                                         validated_data["liveCourseBanner"]["sourceUrl"],
                                         liveCourseBanner.uuid)
                                     )
                t.start()
            liveCourse.liveCourseBannerUuid = liveCourseBanner
            liveCourse.save()
            return liveCourse
    ############################################################

    def updateCourse(self, instance, validated_data):
        shareImg = instance.shareImg
        courseSource = validated_data.get("courseSourceUuid", None)
        if courseSource:
            instance.duration = courseSource.duration
        instance.name = validated_data["name"]
        instance.subhead = validated_data.get("subhead", instance.subhead)
        instance.expertUuid = validated_data["expertUuid"]
        instance.briefIntro = validated_data.get("briefIntro", instance.briefIntro)
        instance.courseBanner = validated_data["courseBanner"]
        instance.courseThumbnail = validated_data["courseThumbnail"]
        instance.shareImg = validated_data.get("shareImg", str(shareImg))
        instance.preChapter = validated_data.get("preChapter", instance.preChapter)
        instance.infoType = validated_data["infoType"]
        instance.info = validated_data["info"]
        instance.coursePermission = validated_data["coursePermission"]
        instance.originalPrice = int(validated_data["originalPrice"]) * 100
        instance.realPrice = int(validated_data["realPrice"]) * 100
        keywords = validated_data.get("keywords", instance.keywords)
        if keywords:
            instance.keywords = ",".join(keywords)
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
            instance.startTime = startTime
        instance.vPopularity = validated_data.get("vPopularity", instance.vPopularity)
        instance.mustRead = validated_data["mustRead"]
        # 创建课程

        gifts = validated_data["gifts"]
        tags = validated_data["tags"]
        # 关联礼物
        instance.gifts.clear()
        instance.tags.clear()
        # 关联标签、相关课程，栏目
        instance.tags.set(gifts)
        instance.tags.set(tags)
        isrelated = validated_data.get("relatedCourse", None)
        instance.relatedCourse.clear()
        if isrelated:
            instance.relatedCourse.set(isrelated)
        instance.save()
        courseSection = validated_data["courseSection"]
        for i in courseSection:
            if not SectionCourse.objects.filter(courseUuid=instance, sectionUuid=i).exists():
                SectionCourse(courseUuid=instance, sectionUuid=i).save()
        existSection = SectionCourse.objects.filter(courseUuid=instance).exclude(
            sectionUuid__in=courseSection).delete()
        return instance

    def updateGoods(self, instance, validated_data):
        goods = Goods.objects.filter(content=instance.uuid).first()
        if goods:
            goods.name = instance.name
            goods.content = instance.uuid
            goods.icon = instance.courseBanner
            goods.originalPrice = instance.originalPrice
            goods.realPrice = instance.realPrice
            goods.goodsType = instance.courseType
            goods.inventory = 1000000
            goods.rewardStatus = validated_data["rewardStatus"]
            goods.rewardPercent = validated_data["rewardPercent"]
            goods.isCoupon = validated_data["isCoupon"]
            goods.save()
        return goods

    def update_chapter(self, validated_data, instance, chat_room):
        chapter_dict = Chapters.objects.filter(courseUuid=instance).first()
        if not chapter_dict:
            chapter_dict = Chapters()
        chapter_dict.courseSourceUuid = validated_data.get("courseSourceUuid", chapter_dict.courseSourceUuid)
        chapter_dict.expertUuid = instance.expertUuid
        chapter_dict.tryInfoUuid = validated_data.get("tryInfoUuid", chapter_dict.tryInfoUuid)
        chapter_dict.name = instance.name
        chapter_dict.duration = instance.duration
        chapter_dict.roomUuid = chat_room
        chapter_dict.startTime = instance.startTime
        chapter_dict.chapterBanner = instance.courseBanner
        chapter_dict.info = instance.info
        chapter_dict.keywords = instance.keywords
        coursePermission = instance.coursePermission
        chapter_dict.isTry = 1
        if coursePermission == 1:
            chapter_dict.isTry = 2
        chapter_dict.save()
        return chapter_dict

    def update_chat_room(self, courseInstance, validated_data):
        chatRoom_dict = ChatsRoom.objects.filter(roomChapterUuid__courseUuid = courseInstance).first()
        if not chatRoom_dict:
            chatRoom_dict = ChatsRoom()
        chatRoom_dict.name = courseInstance.name
        chatRoom_dict.startTime = courseInstance.startTime
        chatRoom_dict.banner = courseInstance.courseBanner
        chatRoom_dict.liveCourseUuid = validated_data.get("liveCourseUuid", chatRoom_dict.liveCourseUuid)
        chatRoom_dict.mcUuid = validated_data.get("mc", chatRoom_dict.mcUuid)
        chatRoom_dict.studyNum = validated_data.get("vPopularity", chatRoom_dict.studyNum)
        chatRoom_dict.expertUuid = courseInstance.expertUuid
        chatRoom_dict.save()
        inviter = validated_data.get("inviter", None)
        if inviter:
            chatRoom_dict.inviterUuid.clear()
            chatRoom_dict.inviterUuid.set(inviter)
        return chatRoom_dict

    class Meta:
        model = Courses
        fields = (
            "uuid", "courseType", "courseSection", "mc", "originalPrice", "info", "gifts", "name", "subhead",
            "expertUuid",
            "briefIntro", "preChapter", "startTime", "inviter", "courseSourceUuid", "courseBanner",
            "courseThumbnail", "shareImg", "infoType", "tags", "coursePermission", "realPrice", "rewardStatus",
            "rewardPercent", "keywords", "vPopularity", "relatedCourse", "courseSection", "mustRead", "isCoupon",
            "tryInfoUuid", "liveCourseUuid", "liveCourseBanner")


class CourseDeleteSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=COURSES_FORBIDDEN_CHOICES, required=True)

    def change_status(self, instance, data):
        if instance.status == data["status"]:
            raise ParamError(NOT_CHANGE_STATUS_ERROR)
        status = data["status"]
        goods = Goods.objects.filter(content=instance.uuid).all()
        chapters = Chapters.objects.filter(courseUuid=instance).all()
        sectioncourses = SectionCourse.objects.filter(courseUuid=instance).all()
        for sectioncourse in sectioncourses:
            if sectioncourse.status == 1:
                raise ParamError(FORBIDDEN_CHANGE_STATUS)
        for i in goods:
            i.status = status
            i.save()
        for n in chapters:
            n.status = status
            n.save()
        if status == 4:
            for m in sectioncourses:
                m.status = 3
                m.save()
        elif status in [2, 3]:
            for m in sectioncourses:
                m.status = 2
                m.save()
        instance.status = status
        instance.save()
        return True

    class Meta:
        model = Courses
        fields = ("status",)


class CourseUpdateStatusSerializer(serializers.ModelSerializer):
    updateStatus = serializers.ChoiceField(choices=COURSE_UPDATE_STATUS, required=True)

    def update_status(self, instance, data):
        if instance.updateStatus == data["updateStatus"]:
            raise ParamError(NOT_CHANGE_STATUS_ERROR)
        instance.updateStatus = data["updateStatus"]
        instance.save()
        return True

    class Meta:
        model = Courses
        fields = ("updateStatus",)


class ChaptersSelectSerializer(serializers.ModelSerializer):
    startTime = serializers.SerializerMethodField()
    expert = serializers.SerializerMethodField()
    courseSource = serializers.SerializerMethodField()

    @staticmethod
    def get_expert(obj):
        queryset = Experts.objects.filter(uuid=obj.expertUuid_id).first()
        if queryset:
            return ExpertNameSerializer(queryset).data
        return None

    @staticmethod
    def get_startTime(obj):
        try:
            queryset = timeChange(obj.startTime, 1)
        except:
            queryset = None
        return queryset
    @staticmethod
    def get_courseSource(obj):
        queryset = obj.courseSourceUuid
        if queryset:
            return CourseSourceUrlSerializer(queryset).data
        return None

    class Meta:
        model = Chapters
        fields = (
            "uuid", "serialNumber", "chapterBanner", "name", "chapterStyle", "updateStatus", "expert", "createTime",
            "startTime", "duration", "isTry", "status","courseSource")


class ChaptersInfoSerializer(serializers.ModelSerializer):
    courseSourceUuid = CourseSourceSerializer()
    tryInfoUuid = CourseSourceSerializer()
    expert = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    mc = serializers.SerializerMethodField()
    inviter = serializers.SerializerMethodField()
    startTime = serializers.SerializerMethodField()
    liveCourseUuid = serializers.SerializerMethodField()
    liveCourseBanner = serializers.SerializerMethodField()

    @staticmethod
    def get_liveCourseUuid(obj):
        if not obj.roomUuid:
            return None
        if not obj.roomUuid.liveCourseUuid:
            return None
        if not obj.roomUuid.liveCourseUuid.uuid:
            return None
        return LiveCourseSerializer(obj.roomUuid.liveCourseUuid).data

    @staticmethod
    def get_liveCourseBanner(obj):
        if not obj.roomUuid:
            return None
        if not obj.roomUuid.liveCourseUuid:
            return None
        if not obj.roomUuid.liveCourseUuid.liveCourseBannerUuid:
            return None
        return LiveCourseBannerSerializer(obj.roomUuid.liveCourseUuid.liveCourseBannerUuid).data

    @staticmethod
    def get_startTime(obj):
        try:
            queryset = timeChange(obj.startTime, 1)
        except:
            queryset = None
        return queryset

    @staticmethod
    def get_expert(obj):
        queryset = Experts.objects.filter(uuid=obj.expertUuid_id).first()
        if queryset:
            return ExpertNameSerializer(queryset).data
        return None

    @staticmethod
    def get_keywords(obj):
        keywords = obj.keywords
        if keywords:
            return keywords.split(',')
        return []

    @staticmethod
    def get_inviter(obj):
        queryset = ChatsRoom.objects.filter(roomChapterUuid=obj).first()
        if queryset:
            return UserSerializer(queryset.inviterUuid, many=True).data
        return []

    @staticmethod
    def get_mc(obj):
        queryset = ChatsRoom.objects.filter(roomChapterUuid=obj).first()
        if queryset:
            return UserSerializer(queryset.mcUuid).data
        return {}

    class Meta:
        model = Chapters
        fields = (
            "uuid", "serialNumber", "chapterBanner", "name", "chapterStyle", "updateStatus", "createTime", "startTime",
            "duration", "courseSourceUuid", "tryInfoUuid", "expert", "keywords",
            "status", "inviter", "mc", "liveCourseUuid", "liveCourseBanner")


class ChapterSaveSerializer(serializers.Serializer):
    courseUuid = serializers.SlugRelatedField(required=True, slug_field="uuid", allow_null=False,
                                              queryset=Courses.objects.filter(courseType=2).exclude(status=4),
                                              error_messages={"does_not_exist": "对象不可选或不存在"})
    name = serializers.CharField(
        max_length=20,
        required=True,
        error_messages={'required': "章节名必填",
                        'min_length': "标题最少两个字符",
                        'max_length': "标题最多20个字符"})
    chapterStyle = serializers.ChoiceField(choices=COURSE_STYLE_CHOICES, required=True)  # 上课形式，1直播，2音频，3视频
    courseSourceUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                    queryset=CourseSource.objects.filter(enable=1),
                                                    error_messages={"does_not_exist": "对象不可选或不存在"})
    tryInfoUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                               queryset=CourseSource.objects.filter(enable=1),
                                               error_messages={"does_not_exist": "对象不可选或不存在"})
    chapterBanner = serializers.CharField(required=True, max_length=1024, min_length=32,
                                          error_messages={"required": "封面信息必填",
                                                          "max_length": "封面信息有误",
                                                          "min_length": "封面信息有误"})
    keywords = serializers.ListField(child=serializers.CharField(), max_length=10,required=False,allow_null=True)
    startTime = serializers.DateTimeField(required=False, error_messages={'required': "开始时间必填"},allow_null=True)
    expertUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid", required=True,
                                              queryset=Experts.objects.filter(enable=1),
                                              error_messages={"required": "主讲专家有误", "does_not_exist": "对象已禁用或不存在"})
    mc = serializers.SlugRelatedField(required=False, slug_field="uuid", queryset=User.objects.filter(status=1),
                                      allow_null=True, error_messages={"does_not_exist": "对象已禁用或不存在"})
    inviter = serializers.SlugRelatedField(required=False, many=True, slug_field="uuid",
                                           queryset=User.objects.filter(status=1).all(),allow_null=True, error_messages={"does_not_exist": "对象已禁用或不存在"})
    status = serializers.ChoiceField(choices=COURSES_FORBIDDEN_CHOICES)
    # 章节管理 创建新的章节 直播课课件 和 直播课banner #########################################
    liveCourseUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                  queryset=LiveCourse.objects.filter(enable=1),
                                                  error_messages={"does_not_exist": "对象不可选或不存在"})

    liveCourseBanner = serializers.DictField(required=False, allow_null=True)
    ######################################################

    def validate(self, data):
        chapterStyle = data["chapterStyle"]
        courseSource = data.get("courseSourceUuid", None)
        mc = data.get("mc", None)
        startTime = data.get("startTime", None)
        # courseSource = CourseSource.objects.filter(uuid=courseSourceUuid).first()
        if chapterStyle != 1:
            # 当不是直播课， 校验必传课件
            if not courseSource:
                raise ParamError(COURSE_SOURCE_ERROR)
        if chapterStyle == 2:
            if courseSource.sourceType != 2:
                raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        elif chapterStyle == 3:
            if courseSource.sourceType != 1:
                raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        else:
            # 直播课校验
            ########################################################
            if not data.get("liveCourseUuid"):
                raise ParamError(LIVE_COURSE_NOT_EXISTS)
            if data.get("liveCourseBanner"):
                a = LiveCourseBannerPostSerializer(data=data['liveCourseBanner'])
                a.is_valid(raise_exception=True)
            ########################################################
            if not mc or not startTime:
                raise ParamError(START_MC_ERROR)
            nowTime = time.time() * 1000
            if timeChange(startTime, 3) - nowTime < 595:
                raise ParamError(START_TIME_ERROR)
        return data

    #########################################################
    def update_live_course(self, validated_data):
        if validated_data.get("liveCourseBanner"):
            liveCourse = validated_data["liveCourseUuid"]
            liveCourseBanner = LiveCourseBanner.objects.create(
                name=validated_data["liveCourseBanner"]["name"],
                sourceUrl=validated_data["liveCourseBanner"]["sourceUrl"],
                sourceType=validated_data["liveCourseBanner"]["sourceType"],
                fileSize=validated_data["liveCourseBanner"]["fileSize"],
                duration=validated_data["liveCourseBanner"]["duration"]
            )
            if validated_data["liveCourseBanner"]["sourceType"] == 3:
                cli = get_sts_token()
                taskid = change(cli, validated_data["liveCourseBanner"]["sourceUrl"].split("/")[-1],
                                validated_data["liveCourseBanner"]["sourceUrl"].split("/")[2].split(".")[0])
                t = threading.Thread(target=get_res,
                                     args=(
                                         cli,
                                         taskid,
                                         validated_data["liveCourseBanner"]["sourceUrl"],
                                         liveCourseBanner.uuid)
                                     )
                t.start()
            liveCourse.liveCourseBannerUuid = liveCourseBanner
            liveCourse.save()
            return liveCourse
    #########################################################

    def create_chatRoom(self, validated_data):
        """
        创建聊天室
        """
        chatRoom_dict = {}
        chatRoom_dict["name"] = validated_data["name"]
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
        chatRoom_dict["startTime"] = startTime
        chatRoom_dict["banner"] = validated_data.get("chapterBanner", None)
        chatRoom_dict["liveCourseUuid"] = validated_data["liveCourseUuid"]
        chatRoom_dict["mcUuid"] = validated_data.get("mc", None)
        chatRoom_dict["studyNum"] = validated_data.get("vPopularity", 0)
        chatRoom_dict["expertUuid"] = validated_data.get("expertUuid", None)
        chat_room = ChatsRoom.objects.create(**chatRoom_dict)
        inviter = validated_data.get("inviter", None)
        if inviter:
            chat_room.inviterUuid.set(inviter)
        return chat_room

    def create_chapter(self, validated_data):
        # todo； 添加章节
        chapter_dict = {}
        course = validated_data["courseUuid"]
        max_serialNumber = Chapters.objects.filter(courseUuid=course).aggregate(Max('serialNumber'))[
            "serialNumber__max"]
        if not max_serialNumber:
            max_serialNumber = 0
        chapter_dict["serialNumber"] = max_serialNumber + 1
        expert = validated_data.get("expertUuid", None)
        chapter_dict["expertUuid"] = expert
        chapter_dict["chapterStyle"] = validated_data["chapterStyle"]
        chapter_dict["chapterBanner"] = validated_data["chapterBanner"]
        chapter_dict["courseUuid"] = course
        chapter_dict["status"] = validated_data["status"]
        chapter_dict["name"] = validated_data["name"]
        chapter_dict["info"] = course.info
        chapter_dict["tryInfoUuid"] = validated_data.get("tryInfoUuid", None)
        if validated_data["chapterStyle"] != 1:
            chapter_dict["updateStatus"] = 1
        courseSource = validated_data.get("courseSourceUuid", None)
        chapter_dict["courseSourceUuid"] = courseSource
        if courseSource:
            chapter_dict["duration"] = courseSource.duration
        keywords = validated_data.get("keywords", None)
        if keywords:
            chapter_dict["keywords"] = ",".join(keywords)
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
            chapter_dict["startTime"] = startTime
        chapter = Chapters.objects.create(**chapter_dict)
        return chapter

    class Meta:
        model = Chapters
        fields = ("courseUuid", "name", "chapterStyle", "courseSourceUuid", "tryInfoUuid", "chapterBanner", "keywords",
                  "startTime", "expertUuid", "mc","inviter", "status")


class ChapterUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=20,
        required=True,
        error_messages={'required': "章节名必填",
                        'min_length': "标题最少两个字符",
                        'max_length': "标题最多20个字符"})
    courseSourceUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                    queryset=CourseSource.objects.filter(enable=1),
                                                    error_messages={"does_not_exist": "对象不可选或不存在"})
    tryInfoUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                               queryset=CourseSource.objects.filter(enable=1),
                                               error_messages={"does_not_exist": "对象不可选或不存在"})
    chapterBanner = serializers.CharField(required=True, max_length=1024, min_length=32,
                                          error_messages={"required": "封面信息必填",
                                                          "max_length": "封面信息有误",
                                                          "min_length": "封面信息有误"})
    keywords = serializers.ListField(child=serializers.CharField(), max_length=10)
    startTime = serializers.DateTimeField(required=False, allow_null=True)
    expertUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid", required=True,
                                              queryset=Experts.objects.filter(enable=1),
                                              error_messages={"required": "主讲专家有误", "does_not_exist": "对象不可选或不存在"})
    mc = serializers.SlugRelatedField(required=False, slug_field="uuid", queryset=User.objects.filter(status=1),allow_empty=True,
                                      allow_null=True, error_messages={"does_not_exist": "对象不可选或不存在"})
    inviter = serializers.SlugRelatedField(required=False, many=True, slug_field="uuid",allow_null=True,
                                           queryset=User.objects.filter(status=1),
                                            error_messages={"does_not_exist": "对象不可选或不存在"})
    status = serializers.ChoiceField(choices=COURSES_FORBIDDEN_CHOICES)
    # 章节管理 创建新的章节 直播课课件 和 直播课banner #########################################
    liveCourseUuid = serializers.SlugRelatedField(required=False, slug_field="uuid", allow_null=True,
                                                  queryset=LiveCourse.objects.filter(enable=1),
                                                  error_messages={"does_not_exist": "对象不可选或不存在"})

    liveCourseBanner = serializers.DictField(required=False, allow_null=True)
    ######################################################

    ############################################################
    def update_live_course(self, validated_data):
        if validated_data.get("liveCourseBanner"):
            liveCourse = validated_data["liveCourseUuid"]
            liveCourseBanner = LiveCourseBanner.objects.create(
                name=validated_data["liveCourseBanner"]["name"],
                sourceUrl=validated_data["liveCourseBanner"]["sourceUrl"],
                sourceType=validated_data["liveCourseBanner"]["sourceType"],
                fileSize=validated_data["liveCourseBanner"]["fileSize"],
                duration=validated_data["liveCourseBanner"]["duration"]
            )
            # ppt转图片
            if validated_data["liveCourseBanner"]["sourceType"] == 3:
                cli = get_sts_token()
                taskid = change(cli, validated_data["liveCourseBanner"]["sourceUrl"].split("/")[-1],
                                validated_data["liveCourseBanner"]["sourceUrl"].split("/")[2].split(".")[0])
                t = threading.Thread(target=get_res,
                                     args=(
                                         cli,
                                         taskid,
                                         validated_data["liveCourseBanner"]["sourceUrl"],
                                         liveCourseBanner.uuid)
                                     )
                t.start()
            liveCourse.liveCourseBannerUuid = liveCourseBanner
            liveCourse.save()
            return liveCourse

    ############################################################

    def check_params(self, instance, data):
        chapterStyle = instance.chapterStyle
        courseSource = data.get("courseSourceUuid", None)
        mc = data.get("mc", None)
        startTime = data.get("startTime", None)
        if chapterStyle != 1:
            if not courseSource:
                raise ParamError(COURSE_SOURCE_ERROR)
        if chapterStyle == 2:
            if courseSource.sourceType != 2:
                raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        elif chapterStyle == 3:
            if courseSource.sourceType != 1:
                raise ParamError(COURSE_SOURCE_TYPE_ERROR)
        else:
            # 直播课校验
            ########################################################
            if not data.get("liveCourseUuid"):
                raise ParamError(LIVE_COURSE_NOT_EXISTS)
            if data.get("liveCourseBanner"):
                a = LiveCourseBannerPostSerializer(data=data['liveCourseBanner'])
                a.is_valid(raise_exception=True)
            ########################################################
            if not mc or not startTime:
                raise ParamError(START_MC_ERROR)
            nowTime = time.time() * 1000
            if timeChange(startTime, 3) - nowTime < 595:
                raise ParamError(START_TIME_ERROR)
            if instance.startTime - nowTime <= 595:
                raise ParamError(START_TIME_FORBIDDEN)
        return data

    def updateChapter(self, instance, validated_data):
        # todo： 修改章节
        expert = validated_data.get("expertUuid", None)
        if not expert:
            course = Courses.objects.filter(chapterCourseUuid=instance).first()
            expert = course.expertUuid
        instance.expertUuid = expert
        instance.chapterBanner = validated_data["chapterBanner"]
        instance.status = validated_data["status"]
        instance.name = validated_data["name"]
        instance.tryInfoUuid = validated_data.get("tryInfoUuid", None)
        courseSource = validated_data.get("courseSourceUuid", None)
        instance.courseSourceUuid = courseSource
        if courseSource:
            instance.duration = courseSource.duration
        keywords = validated_data.get("keywords", None)
        if keywords:
            instance.keywords = ",".join(keywords)
        startTime = validated_data.get("startTime", None)
        if startTime:
            startTime = timeChange(startTime, 3)
            instance.startTime = startTime
        instance.save()
        return instance

    def update_chatRoom(self, instance, validated_data):
        """
        更新聊天室
        """
        chatRoom = instance.roomUuid
        if not chatRoom:
            raise ParamError(CHAT_ROOM_NOT_EXISTS)
        chatRoom.name = instance.name
        chatRoom.startTime = instance.startTime
        chatRoom.banner = instance.chapterBanner
        chatRoom.liveCourseUuid = validated_data.get("liveCourseUuid")
        chatRoom.mcUuid_id = validated_data.get("mc", None)
        chatRoom.expertUuid = validated_data.get("expertUuid", None)
        inviter = validated_data.get("inviter", None)
        if inviter:
            chatRoom.inviterUuid.clear()
            chatRoom.inviterUuid.set(inviter)
        chatRoom.save()
        return chatRoom


class ChapterDeleteSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=COURSES_FORBIDDEN_CHOICES, required=True)

    def change_status(self, instance, data):
        if instance.status == data["status"]:
            raise ParamError(NOT_CHANGE_STATUS_ERROR)
        status = data["status"]
        instance.status = status
        instance.save()
        return True

    class Meta:
        model = Courses
        fields = ("status",)


class ChapterExchangeSerializer(serializers.Serializer):
    objUuid = serializers.SlugRelatedField(required=True, slug_field="uuid", allow_null=True,
                                           queryset=Chapters.objects.filter(),
                                           error_messages={"does_not_exist": "对象不可选或不存在"})

    def change_serialNumber(self, instance, data):
        obj = data["objUuid"]
        objChapter = Chapters.objects.filter(uuid=obj).first()
        if instance.courseUuid != objChapter.courseUuid:
            raise ParamError(EXCHANGE_OBJ_ERROR)
        instance.serialNumber, objChapter.serialNumber = objChapter.serialNumber, instance.serialNumber
        objChapter.save()
        instance.save()
        return True
