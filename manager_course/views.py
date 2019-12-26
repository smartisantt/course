import time

from django.db import transaction
from django.db.models import Max
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework import mixins, viewsets, status, request
from rest_framework.response import Response
# Create your views here.
from client.models import Chats
from common.models import Courses, Chapters, ChatsRoom, User
from manager_course.filters import CourseFilter, ChapterFilter, DummyUserFilter, ChatsHistoryFilter
from manager_course.serializers import CourseSaveSerializer, CourseSelectSerializer, CourseUpdateSerializer, \
    CourseInfoSerializer, CourseDeleteSerializer, CourseUpdateStatusSerializer, ChaptersSelectSerializer, \
    ChapterSaveSerializer, ChaptersInfoSerializer, ChapterUpdateSerializer, ChapterDeleteSerializer, \
    ChapterExchangeSerializer, DummyUserSerializer, DummyUserPostSerializer, ChatsHistorySerializer
from parentscourse_server.config import IM_PLATFORM
from utils.tencentIM2 import ServerAPI
from utils.errors import ParamError
from utils.msg import SECTION_NOT_EXISTS, PUT_SUCCESS, CHANGE_SUCCESS, MAX_WEIGHT_ERROR, COURSE_NOT_EXISTS, \
    MAX_WEIGHT_SUCCESS, CHAPTER_NOT_EXISTS, EXCHANGE_NUMBER_SUCCESS, CHAT_ROOM_NOT_EXISTS, \
    LIVE_COURSE_END_SUCCESS, LIVE_COURSE_START_SUCCESS, POST_SUCCESS, MSG_NOT_EXISTS, DEL_SUCCESS


class CourseView(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = Courses.objects.exclude(status__in=[3, 4]).order_by("-weight").all()
    serializer_class = CourseSelectSerializer
    filter_class = CourseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight",)

    @transaction.atomic  # 加事务锁
    def create(self, request, *args, **kwargs):
        serializer_data = CourseSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        instance = serializer_data.create(serializer_data.validated_data)
        goods = serializer_data.create_goods(serializer_data.validated_data, instance)
        if instance.courseType == 1:
            chat_room = None
            if serializer_data.data["chapterStyle"] == 1:
                """        修改直播课件关联的banner       """
                serializer_data.update_live_course(serializer_data.validated_data)
                chat_room = serializer_data.create_chat_room(serializer_data.validated_data, request)
            chapter = serializer_data.create_chapter(serializer_data.validated_data, instance, chat_room)
        return Response(serializer_data.initial_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COURSE_NOT_EXISTS)
        serializer = CourseInfoSerializer(instance)
        return Response(serializer.data)

    @transaction.atomic  # 加事务锁
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = CourseUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkedData = serializer_data.check_params(instance, serializer_data.validated_data)
        course = serializer_data.updateCourse(instance, checkedData, request)
        chapter = Chapters.objects.filter(courseUuid=instance).first()
        goods = serializer_data.updateGoods(instance, checkedData)
        if instance.courseType == 1:
            chat_room = None
            if chapter.chapterStyle == 1:
                """         修改直播课件关联的banner(前提是有传banner)         """
                serializer_data.update_live_course(serializer_data.validated_data)
                chat_room = serializer_data.update_chat_room(instance, checkedData)
            chapter = serializer_data.update_chapter(checkedData, instance, chat_room)
        return Response(PUT_SUCCESS)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        self.queryset = Courses.objects.filter().order_by("-weight").all()
        instance = self.get_object()
        serializer_data = CourseDeleteSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        deleteResult = serializer_data.change_status(instance, serializer_data.data)
        if deleteResult:
            return Response(CHANGE_SUCCESS)

    @action(methods=['put'], detail=True)
    def weight(self, request, pk):
        course = self.get_object()
        max_weight = self.queryset.aggregate(Max('weight'))["weight__max"]
        max_course = Courses.objects.filter(weight=max_weight).first()
        if course == max_course:
            raise ParamError(MAX_WEIGHT_ERROR)
        course.weight = max_weight + 1
        course.save()
        return Response(MAX_WEIGHT_SUCCESS)

    @action(methods=['put'], detail=True)
    def updateStatus(self, request, pk):
        course = self.get_object()
        serializer_data = CourseUpdateStatusSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.update_status(course, serializer_data.data)
        return Response(CHANGE_SUCCESS)

    # 手动开始直播课
    @action(methods=['put'], detail=False)
    def startLiveCourse(self, request):
        liveRoomId = request.data.get("liveRoomId", None)
        if not liveRoomId:
            raise ParamError("直播课Id不能为空")
        if IM_PLATFORM == "TM":
            chatRoom = ChatsRoom.objects.filter(tmId=liveRoomId).first()
        else:
            chatRoom = ChatsRoom.objects.filter(huanxingId=liveRoomId).first()

        if not chatRoom:
            raise ParamError(CHAT_ROOM_NOT_EXISTS)
        if chatRoom.liveStatus != 1:
            raise ParamError("当前状态操作无效")
        if chatRoom.startTime < time.time() * 1000 or chatRoom.liveStatus == 2:
            raise ParamError("直播课已开始")
        chatRoom.actualStartTime = int(time.time() * 1000)
        chatRoom.startTime = int(time.time() * 1000)
        chatRoom.liveStatus = 2
        chatRoom.save()
        # 课程更新状态1：已完结 2：更新中,3未开始 4 直播结束 5 直播中  6 直播未开始
        # 更改课程状态 updateStatus 5 直播中
        chapter = Chapters.objects.filter(roomUuid=chatRoom).first()
        if chapter:
            chapter.updateStatus = 5
            chapter.save()

        return Response(LIVE_COURSE_START_SUCCESS)

    # 手动结束直播课
    @action(methods=['put'], detail=False)
    def endLiveCourse(self, request):
        liveRoomId = request.data.get("liveRoomId", None)
        if not liveRoomId:
            raise ParamError("直播课Id不能为空")
        if IM_PLATFORM == "TM":
            chatRoom = ChatsRoom.objects.filter(tmId=liveRoomId).first()
        else:
            chatRoom = ChatsRoom.objects.filter(huanxingId=liveRoomId).first()

        if not chatRoom:
            raise ParamError(CHAT_ROOM_NOT_EXISTS)
        if chatRoom.liveStatus not in [1, 2]:
            raise ParamError("当前状态操作无效")

        if chatRoom.startTime > time.time() * 1000 and chatRoom.liveStatus == 1:
            raise ParamError("直播课未开始")
        chatRoom.endTime = int(time.time() * 1000)
        chatRoom.liveStatus = 3  # 聊天室状态
        chatRoom.save()
        # 更改课程状态 updateStatus 4 已完结
        chapter = Chapters.objects.filter(roomUuid=chatRoom).first()
        if chapter:
            chapter.updateStatus = 4
            chapter.save()

        return Response(LIVE_COURSE_END_SUCCESS)

    # @action(methods=['get'], detail=True)
    # def chapter(self, request, pk):
    #     course = self.get_object()
    #     queryset = Chapters.objects.filter(courseUuid=course).exclude(status=4).order_by("serialNumber").all()
    #     if request.method == "GET":
    #         Filter = ChapterFilter(request.GET, queryset=queryset)
    #         serializer_class = ChaptersSelectSerializer(Filter.qs, many=True)
    #         return Response(serializer_class.data)


class RecyclingView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet):
    queryset = Courses.objects.filter(status=3).order_by("-weight").all()
    serializer_class = CourseSelectSerializer
    filter_class = CourseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("-weight",)


class ChapterView(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet):
    queryset = Chapters.objects.exclude(status=4).all()
    serializer_class = ChaptersSelectSerializer
    filter_class = ChapterFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ("serialNumber",)

    @transaction.atomic  # 加事务锁
    def create(self, request, *args, **kwargs):
        serializer_data = ChapterSaveSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        instance = serializer_data.create_chapter(serializer_data.validated_data)
        if instance.chapterStyle == 1:
            serializer_data.update_live_course(serializer_data.validated_data)
            chat_room = serializer_data.create_chatRoom(serializer_data.validated_data)
            instance.roomUuid = chat_room
            instance.save()

        return Response(serializer_data.initial_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(CHAPTER_NOT_EXISTS)
        serializer = ChaptersInfoSerializer(instance)
        return Response(serializer.data)

    @transaction.atomic  # 加事务锁
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = ChapterUpdateSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkedData = serializer_data.check_params(instance, serializer_data.validated_data)
        chapter = serializer_data.updateChapter(instance, serializer_data.validated_data)
        if instance.chapterStyle == 1:
            serializer_data.update_live_course(serializer_data.validated_data)
            chat_room = serializer_data.update_chatRoom(instance, serializer_data.validated_data)
            instance.roomUuid = chat_room
            instance.save()

        return Response(PUT_SUCCESS)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = ChapterDeleteSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        deleteResult = serializer_data.change_status(instance, serializer_data.data)
        if deleteResult:
            return Response(CHANGE_SUCCESS)

    @action(methods=['put'], detail=True)
    def isTry(self, request, pk):
        instance = self.get_object()
        instance.isTry = not instance.isTry
        instance.save()
        return Response(CHANGE_SUCCESS)

    @action(methods=['put'], detail=True)
    def exchange(self, request, pk):
        instance = self.get_object()
        serializer_data = ChapterExchangeSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        changeResult = serializer_data.change_serialNumber(instance, serializer_data.data)
        if changeResult:
            return Response(EXCHANGE_NUMBER_SUCCESS)


class DummyUserView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = User.objects.filter(isMajia=True).order_by("-createTime").all()
    serializer_class = DummyUserSerializer
    filter_class = DummyUserFilter

    def create(self, request, *args, **kwargs):
        serializer_data = DummyUserPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        maUser = serializer_data.create_maUser(serializer_data.validated_data)
        if not maUser:
            raise ParamError(serializer_data.errors)
        server = ServerAPI()
        server.createUser(maUser.uuid, maUser.nickName, maUser.avatar)
        return Response(POST_SUCCESS)


class RandomDummyView(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    queryset = User.objects.filter(isMajia=True).order_by("?").all()[:1]
    serializer_class = DummyUserSerializer
    filter_class = DummyUserFilter
    pagination_class = None


class ChatsHistoryView(mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    # 已撤回的消息不做展示
    queryset = Chats.objects.exclude(msgStatus=2).order_by("msgSeq")
    serializer_class = ChatsHistorySerializer

    filter_class = ChatsHistoryFilter

    def get_queryset(self):
        qs = super().get_queryset()
        uuid = self.request.query_params.get("uuid")
        if not uuid:
            raise ParamError("请选择要进入的聊天室")
        if IM_PLATFORM == "TM":
            room = ChatsRoom.objects.filter(tmId=uuid).first()
        else:
            room = ChatsRoom.objects.filter(huanxingId=uuid).first()
        if not room:
            raise ParamError("聊天室不存在")
        qs = qs.filter(roomUuid=room)
        isQuestion = self.request.query_params.get("isQuestion", None)
        if isQuestion != None:
            qs = qs.filter(msgStatus=1)
        # displayPos = self.request.query_params.get("displayPos", None)
        # if displayPos != None:
        #     qs = qs.filter(displayPos=displayPos)
        # resQs = qs.filter(roomUuid__uuid=uuid).order_by("msgSeq").all()
        return qs

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(MSG_NOT_EXISTS)
        if instance.msgStatus != 1:
            raise ParamError("该消息状态无法删除")
        instance.msgStatus = 3
        instance.save()
        return Response(DEL_SUCCESS)