#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time

from django.db.models import Max, Q, Sum
from django.db.models import Max
from django.db import transaction
from rest_framework import serializers

from client.models import Banner, MayLike
from common.models import *
from common.rePattern import TEL_PATTERN, CheckPhone
from utils.errors import ParamError
from utils.msg import *
from datetime import datetime

from utils.qFilter import BANNER_Q, HOT_SEARCH_Q, COURSE_LIVE_SEARCH_Q, COURSE_LIVE_Q, MAY_LIKE_Q, COURSE_Q
from utils.ppt2png import get_sts_token, change, get_res
from utils.timeTools import timeChange


class TagSaveSerializer(serializers.ModelSerializer):
    """新增标签序列化"""
    name = serializers.CharField(max_length=64, min_length=0, required=True,
                                 error_messages={"required": "标签名必填", "max_length": "标签名最多64个字"})
    parentUuid = serializers.CharField(max_length=32, required=False, allow_blank=True)
    weight = serializers.IntegerField(required=False, min_value=1, error_messages={"min_value": "顺序最小值为1"})
    tagType = serializers.ChoiceField(required=False, choices=TAG_CHOICES,
                                      error_messages={"invalid_choice": "标签类型选择有误"}, allow_blank=True)
    level = serializers.ChoiceField(required=True, choices=TAG_LEVEL_CHOICES, error_messages={"required": "标签级别必选"})
    enable = serializers.NullBooleanField(required=True, error_messages={"required": "是否启用必填"})

    def validate(self, data):
        name = data.get("name", "")
        weight = data.get("weight", 1)
        tagType = data.get("tagType", "")
        level = data.get("level", "")
        parent = self.parentUuid
        checkName = Tags.objects.filter(tagType=tagType, level=level).all().filter(name=name).first()
        if checkName:
            raise ParamError(TAG_NAME_EXISTS)
        checkSort = Tags.objects.filter(tagType=tagType, weight=weight, level=level, parentUuid=parent).first()
        if checkSort:
            raise ParamError(TAG_NUM_EXISTS)
        parent = data.get("parentUuid", None)
        if parent:
            parentTag = Tags.objects.filter(uuid=parent, level=(level - 1), tagType=tagType).first()
            if not parentTag:
                raise ParamError(TAG_PARENT_ERROR)
            # data["parentUuid"] = parentTag.uuid
        if level != 1 and not parent:
            raise ParamError(TAG_PARENT_ERROR)
        return data

    class Meta:
        model = Tags
        fields = ("name", "tagType", "parentUuid", "weight", "level", "enable")


class TagNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("name", "uuid")


class TagBasicSerializer(serializers.ModelSerializer):
    parentUuid = TagNameSerializer()

    class Meta:
        model = Tags
        fields = ("uuid", "name", "tagType", "parentUuid", "weight", "enable", "level")


class TagUpdateSerializer(serializers.Serializer):
    """更新标签序列化"""
    name = serializers.CharField(max_length=64, min_length=0, required=True,
                                 error_messages={"required": "标签名必填", "max_length": "标签名最多64个字"})
    parentUuid = serializers.CharField(max_length=32, required=False, allow_blank=True)
    weight = serializers.IntegerField(required=True, min_value=1,
                                      error_messages={"required": "显示顺必填", "min_value": "顺序最小值为1"})
    enable = serializers.NullBooleanField(required=True, error_messages={"required": "是否启用必填"})  # 使用NullBooleanField

    def update_tag(self, instance, validated_data):
        name = validated_data.get("name", "")
        weight = validated_data.get("weight", None)
        tagType = instance.tagType
        level = instance.level
        parent = validated_data.get("parentUuid", None)
        enable = validated_data.get("enable", 1)
        if parent:
            parentTag = Tags.objects.filter(uuid=parent, level=(level - 1), tagType=tagType).exclude(
                uuid=instance.uuid).first()
            if not parentTag:
                raise ParamError(TAG_PARENT_ERROR)
            instance.parentUuid = parentTag
        obj = Tags.objects.filter(name=name, level=level, tagType=tagType).exclude(uuid=instance.uuid).exists()
        if obj:
            raise ParamError(TAG_NAME_EXISTS)
        tags = Tags.objects.filter(tagType=tagType).filter(weight=weight, level=level,
                                                           parentUuid=instance.parentUuid).exclude(
            uuid=instance.uuid).exists()
        if tags:
            raise ParamError(TAG_NUM_EXISTS)
        instance.name = name
        instance.weight = weight
        # instance.tagType = tagType
        instance.enable = enable
        instance.save()
        return True

    class Meta:
        model = Tags
        fields = "__all__"


class SectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("uuid", "createTime", "updateTime", "name", "intro", "enable", "weight", "isShow")


class SectionSaveSerializer(serializers.ModelSerializer):
    """创建栏目序列化"""
    name = serializers.CharField(max_length=64, required=True,
                                 error_messages={"required": "栏目名必填", "max_length": "栏目名最多64个字"})
    intro = serializers.CharField(required=False, max_length=512, error_messages={"max_length": "栏目名最多512个字"},
                                  allow_blank=True)
    sectionType = serializers.IntegerField(required=False, min_value={"min_length": "栏目类型最小为1"})  # 栏目类型

    # enable = serializers.BooleanField(required=False)
    # weight = serializers.IntegerField(required=False, min_value=0, error_messages={"min_value": "权重值请大于0"})  # 权重值

    def validate(self, data):
        name = data["name"]
        sectionType = data.get("sectionType", 1)
        intro = data.get("intro", None)
        if Section.objects.filter(name=name, sectionType=sectionType).exists():
            raise ParamError(SECTION_EXISTS_ERROR)
        return data

    class Meta:
        model = Section
        fields = ("name", "intro", "sectionType")


class SectionUpdateSerializer(serializers.Serializer):
    """更新栏目序列化"""
    name = serializers.CharField(max_length=64, required=True,
                                 error_messages={"required": "栏目名必填", "max_length": "栏目名最多64个字"})
    intro = serializers.CharField(max_length=512, required=False,
                                  error_messages={"max_length": "栏目名最多512个字"}, allow_blank=True)
    sectionType = serializers.IntegerField(required=False, min_value={"min_length": "栏目类型最小为1"})  # 栏目类型

    def updateSection(self, instance, validated_data):
        name = validated_data.get("name", "")
        sectionType = validated_data.get("sectionType", 1)
        intro = validated_data.get("intro", "")
        if Section.objects.filter(name=name, sectionType=sectionType).exclude(uuid=instance.uuid).exists():
            raise ParamError(SECTION_EXISTS_ERROR)
        instance.name = name
        instance.intro = intro
        instance.save()
        return True

    class Meta:
        model = Section
        fields = ("name", "intro", "sectionType", "uuid")


# class ExpertUserSerializer(serializers.ModelSerializer):


class ExpertBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experts
        fields = (
            "uuid", "avatar", "name", "department", "jobTitle", "hospital", "tel", "isStar", "enable", "userUuid",
            "tags", "intro", "specialty")


class ExpertSaveSerializer(serializers.ModelSerializer):
    tel = serializers.CharField(required=True, max_length=32,
                                error_messages={"required": "电话号码必填", "max_length": "电话长度有误"})
    name = serializers.CharField(required=True, max_length=32,
                                 error_messages={"required": "专家名必填", "max_length": "专家名长度有误"})
    avatar = serializers.CharField(required=True, max_length=1024,
                                   error_messages={"required": "头像必填", "max_length": "头像长度有误"})
    hospital = serializers.CharField(required=True, max_length=512,
                                     error_messages={"required": "所在医院必填", "max_length": "医院长度有误"})
    department = serializers.CharField(required=True, max_length=128,
                                       error_messages={"required": "所在科室必填", "max_length": "科室名有误"})
    jobTitle = serializers.CharField(required=True, max_length=128,
                                     error_messages={"required": "专家职称必填", "max_length": "职称长度有误"})
    tags = serializers.SlugRelatedField(many=True,
                                        allow_null=False,
                                        slug_field="uuid",
                                        queryset=Tags.objects.filter(tagType=2),
                                        required=True,
                                        error_messages={
                                            'required': "标签不能为空"
                                        })
    specialty = serializers.CharField(required=False, max_length=1024, error_messages={"max_length": "专长度有误"},
                                      allow_blank=True,allow_null=True)
    isStar = serializers.NullBooleanField(required=True, error_messages={"required": "是否明星专家必填"})
    intro = serializers.CharField(required=False, max_length=1024,
                                  error_messages={"max_length": "专家介绍有误"}, allow_blank=True,allow_null=True)
    enable = serializers.NullBooleanField(required=True, error_messages={"required": "是否启用必填"})

    def validate(self, data):
        tel = data["tel"]
        name = data["name"]
        avatar = data["avatar"]
        tags = data["tags"]
        if not CheckPhone(tel):
            # 校验手机号
            raise ParamError(USER_TEL_ERROR)
        # 校验专家是否已存在
        if Experts.objects.filter(tel=data["tel"]).exists():
            raise ParamError(EXPERT_EXISTS_ERROR)
        user = User.objects.filter(tel=tel).first()
        if not user:
            userDict = {
                "tel": tel,
                "realName": name,
                "avatar": avatar
            }
            User.objects.create(**userDict)
        else:
            user.realName = name
            user.avatar = avatar
            user.save()
        return data

    def create(self, validated_data):
        expert = Experts.objects.filter(tel=validated_data["tel"]).first()
        if not expert:
            expert = Experts()
        expert.tel = validated_data["tel"]
        expert.name = validated_data["name"]
        expert.avatar = validated_data["avatar"]
        expert.hospital = validated_data["hospital"]
        expert.department = validated_data["department"]
        expert.jobTitle = validated_data["jobTitle"]
        expert.specialty = validated_data.get("specialty", None)
        expert.intro = validated_data.get("intro", None)
        expert.enable = validated_data["enable"]
        expert.isStar = validated_data["isStar"]
        user = User.objects.filter(tel=validated_data["tel"]).first()
        expert.userUuid = user
        expert.save()
        # 关联多对多
        expert.tags.set(validated_data["tags"])

    class Meta:
        model = Experts
        fields = (
            "uuid", "avatar", "name", "department", "jobTitle", "hospital", "tel", "isStar", "enable",
            "tags", "intro", "specialty")


class ExpertUpdateSerializer(serializers.Serializer):
    tel = serializers.CharField(required=True, max_length=32,
                                error_messages={"required": "电话号码必填", "max_length": "电话长度有误"})
    name = serializers.CharField(required=True, max_length=32,
                                 error_messages={"required": "专家名必填", "max_length": "专家名长度有误"})
    avatar = serializers.CharField(required=True, max_length=1024,
                                   error_messages={"required": "头像必填", "max_length": "头像长度有误"})
    hospital = serializers.CharField(required=True, max_length=512,
                                     error_messages={"required": "所在医院必填", "max_length": "医院长度有误"})
    department = serializers.CharField(required=True, max_length=128,
                                       error_messages={"required": "所在科室必填", "max_length": "科室名有误"})
    jobTitle = serializers.CharField(required=True, max_length=128,
                                     error_messages={"required": "专家职称必填", "max_length": "职称长度有误"})
    tags = serializers.SlugRelatedField(many=True,
                                        allow_null=False,
                                        slug_field="uuid",
                                        queryset=Tags.objects.filter(tagType=2),
                                        required=True,
                                        error_messages={
                                            'required': "标签不能为空"
                                        })
    specialty = serializers.CharField(required=False, max_length=1024, error_messages={"max_length": "专长度有误"},
                                      allow_blank=True,allow_null=True)
    isStar = serializers.NullBooleanField(required=True, error_messages={"required": "是否明星专家必填"})
    intro = serializers.CharField(required=False, max_length=1024,
                                  error_messages={"max_length": "专家介绍有误"}, allow_blank=True,allow_null=True)
    enable = serializers.NullBooleanField(required=True, error_messages={"required": "是否启用必填"})

    def validate(self, data):
        tel = data["tel"]
        if not CheckPhone(tel):
            # 校验手机号
            raise ParamError(USER_TEL_ERROR)
        return data

    def updateExpert(self, instance, validated_data):
        expert = Experts.objects.filter(tel=validated_data["tel"]).first()
        if not expert or expert.uuid != instance.uuid:
            raise ParamError(USER_TEL_ERROR)
        user = User.objects.filter(uuid=instance.userUuid.uuid).first()
        if not user:
            raise ParamError(USER_NOT_EXISTS)
        user.realName = validated_data["name"]
        user.avatar = validated_data["avatar"]
        user.save()
        instance.tel = validated_data["tel"]
        instance.name = validated_data["name"]
        instance.avatar = validated_data["avatar"]
        instance.hospital = validated_data["hospital"]
        instance.department = validated_data["department"]
        instance.jobTitle = validated_data["jobTitle"]
        instance.specialty = validated_data.get("specialty", None)
        instance.intro = validated_data.get("intro", None)
        instance.enable = validated_data["enable"]
        instance.isStar = validated_data["isStar"]
        instance.save()
        instance.tags.clear()
        instance.tags.set(validated_data["tags"])
        return True

    class Meta:
        model = Experts
        fields = (
            "uuid", "avatar", "name", "department", "jobTitle", "hospital", "tel", "isStar", "enable",
            "tags", "intro", "specialty")


class MustReadBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MustRead
        fields = ("uuid", "createTime", "updateTime", "name", "content", "mustReadNum", "mustReadType", "enable")


class MustReadSaveSerializer(serializers.ModelSerializer):
    """创建必读"""
    name = serializers.CharField(max_length=64, required=True,
                                 error_messages={"required": "须知名必填", "max_length": "须知名最多64个字"})
    content = serializers.CharField(required=True, error_messages={"required": "须知内容必填"})
    mustReadType = serializers.ChoiceField(choices=MUSTREAD_TYPE_CHOICES)

    def validate(self, data):
        mustReadType = data.get("mustReadType", None)
        if MustRead.objects.filter(mustReadType=mustReadType).exists():
            raise ParamError(MUSTREAD_EXISTS_ERROR)
        return data

    class Meta:
        model = MustRead
        fields = ("name", "content", "mustReadNum", "uuid", "mustReadType")


class MustReadUpdateSerializer(serializers.ModelSerializer):
    """更新必读"""
    name = serializers.CharField(max_length=64, required=True,
                                 error_messages={"required": "须知名必填", "max_length": "须知名最多64个字"})
    content = serializers.CharField(required=True, error_messages={"required": "须知内容必填"})
    uuid = serializers.CharField(required=False)

    def updateMustRead(self, instance, validated_data):
        name = validated_data.get("name", None)
        content = validated_data.get("content", None)
        if MustRead.objects.filter(mustReadType=instance.mustReadType).exclude(uuid=instance.uuid).exists():
            raise ParamError(MUSTREAD_EXISTS_ERROR)
        instance.name = name
        instance.content = content
        instance.save()
        return True

    class Meta:
        model = MustRead
        fields = ("name", "content", "mustReadNum", "uuid", "mustReadType")


class CoursePPTSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoursePPT
        fields = ("imgUrl", )


class CourseSourceBasicSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseSource
        fields = (
            "uuid", "createTime", "name", "sourceUrl", "sourceType", "fileSize", "duration",
            "enable")


class CourseSourceSaveSerializer(serializers.ModelSerializer):
    """存储课件库"""
    name = serializers.CharField(max_length=64, required=True,
                                 error_messages={"required": "课件名必填", "max_length": "课件名最多64个字"})
    sourceUrl = serializers.CharField(max_length=1024, required=True,
                                      error_messages={"required": "课件地址必填", "max_length": "课件地址长度有误"})
    fileSize = serializers.IntegerField(error_messages={"required": "文件大小必填"})
    duration = serializers.IntegerField(required=False)  # 课件时长
    sourceType = serializers.ChoiceField(choices=COURSESOURCE_TYPE_CHOICES, error_messages={"required": "课件类型必填"})

    def validate(self, data):
        name = data["name"]
        duration = data.get("duration", None)
        sourceType = data["sourceType"]
        if sourceType != 3:
            if not duration:
                raise ParamError(DURATION_VALUE_ERROR)
        if CourseSource.objects.filter(name=name).exists():
            raise ParamError(COURSESOURCE_EXISTS_ERROR)

        return data

    def create(self, validated_data):
        source_data = {}
        source_data["name"] = validated_data["name"]
        source_data["sourceUrl"] = validated_data["sourceUrl"]
        source_data["fileSize"] = validated_data["fileSize"]
        source_data["duration"] = validated_data.get("duration", None)
        source_data["sourceType"] = validated_data["sourceType"]
        courseSource = CourseSource.objects.create(**source_data)
        # 如果传的是ppt文件，则需要转成png
        if validated_data["sourceType"] == 3:
            cli = get_sts_token()
            taskid = change(cli, validated_data["sourceUrl"].split("/")[-1],
                            validated_data["sourceUrl"].split("/")[2].split(".")[0])
            t = threading.Thread(target=get_res, args=(cli, taskid, validated_data["sourceUrl"], courseSource.uuid))
            t.start()
        return CourseSourceBasicSerializer(courseSource)

    class Meta:
        model = CourseSource
        fields = (
            "uuid", "createTime", "name", "sourceUrl", "sourceType", "fileSize", "duration")


class SectionNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("uuid", "name", "intro")


class CourseNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ("uuid", "courseNum", "name", "courseThumbnail")


class SectionCourseNameSerializer(serializers.ModelSerializer):
    courseUuid = CourseNameSerializer()

    class Meta:
        model = Section
        fields = ("courseUuid",)


class SearchSectionCourseSerializer(serializers.ModelSerializer):
    """
    查询板块所对应课程
    """
    courses = serializers.SerializerMethodField()

    @staticmethod
    def get_courses(obj):
        queryset = Courses.objects.filter(uuid=obj.courseUuid_id).all()
        return CourseNameSerializer(queryset, many=True).data

    class Meta:
        model = SectionCourse
        fields = ("sectionUuid", "courses")


class SearchUserSerializer(serializers.ModelSerializer):
    """
    用户名模糊搜索
    """

    class Meta:
        model = User
        fields = ("uuid", "nickName", "tel")


class SearchGoodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goods
        fields = ("uuid", "name")


class SearchCoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ("uuid", "name")


class SectionWeightSerializer(serializers.ModelSerializer):
    objUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid",
                                           queryset=Section.objects.filter(enable=1, isShow=1),
                                           required=True,
                                           error_messages={
                                               'required': "对象栏目必填", "does_not_exist": "对象课程不存在"
                                           })
    uuid = serializers.CharField(required=False)

    def updateWeight(self, instance, validated_data):
        obj = validated_data["objUuid"]
        obj = Section.objects.filter(uuid=obj).first()
        instance.weight, obj.weight = obj.weight, instance.weight
        obj.save()
        instance.save()
        return True

    class Meta:
        model = Section
        fields = ("uuid", "objUuid")


class SectionCourseBasicSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()

    def get_courses(self, obj):
        queryset = Courses.objects.filter(courseSections=obj, courseSectionUuid__status=1).all()
        if queryset:
            return CourseNameSerializer(queryset, many=True).data
        return []

    class Meta:
        model = Section
        fields = (
            "uuid", "showType", "updateTime", "name", "showNum", "weight", "courses")


class BannerSerializer(serializers.ModelSerializer):

    # 显示顺序
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    class Meta:
        model = Banner
        exclude = ("updateTime", "orderNum")


class SectionCourseSaveSerializer(serializers.ModelSerializer):
    """
        保存展示栏目
    """
    showType = serializers.ChoiceField(choices=SECTION_SHOW_TYPE, required=True,
                                       error_messages={"required": "展示方式必填"})
    sectionUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid",
                                               queryset=Section.objects.filter(enable=1),
                                               required=True,
                                               error_messages={
                                                   'required': "栏目不能为空"
                                               })
    showNum = serializers.IntegerField(max_value=12, min_value=1, required=True,
                                       error_messages={"required": "展示数量必填", "max_value": "显示数量有误",
                                                       "min_value": "显示数量有误"})
    courses = serializers.SlugRelatedField(many=True,
                                           allow_null=False,
                                           slug_field="uuid",
                                           queryset=Courses.objects.exclude(status=4),
                                           error_messages={
                                               "does_not_exist": "课程不存在"
                                           })

    def validate(self, data):
        showType = data["showType"]
        showNum = data["showNum"]
        sectionUuid = data["sectionUuid"]
        courses = data["courses"]
        if showNum != len(courses):
            """判断展示数量和传的课程数量是否一致"""
            raise ParamError(SHOW_NUM_ERROR)
        if int(showType) == 2 and int(showNum) not in [2, 4, 6, 8, 10, 12]:
            raise ParamError(SHOW_NUM_ERROR)
        if sectionUuid.isShow:
            # 判断该栏目是否已存在
            raise ParamError(SECTION_EXISTS_ERROR)
        True_courses = sectionUuid.courses.all()
        for course in courses:
            if course not in True_courses:
                raise ParamError(SECTION_COURSE_ERROR)
        return data

    def create(self, validated_data):
        showType = validated_data["showType"]
        showNum = validated_data["showNum"]
        courses = validated_data["courses"]
        section = validated_data["sectionUuid"]
        section.showType = showType
        section.showNum = showNum
        section.isShow = True
        section.save()
        clength = len(courses) + 1
        for i in range(len(courses)):
            course = SectionCourse.objects.filter(courseUuid=courses[i], sectionUuid=section).first()
            course.status = 1
            course.weight = clength
            clength -= 1
            course.save()

    class Meta:
        model = Section
        fields = ("showType", "sectionUuid", "showNum", "courses")


class SectionCourseUpdateSerializer(serializers.Serializer):
    """
        修改展示栏目
    """
    showType = serializers.ChoiceField(choices=SECTION_SHOW_TYPE, required=True,
                                       error_messages={"required": "展示方式必填"})
    showNum = serializers.IntegerField(max_value=12, min_value=1, required=True,
                                       error_messages={"required": "展示数量必填", "max_value": "显示数量有误",
                                                       "min_value": "显示数量有误"})
    courses = serializers.SlugRelatedField(many=True,
                                           allow_null=False,
                                           slug_field="uuid",
                                           queryset=Courses.objects.exclude(status=4),
                                           required=True,
                                           error_messages={
                                               'required': "课程内容不能为空", "does_not_exist": "课程不存在"
                                           })

    def validate(self, data):
        showType = data["showType"]
        showNum = data["showNum"]
        courses = data["courses"]
        if showNum != len(courses):
            """判断展示数量和传的课程数量是否一致"""
            raise ParamError(SHOW_NUM_ERROR)
        if int(showType) == 2 and int(showNum) not in [2, 4, 6, 8, 10, 12]:
            raise ParamError(SHOW_NUM_ERROR)
        return data

    def updateSection(self, instance, validated_data):
        showType = validated_data["showType"]
        showNum = validated_data["showNum"]
        courses = validated_data["courses"]
        True_courses = instance.courses.all()
        for course in courses:
            if course not in True_courses:
                raise ParamError(SECTION_COURSE_ERROR)
        instance.showType = showType
        instance.showNum = showNum
        instance.isShow = True
        instance.save()
        clength = len(courses) + 1
        sectionsourses = SectionCourse.objects.filter(status=1, sectionUuid=instance).exclude(
            courseUuid__in=courses).all()  # 获取课程栏目中间表状态
        for sectionsourse in sectionsourses:
            """修改其他课程状态"""
            sectionsourse.status = 2
            sectionsourse.weight = 1
            sectionsourse.save()
        SectionCourses = SectionCourse.objects.filter(courseUuid__in=courses, sectionUuid=instance).order_by(
            "weight").all()
        for update_date in SectionCourses:
            update_date.status = 1
            update_date.weight = clength
            update_date.save()
            clength -= 1
        return True

    class Meta:
        model = SectionCourse
        fields = ("showType", "sectionUuid", "showNum", "courses")


# 创建banner
class BannerPostSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "轮播图标题必填"})
    status = serializers.ChoiceField(choices=BANNER_MODIFY_CHOICES, required=True,
                                     error_messages={"required": "状态必填"})
    icon = serializers.CharField(required=True, error_messages={"required": "轮播图图片必填"})
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })
    type = serializers.ChoiceField(required=True, choices=JUMP_TYPE_CHOICES,
                                   error_messages={
                                       "invalid_choice": "轮播类型选择有误",
                                       "required": "轮播类型必填"
                                   })

    target = serializers.CharField(required=True, error_messages={"required": "跳转对象必填"})

    def validate(self, attrs):
        if Banner.objects.filter(name=attrs['name']).exclude(status=3).exists():
            raise ParamError(BANNER_NAME_EXISTS)
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        # 优惠卷结束时间早于当前时间
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)
        # 如果是课程
        if attrs["type"] == 1:
            if not Courses.objects.filter(uuid=attrs["target"], status=1).exists():
                raise ParamError("跳转的课程不存在")
        # 如果是外部链接
        if attrs["type"] == 2:
            if not any([attrs["target"].startswith('http://'), attrs["target"].startswith('https://')]):
                raise ParamError("跳转外链地址格式错误，需http://或者https://开头。")
        return attrs

    def create(self, validated_data):
        try:
            validated_data["startTime"] = timeChange(validated_data['startTime'], 2)
            validated_data["endTime"] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)
        validated_data["orderNum"] = Banner.objects.exclude(status=3).aggregate(Max('orderNum'))['orderNum__max'] or 0
        validated_data["orderNum"] += 1
        banner = Banner.objects.create(**validated_data)
        return True

    class Meta:
        model = Banner
        exclude = ("updateTime",)


class BannerUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, error_messages={"required": "轮播图标题必填"})
    icon = serializers.CharField(required=True, error_messages={"required": "轮播图图片必填"})
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })
    type = serializers.ChoiceField(required=True, choices=JUMP_TYPE_CHOICES,
                                   error_messages={
                                       "invalid_choice": "轮播类型选择有误",
                                       "required": "轮播类型必填"
                                   })
    status = serializers.ChoiceField(choices=BANNER_MODIFY_CHOICES, required=True)
    target = serializers.CharField(required=True, error_messages={"required": "跳转对象必填"})

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        # 优惠卷结束时间早于当前时间
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)
        # 如果是课程
        if attrs["type"] == 1:
            if not Courses.objects.filter(uuid=attrs["target"], status=1).exists():
                raise ParamError("跳转的课程不存在")
        # 如果是外部链接
        if attrs["type"] == 2:
            if not any([attrs["target"].startswith('http://'), attrs["target"].startswith('https://')]):
                raise ParamError("跳转外链地址格式错误，需http://或者https://开头。")
        return attrs

    def update_banner(self, instance, validated_data):
        try:
            validated_data['startTime'] = timeChange(validated_data['startTime'], 2)
            validated_data['endTime'] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)

        if Banner.objects.filter(name=validated_data['name']).exclude(Q(status=3) | Q(uuid=instance.uuid)).exists():
            raise ParamError(BANNER_NAME_EXISTS)

        instance.name = validated_data["name"]
        instance.startTime = validated_data["startTime"]
        instance.endTime = validated_data["endTime"]
        instance.icon = validated_data["icon"]
        instance.type = validated_data["type"]
        instance.target = validated_data["target"]
        instance.status = validated_data["status"]
        instance.save()
        return True


class BannerChangeSerializer(serializers.Serializer):
    swapBannerUuid = serializers.PrimaryKeyRelatedField(allow_null=False,
                                                        queryset=Banner.objects.filter(BANNER_Q),
                                                        required=True,
                                                        error_messages={
                                                            'required': "交换的轮播图必填", "does_not_exist": "交换的轮播图不存在"
                                                        })

    def updateOrderNum(self, instance, validated_data):
        obj = validated_data["swapBannerUuid"]
        obj = Banner.objects.filter(uuid=obj).first()
        instance.orderNum, obj.orderNum = obj.orderNum, instance.orderNum
        obj.save()
        instance.save()
        return True


class HotSearchSerializer(serializers.ModelSerializer):

    # 显示顺序
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    class Meta:
        model = HotSearch
        exclude = ("updateTime",)


# 创建热搜词
class HotSearchPostSerializer(serializers.Serializer):
    keyword = serializers.CharField(required=True, error_messages={"required": "关键词必填"})
    status = serializers.ChoiceField(choices=HOT_SEARCH_MODIFY_CHOICES, required=True,
                                     error_messages={"required": "状态必填"})

    def validate(self, attrs):
        if HotSearch.objects.filter(keyword=attrs['keyword']).exclude(status=3).exists():
            raise ParamError(HOT_SEARCH_KEYWORD_ERROR)
        return attrs

    def create(self, validated_data):
        validated_data["weight"] = HotSearch.objects.exclude(status=3).aggregate(Max('weight'))['weight__max'] or 0
        validated_data["weight"] += 1
        validated_data["searchType"] = 1
        hotSearch = HotSearch.objects.create(**validated_data)
        return True


class HotSearchChangeSerializer(serializers.Serializer):
    swapHotSearchUuid = serializers.PrimaryKeyRelatedField(allow_null=False,
                                                           queryset=HotSearch.objects.filter(HOT_SEARCH_Q),
                                                           required=True,
                                                           error_messages={
                                                               'required': "交换的关键词必填", "does_not_exist": "交换的关键词不存在"
                                                           })

    def updateWeight(self, instance, validated_data):
        obj = validated_data["swapHotSearchUuid"]
        obj = HotSearch.objects.filter(uuid=obj).first()
        instance.weight, obj.weight = obj.weight, instance.weight
        obj.save()
        instance.save()
        return True


class CourseLiveSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    # 显示顺序
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    def get_name(self, obj):
        return obj.courseUuid.name

    class Meta:
        model = CourseLive
        exclude = ("updateTime",)


# 创建大咖直播
class CourseLivePostSerializer(serializers.Serializer):
    icon = serializers.CharField(required=True, error_messages={"required": "条幅图片必填"})
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })

    course = serializers.PrimaryKeyRelatedField(required=True,
                                                queryset=Courses.objects.filter(COURSE_LIVE_SEARCH_Q),
                                                error_messages={"required": "跳转课程必填"})

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)
        return attrs

    def create(self, validated_data):
        try:
            validated_data["startTime"] = timeChange(validated_data['startTime'], 2)
            validated_data["endTime"] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)
        validated_data["weight"] = CourseLive.objects.exclude(status=3).aggregate(Max('weight'))['weight__max'] or 0
        validated_data["weight"] += 1
        validated_data["courseUuid_id"] = validated_data.pop("course")
        courseLive = CourseLive.objects.create(**validated_data)
        return True


class CourseLiveUpdateSerializer(serializers.Serializer):
    icon = serializers.CharField(required=True, error_messages={"required": "条幅图片必填"})
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })

    course = serializers.PrimaryKeyRelatedField(required=True,
                                                queryset=Courses.objects.filter(COURSE_LIVE_SEARCH_Q),
                                                error_messages={"required": "跳转课程必填"})

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)

        return attrs

    def update_courseLive(self, instance, validated_data):
        try:
            validated_data['startTime'] = timeChange(validated_data['startTime'], 2)
            validated_data['endTime'] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)

        instance.startTime = validated_data["startTime"]
        instance.endTime = validated_data["endTime"]
        instance.icon = validated_data["icon"]
        instance.courseUuid_id = validated_data["course"]
        instance.save()
        return True


class CourseLiveChangeSerializer(serializers.Serializer):
    swapCourseLiveUuid = serializers.PrimaryKeyRelatedField(allow_null=False,
                                                            queryset=CourseLive.objects.filter(COURSE_LIVE_Q),
                                                            required=True,
                                                            error_messages={
                                                                'required': "交换的直播课必填", "does_not_exist": "交换的直播课不存在"
                                                            })

    def updateWeight(self, instance, validated_data):
        obj = validated_data["swapCourseLiveUuid"]
        obj = CourseLive.objects.filter(uuid=obj).first()
        instance.weight, obj.weight = obj.weight, instance.weight
        obj.save()
        instance.save()
        return True


# 猜你喜欢
class MayLikeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    courseBanner = serializers.SerializerMethodField()

    # 显示顺序
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    def get_name(self, obj):
        return obj.courseUuid.name

    def get_courseBanner(self, obj):
        return obj.courseUuid.courseBanner

    class Meta:
        model = MayLike
        exclude = ("updateTime", "userUuid", "likeType")


# 创建猜你喜欢
class MayLikePostSerializer(serializers.Serializer):
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })

    course = serializers.PrimaryKeyRelatedField(required=True,
                                                queryset=Courses.objects.filter(COURSE_Q),
                                                error_messages={"required": "课程必填"})

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)
        return attrs

    def create(self, validated_data):
        try:
            validated_data["startTime"] = timeChange(validated_data['startTime'], 2)
            validated_data["endTime"] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)
        validated_data["weight"] = MayLike.objects.exclude(status=3).aggregate(Max('weight'))['weight__max'] or 0
        validated_data["weight"] += 1
        validated_data["likeType"] = 3
        validated_data["courseUuid_id"] = validated_data.pop("course")
        courseLive = MayLike.objects.create(**validated_data)
        return True


class MayLikeUpdateSerializer(serializers.Serializer):
    startTime = serializers.DateTimeField(required=True,
                                          error_messages={
                                              'required': "开始时间必填"
                                          })
    endTime = serializers.DateTimeField(required=True,
                                        error_messages={
                                            'required': "结束时间必填"
                                        })
    course = serializers.PrimaryKeyRelatedField(required=True,
                                                queryset=Courses.objects.filter(COURSE_Q),
                                                error_messages={"required": "课程必填"})

    def validate(self, attrs):
        if attrs['startTime'] > attrs['endTime']:
            raise ParamError(TIME_RANGE_ERROR)
        now = datetime.now()
        if attrs["endTime"] < now:
            raise ParamError(ENDTIME_RANGE_ERROR)

        return attrs

    def update_mayLike(self, instance, validated_data):
        try:
            validated_data['startTime'] = timeChange(validated_data['startTime'], 2)
            validated_data['endTime'] = timeChange(validated_data['endTime'], 2)
        except Exception as e:
            raise ParamError(DATETIME_TO_TIMESTAMP_ERROR)

        instance.startTime = validated_data["startTime"]
        instance.endTime = validated_data["endTime"]
        instance.courseUuid_id = validated_data["course"]
        instance.save()
        return True


#  改变顺序
class MayLikeChangeSerializer(serializers.Serializer):
    swapMayLikeUuid = serializers.PrimaryKeyRelatedField(allow_null=False,
                                                         queryset=MayLike.objects.filter(MAY_LIKE_Q),
                                                         required=True,
                                                         error_messages={
                                                             'required': "交换的课程必填", "does_not_exist": "交换的课程不存在"
                                                         })

    def updateWeight(self, instance, validated_data):
        obj = validated_data["swapMayLikeUuid"]
        obj = MayLike.objects.filter(uuid=obj).first()
        instance.weight, obj.weight = obj.weight, instance.weight
        obj.save()
        instance.save()
        return True


class LiveCourseBannerPostSerializer(serializers.Serializer):
    """直播素材创建"""
    name = serializers.CharField(max_length=512, required=False, allow_null=True)
    sourceUrl = serializers.CharField(max_length=1024, required=True,
                                      error_messages={"required": "直播素材地址必填", "max_length": "直播素材地址长度有误"})
    fileSize = serializers.IntegerField(required=True, error_messages={"required": "直播素文件大小必填"})
    duration = serializers.IntegerField(required=False, allow_null=True)  # 课件时长
    sourceType = serializers.ChoiceField(choices=LIVE_COURSE_BANNER_TYPE_CHOICES,
                                         error_messages={"required": "直播素材类型必填"})

    def validate(self, data):
        sourceUrl = data["sourceUrl"]
        # if LiveCourseBanner.objects.filter(sourceUrl=sourceUrl).exists():
        #     raise ParamError(LIVE_COURSE_BANNER_EXISTS)
        sourceType = data["sourceType"]
        # 1,2 音频 视频
        if sourceType in [1, 2]:
            if not data.get("duration"):
                raise ParamError(DURATION_VALUE_ERROR)
        # ppt
        if sourceType == 3:
            if not sourceUrl.endswith("ppt") and not sourceUrl.endswith("pptx"):
                raise ParamError(PPT_VALUE_ERROR)
        return data


class LiveCourseMsgPostSerializer(serializers.Serializer):
    """直播单条内容创建"""
    name = serializers.CharField(max_length=512, required=True)
    sourceUrl = serializers.CharField(max_length=1024, required=True,
                                      error_messages={"required": "直播课件地址必填", "max_length": "直播课件地址长度有误"})
    fileSize = serializers.IntegerField(error_messages={"required": "直播课件大小必填"})
    duration = serializers.IntegerField(required=False, allow_null=True)  # 课件时长
    sourceType = serializers.ChoiceField(choices=LIVE_SOURCE_MSG_TYPE_CHOICES,
                                         error_messages={"required": "直播课件类型必填"})


class LiveCoursePostSerializer(serializers.Serializer):
    """直播课件创建"""
    name = serializers.CharField(max_length=64, min_length=0, required=True,
                                 error_messages={"required": "课件名必填", "max_length": "课件名最多64个字"})
    banner = serializers.DictField(required=False, allow_null=True)
    courseList = serializers.ListField(required=True, error_messages={"required": "直播课件必填"})

    def validate(self, data):
        if LiveCourse.objects.filter(name=data['name']).exists():
            raise ParamError(LIVE_COURSE_NAME_EXISTS)
        if data.get("banner"):
            a = LiveCourseBannerPostSerializer(data=data['banner'])
            a.is_valid(raise_exception=True)

        for item in data["courseList"]:
            c = LiveCourseMsgPostSerializer(data=item)
            c.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):
        # 创建素材
        liveCourseBanner = None
        if validated_data.get("banner"):
            liveCourseBanner = LiveCourseBanner.objects.create(
                name=validated_data["banner"]["name"],
                sourceUrl=validated_data["banner"]["sourceUrl"],
                sourceType=validated_data["banner"]["sourceType"],
                fileSize=validated_data["banner"]["fileSize"],
                duration=validated_data["banner"]["duration"]
            )
            if validated_data["banner"]["sourceType"] == 3:
                cli = get_sts_token()
                taskid = change(cli, validated_data["banner"]["sourceUrl"].split("/")[-1],
                                validated_data["banner"]["sourceUrl"].split("/")[2].split(".")[0])
                t = threading.Thread(target=get_res,
                                     args=(cli, taskid, validated_data["banner"]["sourceUrl"], liveCourseBanner.uuid))
                t.start()
        # 创建课件
        liveCourse = LiveCourse(
            name=validated_data["name"],
            enable=True,
            liveCourseBannerUuid=liveCourseBanner
        )
        liveCourse.save()
        # 批量创建消息体
        liveCourseMsgList = []
        for i, item in enumerate(validated_data["courseList"]):
            liveCourseMsgList.append(
                LiveCourseMsg(
                    sortNum=i + 1,
                    liveCourseUuid=liveCourse,
                    fileSize=item["fileSize"],
                    sourceUrl=item["sourceUrl"],
                    sourceType=item["sourceType"],
                    duration=item["duration"],
                    name=item["name"]
                )
            )
        LiveCourseMsg.objects.bulk_create(liveCourseMsgList)
        return True


class LiveCourseBannerSerializer(serializers.ModelSerializer):
    pptType = serializers.SerializerMethodField()
    pptUrlList = serializers.SerializerMethodField()
    pages = serializers.SerializerMethodField()

    def get_pptType(self, obj):
        if obj.sourceType == 3:
            if obj.sourceUrl:
                return 1            # 上传url返回url
            else:
                return 2            # 返回url列表

    def get_pptUrlList(self, obj):
        if obj.sourceType == 3 and not obj.sourceUrl:
            ppt = CoursePPT.objects.filter(o_topic_id=obj.o_topic_id, enable=True).order_by("sortNum")
            return CoursePPTSerializer(ppt, many=True).data

    def get_pages(self, obj):
        if obj.sourceType == 3 and not obj.sourceUrl:
            return CoursePPT.objects.filter(o_topic_id=obj.o_topic_id, enable=True).count()
        if obj.sourceType == 3 and obj.sourceUrl:
            return obj.courseSourcePpt.filter(enable=1).count()

    class Meta:
        model = LiveCourseBanner
        exclude = ("o_topic_id", "o_media_id", "updateTime", "createTime")


class LiveCourseBannerSimpleSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    def get_pages(self, obj):
        if obj.sourceType == 3 and not obj.sourceUrl:
            return CoursePPT.objects.filter(o_topic_id=obj.o_topic_id, enable=True).count()
        if obj.sourceType == 3 and obj.sourceUrl:
            return obj.courseSourcePpt.filter(enable=1).count()

    class Meta:
        model = LiveCourseBanner
        fields = ("pages", "sourceType", "sourceUrl", "duration")


class LiveCourseSerializer(serializers.ModelSerializer):
    bannerInfo = serializers.SerializerMethodField()
    courseDuration = serializers.SerializerMethodField()

    @staticmethod
    def get_bannerInfo(obj):
        if obj.liveCourseBannerUuid:
            return LiveCourseBannerSerializer(obj.liveCourseBannerUuid).data

    @staticmethod
    def get_courseDuration(obj):
        queryset = obj.liveCourseMsgUuid.aggregate(nums=Sum("duration"))
        # queryset = LiveCourseMsg.objects.filter(courseUuid=obj).aggregate(nums=Sum("duration"))
        return queryset["nums"]

    class Meta:
        model = LiveCourse
        fields = ("bannerInfo", "createTime", "name", "enable", "courseDuration", "uuid")


class LiveCourseMsgSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiveCourseMsg
        exclude = ("liveCourseUuid", "updateTime")


class LiveCourseUpdateSerializer(serializers.Serializer):
    """更新课程素材"""
    banner = serializers.DictField(required=True, error_messages={'required': "更换的素材库必填"})

    def validate(self, data):
        a = LiveCourseBannerPostSerializer(data=data['banner'])
        a.is_valid(raise_exception=True)

    def updateLiveCourse(self, instance, validated_data):
        liveCourseBanner = LiveCourseBanner.objects.create(
            name=validated_data["banner"]["name"],
            sourceUrl=validated_data["banner"]["sourceUrl"],
            sourceType=validated_data["banner"]["sourceType"],
            fileSize=validated_data["banner"]["fileSize"],
            duration=validated_data["banner"]["duration"]
        )
        if validated_data["banner"]["sourceType"] == 3:
            cli = get_sts_token()
            taskid = change(cli, validated_data["banner"]["sourceUrl"].split("/")[-1],
                            validated_data["banner"]["sourceUrl"].split("/")[2].split(".")[0])
            t = threading.Thread(target=get_res,
                                 args=(cli, taskid, validated_data["banner"]["sourceUrl"], liveCourseBanner.uuid))
            t.start()
        instance.liveCourseBannerUuid = liveCourseBanner
        instance.save()
        return True


class LiveCourseMsgSortNumSerializer(serializers.ModelSerializer):
    objUuid = serializers.SlugRelatedField(allow_null=False, slug_field="uuid",
                                           queryset=LiveCourseMsg.objects.filter(),
                                           required=True,
                                           error_messages={
                                               'required': "交换对象必填", "does_not_exist": "交换对象不存在"
                                           })

    def updateSortNum(self, instance, validated_data):
        obj = validated_data["objUuid"]
        if instance.liveCourseUuid != obj.liveCourseUuid:
            raise ParamError("交换的信息不在同一个课件库里")
        # obj = LiveCourseMsg.objects.filter(uuid=obj).first()
        instance.sortNum, obj.sortNum = obj.sortNum, instance.sortNum
        obj.save()
        instance.save()
        return True

    class Meta:
        model = Section
        fields = ("uuid", "objUuid")