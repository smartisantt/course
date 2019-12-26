#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view
from rest_framework.filters import OrderingFilter
from rest_framework import mixins, viewsets, status
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from client.models import Banner, MayLike
from common.models import Courses, Tags, UUIDTools, Section, Experts, MustRead, CourseSource, SectionCourse, User, \
    Goods, HotSearch, CourseLive, LiveCourseBanner, LiveCourse, LiveCourseMsg, Chapters, ChatsRoom
from manager.filters import TagFilter, SectionFilter, ExpertFilter, MustReadFilter, CourseSourceFilter, \
    SectionCourseFilter, SearchSectionCourseFilter, SearchUserFilter, BannerFilter, SearchGoodsFilter, \
    SearchCoursesFilter, HotSearchFilter, LiveCourseFilter, LiveCourseMsgFilter
from manager.serializers import TagSaveSerializer, TagBasicSerializer, TagUpdateSerializer, \
    SectionBasicSerializer, SectionSaveSerializer, SectionUpdateSerializer, ExpertBasicSerializer, ExpertSaveSerializer, \
    ExpertUpdateSerializer, MustReadBasicSerializer, MustReadSaveSerializer, MustReadUpdateSerializer, \
    CourseSourceBasicSerializer, CourseSourceSaveSerializer, SectionCourseBasicSerializer, \
    SearchSectionCourseSerializer, SectionCourseSaveSerializer, SectionCourseUpdateSerializer, SectionWeightSerializer, \
    SearchUserSerializer, BannerSerializer, BannerPostSerializer, SearchGoodsSerializer, SearchCoursesSerializer, \
    BannerChangeSerializer, BannerUpdateSerializer, HotSearchSerializer, HotSearchPostSerializer, \
    HotSearchChangeSerializer, CourseLiveSerializer, CourseLivePostSerializer, CourseLiveUpdateSerializer, \
    CourseLiveChangeSerializer, MayLikeSerializer, MayLikePostSerializer, MayLikeUpdateSerializer, \
    MayLikeChangeSerializer, LiveCoursePostSerializer, LiveCourseSerializer, LiveCourseUpdateSerializer, \
    LiveCourseMsgSerializer, LiveCourseBannerSerializer, LiveCourseMsgSortNumSerializer, LiveCourseBannerPostSerializer, \
    HotSearchUpdateSerializer
from utils.errors import ParamError
from utils.msg import *
from utils.ppt2png import get_sts_token, change, get_res2
from utils.qFilter import NORMAL_USER_Q, BANNER_Q, HOT_SEARCH_Q, COURSE_LIVE_Q, GOODS_DISTRIBUTION_Q, \
    COURSE_LIVE_SEARCH_Q, MAY_LIKE_Q


class TagView(mixins.ListModelMixin,
              mixins.CreateModelMixin,
              mixins.DestroyModelMixin,
              mixins.RetrieveModelMixin,
              mixins.UpdateModelMixin,
              viewsets.GenericViewSet):
    queryset = Tags.objects.filter().order_by('tagType', 'level', 'weight').all()
    serializer_class = TagBasicSerializer
    filter_class = TagFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('createTime',)

    # 新增标签
    def create(self, request, *args, **kwargs):
        serializer_data = TagSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        tag = {}
        parentUuid = Tags.objects.filter(uuid=serializer_data.data.get("parentUuid", None)).first()
        if parentUuid:
            tag["parentUuid"] = parentUuid
        tag["name"] = serializer_data.data.get("name", "")
        tag["weight"] = serializer_data.data.get("weight", None)
        tag["tagType"] = serializer_data.data.get("tagType", "")
        tag["level"] = serializer_data.data.get("level", "")
        tag["enable"] = serializer_data.data.get("enable", "")
        Tags.objects.create(**tag)

        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    # 查询标签
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(TAG_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    #  修改标签
    def update(self, request, *args, **kwargs):
        # try:
        instance = self.get_object()
        # except Exception as e:
        #     raise ParamError(TAG_NOT_EXISTS)
        serializer = TagUpdateSerializer(data=request.data)
        result = serializer.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer.errors)
        checkMsg = serializer.update_tag(instance, serializer.data)
        if checkMsg:
            return Response(PUT_SUCCESS)


"""课程栏目"""


class SectionView(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = Section.objects.filter().order_by('createTime').all()
    serializer_class = SectionBasicSerializer
    filter_class = SectionFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('createTime',)

    def create(self, request, *args, **kwargs):
        serializer_data = SectionSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        section = {}
        section["name"] = serializer_data.data.get("name", "")
        section["intro"] = serializer_data.data.get("intro", None)
        section["sectionType"] = serializer_data.data.get("sectionType", 1)
        # section["weight"] = serializer_data.data.get("weight", 0)
        Section.objects.create(**section)
        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(SECTION_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = SectionUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateSection(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(SECTION_NOT_EXISTS)
        if instance.courses.exists():
            raise ParamError(SECTION_COURSE_EXISTS_ERROR )
        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


"""专家相关"""


class ExpertView(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = Experts.objects.filter().order_by('-createTime').all()
    serializer_class = ExpertBasicSerializer
    filter_class = ExpertFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    def create(self, request, *args, **kwargs):
        serializer_data = ExpertSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.validated_data)
        return Response(serializer_data.initial_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(EXPERT_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = ExpertUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateExpert(instance, serializer_data.validated_data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(EXPERT_NOT_EXISTS)
        if instance.enable:
            courseSource = CourseSource.objects.filter(expertUuid=instance).first()
            if courseSource:
                raise ParamError({"code": 400, "msg": "专家正在课件库【{}】使用".format(courseSource.name)})

            chapter = Chapters.objects.filter(expertUuid=instance).first()
            if chapter:
                raise ParamError({"code": 400, "msg": "专家正在课程中使用"})

            chatsroom = ChatsRoom.objects.filter(expertUuid=instance).first()
            if chatsroom:
                raise ParamError({"code": 400, "msg": "专家正在直播【{}】使用".format(chatsroom.name)})

        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


#  课程须知模块
class MustReadView(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    queryset = MustRead.objects.filter().order_by('-createTime').all()
    serializer_class = MustReadBasicSerializer
    filter_class = MustReadFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    def create(self, request, *args, **kwargs):
        serializer_data = MustReadSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        mustread = {}
        mustread["name"] = serializer_data.data.get("name", "")
        mustread["content"] = serializer_data.data.get("content", "")
        mustread["mustReadType"] = serializer_data.data.get("mustReadType", None)
        # section["weight"] = serializer_data.data.get("weight", 0)
        MustRead.objects.create(**mustread)
        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MUSTREAD_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = MustReadUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateMustRead(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MUSTREAD_NOT_EXISTS)
        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


#  课件库模块
class CourseSourceView(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    queryset = CourseSource.objects.filter().order_by('-createTime').all()
    serializer_class = CourseSourceBasicSerializer
    filter_class = CourseSourceFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


    def create(self, request, *args, **kwargs):
        serializer_data = CourseSourceSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        courseSource = serializer_data.create(serializer_data.data)
        return Response(courseSource.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSESOURCE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSESOURCE_NOT_EXISTS)

        ##################校验课件库 停用后######################
        if instance.enable:
            course = instance.courseSourceChapter.filter().first()
            if course:
                raise ParamError({"code": 400, "msg": "该课件被【{}】使用".format(course.courseUuid.name)})
        ########################################################
        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


class searchSectionCourseView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
        根据板块查询有效课程
    """
    queryset = SectionCourse.objects.exclude(status=3).filter(courseUuid__status=1).order_by('-weight').all()
    serializer_class = SearchSectionCourseSerializer
    filter_class = SearchSectionCourseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight",)


class searchUserView(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.UpdateModelMixin):
    queryset = User.objects.filter(NORMAL_USER_Q)
    serializer_class = SearchUserSerializer
    filter_class = SearchUserFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


class searchGoodsView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Goods.objects.filter(GOODS_DISTRIBUTION_Q)
    serializer_class = SearchGoodsSerializer
    filter_class = SearchGoodsFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


class searchCoursesView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Courses.objects.filter(status=1)
    serializer_class = SearchCoursesSerializer
    filter_class = SearchCoursesFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


class searchCoursesLiveView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Courses.objects.filter(COURSE_LIVE_SEARCH_Q)
    serializer_class = SearchCoursesSerializer
    filter_class = SearchCoursesFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


class SectionChangeView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Section.objects.filter(enable=1, isShow=1).all()
    serializer_class = SectionWeightSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = SectionWeightSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateWeight(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)


#  配置栏目
class SectionCourseView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    queryset = Section.objects.filter(enable=1, isShow=True, sectionCourseUuid__status=1).all().distinct()
    serializer_class = SectionCourseBasicSerializer
    filter_class = SectionCourseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight",)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(SECTION_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer_data = SectionCourseSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.validated_data)
        return Response(serializer_data.initial_data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = SectionCourseUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateSection(instance, serializer_data.validated_data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(SECTION_NOT_EXISTS)
        SectionCourses = SectionCourse.objects.filter(sectionUuid=instance, status=1).all()
        for sectioncourse in SectionCourses:
            sectioncourse.weight = 1
            sectioncourse.status = 2
            sectioncourse.save()
        if instance.isShow:
            instance.weight = 1
            instance.isShow = 0
            instance.save()
        return Response(REMOVE_SUCCESS)


#  轮播图
class BannerView(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = Banner.objects.filter(BANNER_Q)
    serializer_class = BannerSerializer
    # filter_class = BannerFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("orderNum",)

    @action(methods=['put'], detail=True)
    def enable(self, request, pk):
        banner = self.get_object()
        banner.status = 2 if banner.status == 1 else 1
        banner.save()
        return Response(CHANGE_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(BANNER_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_data = BannerPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.data)
        return Response(POST_SUCCESS)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(BANNER_NOT_EXISTS)
        serializers_data = BannerUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_banner(instance, serializers_data.data)
        return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(BANNER_NOT_EXISTS)
        instance.status = 3
        instance.save()
        return Response(DEL_SUCCESS)


class BannerChangeView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Banner.objects.filter(BANNER_Q)
    serializer_class = BannerChangeSerializer

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(BANNER_NOT_EXISTS)
        serializer_data = BannerChangeSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateOrderNum(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)


#  热搜词
class HotSearchView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = HotSearch.objects.filter(HOT_SEARCH_Q)
    serializer_class = HotSearchSerializer
    filter_class = HotSearchFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight", "-searchNum")

    @action(methods=['put'], detail=True)
    def enable(self, request, pk):
        hotSearch = self.get_object()
        hotSearch.status = 2 if hotSearch.status == 1 else 1
        hotSearch.save()
        return Response(CHANGE_SUCCESS)

    @action(methods=['put'], detail=True)
    def defaultHotSearch(self, request, pk):
        hotSearch = self.get_object()
        HotSearch.objects.filter(isDefault=True).update(isDefault=False)
        hotSearch.isDefault = True
        hotSearch.save()
        return Response(CHANGE_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(HOT_SEARCH_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_data = HotSearchPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.data)
        return Response(POST_SUCCESS)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(HOT_SEARCH_NOT_EXISTS)
        serializer_data = HotSearchUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.update_hotSearch(instance, serializer_data.validated_data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(HOT_SEARCH_NOT_EXISTS)
        instance.status = 3
        instance.save()
        return Response(DEL_SUCCESS)

#   交换关键词
class HotSearchChangeView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = HotSearch.objects.filter(HOT_SEARCH_Q)
    serializer_class = HotSearchChangeSerializer

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(HOT_SEARCH_NOT_EXISTS)
        serializer_data = HotSearchChangeSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateWeight(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)


#  大咖直播
class CourseLiveView(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = CourseLive.objects.filter(COURSE_LIVE_Q)
    serializer_class = CourseLiveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight", )

    @action(methods=['put'], detail=True)
    def enable(self, request, pk):
        hotSearch = self.get_object()
        hotSearch.status = 2 if hotSearch.status == 1 else 1
        hotSearch.save()
        return Response(CHANGE_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSE_LIVE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_data = CourseLivePostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.data)
        return Response(POST_SUCCESS)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSE_LIVE_NOT_EXISTS)
        serializers_data = CourseLiveUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_courseLive(instance, serializers_data.data)
        return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSE_LIVE_NOT_EXISTS)
        instance.status = 3
        instance.save()
        return Response(DEL_SUCCESS)


class CourseLiveChangeView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = CourseLive.objects.filter(COURSE_LIVE_Q)
    serializer_class = CourseLiveChangeSerializer

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(HOT_SEARCH_NOT_EXISTS)
        serializer_data = CourseLiveChangeSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateWeight(instance, serializer_data.data)
        if checkMsg:
            return Response(CHANGE_SUCCESS)


# 猜你喜欢
class MayLikeView(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = MayLike.objects.filter(MAY_LIKE_Q)
    serializer_class = MayLikeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight", )

    @action(methods=['put'], detail=True)
    def enable(self, request, pk):
        hotSearch = self.get_object()
        hotSearch.status = 2 if hotSearch.status == 1 else 1
        hotSearch.save()
        return Response(CHANGE_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MAY_LIKE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_data = MayLikePostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.create(serializer_data.data)
        return Response(POST_SUCCESS)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MAY_LIKE_NOT_EXISTS)
        serializers_data = MayLikeUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_mayLike(instance, serializers_data.data)
        return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MAY_LIKE_NOT_EXISTS)
        instance.status = 3
        instance.save()
        return Response(DEL_SUCCESS)


# 修改猜你喜欢顺序
class MayLikeOrderChangeView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = MayLike.objects.filter(MAY_LIKE_Q)
    serializer_class = MayLikeChangeSerializer

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MAY_LIKE_NOT_EXISTS)
        serializer_data = MayLikeChangeSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateWeight(instance, serializer_data.data)
        if checkMsg:
            return Response(CHANGE_SUCCESS)


class LiveCourseView(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = LiveCourse.objects.order_by('-createTime').all()
    serializer_class = LiveCourseSerializer
    filter_class = LiveCourseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    @action(methods=['get'], detail=True)
    def pptInfo(self, request, pk):
        return Response(LiveCourseBannerSerializer(self.get_object().liveCourseBannerUuid).data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer_data = LiveCoursePostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        liveCourse = serializer_data.create(serializer_data.validated_data)
        return Response(POST_SUCCESS)

    #  修改素材，
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_NOT_EXISTS)
        serializer = LiveCourseUpdateSerializer(data=request.data)
        result = serializer.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer.errors)
        checkMsg = serializer.updateLiveCourse(instance, serializer.validated_data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 禁用启用
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_NOT_EXISTS)
        ############################################
        if instance.enable:
            if instance.liveCourseChatsRoom.exists():
                raise ParamError({"code": 400, "msg": "该课件被直播课【{}】使用".format(instance.liveCourseChatsRoom.first().name)})
        ############################################
        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


class LiveCourseMsgView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    queryset = LiveCourseMsg.objects
    serializer_class = LiveCourseMsgSerializer
    filter_class = LiveCourseMsgFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('sortNum',)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_MSG_NOT_EXISTS)
        serializer_data = LiveCourseMsgSortNumSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.updateSortNum(instance, serializer_data.validated_data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 禁用启用
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_NOT_EXISTS)
        instance.enable = not instance.enable
        instance.save()
        return Response(CHANGE_SUCCESS)


class LiveCourseBannerView(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    queryset = LiveCourseBanner.objects
    serializer_class = LiveCourseBannerSerializer

    def create(self, request, *args, **kwargs):
        serializer_data = LiveCourseBannerPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        liveCourseBanner = serializer_data.createPPT(serializer_data.validated_data)
        if liveCourseBanner:
            return Response(liveCourseBanner.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(LIVE_COURSE_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(["POST"])
def ppt2png(request):
    url = request.data.get("url", None)
    if not url:
        raise ParamError("url不能为空")
    cli = get_sts_token()
    taskid = change(cli, url.split("/")[-1], url.split("/")[2].split(".")[0])
    return Response(taskid)


@api_view(["GET"])
def querryppt2png(request):
    taskid = request.GET.get("taskid", None)
    if not taskid:
        raise ParamError("taskid不能为空")
    cli = get_sts_token()
    return Response(get_res2(cli, taskid))