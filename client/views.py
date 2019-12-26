import os
from datetime import timedelta
from itertools import groupby

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_haystack.viewsets import HaystackViewSet
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from client.clientCommon import MyPageNumberPagination
from client.filters import CommentFilter, ExpertFilter
from client.queryFilter import *
from client.serializers import *
from client.tasks import textWorker
from imageTools.imageTools import download_image, code_tool
from fileTools.uploadFile import UploadTool, delete_file
from manager_course.serializers import ChatsHistorySerializer
from parentscourse_server.config import SHARE_HOST, DEFAULT_SHARE_COURSE, DEFAULT_AVATAR
from parentscourse_server.settings import BASE_DIR
from utils.clientAuths import ClientAuthentication
from utils.clientPermission import ClientPermission
from utils.errors import ParamError
from utils.funcTools import http_return
from utils.msg import *

from utils.tencentIM2 import ServerAPI


class BasePermissionModel(object):
    """基础权限类"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]


class BannerView(BasePermissionModel,
                 viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin):
    """轮播图接口"""
    authentication_classes = []
    permission_classes = []
    queryset = Banner.objects.filter(q).order_by('orderNum')
    serializer_class = BannerSerializer
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(BANNER_QUERY_ERROR)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TagsView(BasePermissionModel,
               viewsets.GenericViewSet,
               mixins.ListModelMixin,
               mixins.RetrieveModelMixin):
    """首页标签接口"""
    authentication_classes = []
    permission_classes = []
    queryset = Tags.objects.filter(q1).order_by("-weight")
    serializer_class = TagsSerializer
    # filter_class = BannerFilter
    # filter_backends = (DjangoFilterBackend, OrderingFilter)
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(TAG_QUERY_ERROR)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SectionView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """首页展示模块"""
    authentication_classes = []
    permission_classes = []
    queryset = Section.objects.filter(q2).order_by("-weight")
    serializer_class = SectionSerializer
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(SECTION_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SectionMoreView(BasePermissionModel,
                      viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin):
    """首页展示模块"""
    authentication_classes = []
    permission_classes = []
    queryset = Section.objects.filter(q2)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要查看的板块")
        qs = super().get_queryset().filter(uuid=uuid).first()
        if not qs:
            raise ParamError("版块信息不存你")
        newQueryset = []
        for sc in qs.sectionCourseUuid.filter(status=1).order_by("-weight").all():
            if sc.courseUuid.status == 1:
                newQueryset.append(sc.courseUuid)
        return newQueryset


class MayLikeView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """猜你喜欢展示"""
    queryset = MayLike.objects.filter(q3)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        res = qs.filter(Q(userUuid__uuid=self.request.user.get("uuid")) | Q(likeType=3)).order_by("likeType",
                                                                                                  "-weight").all()
        queryList = []
        courseUuidList = []
        for re in res:
            if re.courseUuid and re.courseUuid.uuid not in courseUuidList:
                queryList.append(re.courseUuid)
                courseUuidList.append(re.courseUuid.uuid)
        return queryList


class CategroyView(BasePermissionModel,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    """分类筛选结果"""
    queryset = Tags.objects.filter(enable=1)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tagUuid = self.request.query_params.get("uuid")
        tag = qs.filter(uuid=tagUuid).first()
        if not tag:
            raise ParamError("标签不存在")
        courseUuidList = []
        for c in tag.courseTags.all():
            if c.status == 1:
                courseUuidList.append(c.uuid)
        if tag.children:
            for ta in tag.children.all():
                for c in ta.courseTags.all():
                    if c.status == 1:
                        courseUuidList.append(c.uuid)
        return Courses.objects.filter(uuid__in=list(set(courseUuidList))).order_by("-weight").all()


class BehaviorView(BasePermissionModel,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    """最近学习和已购视图视图"""
    queryset = Behavior.objects.filter(isDelete=False)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        selfUuid = self.request.user.get("uuid")
        behaviorType = self.request.query_params.get("type")
        if not behaviorType:
            raise ParamError("请选择要查看的数据")
        queryList = []
        for qinfo in qs.filter(userUuid__uuid=selfUuid, behaviorType=behaviorType).order_by("-updateTime").all():
            if qinfo.courseUuid.status == 1:
                queryList.append(qinfo.courseUuid)
        return queryList

    def create(self, request, *args, **kwargs):
        """添加行为"""
        serializers_data = BehaviorPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        res = serializers_data.create_behavior(serializers_data.validated_data, request)
        targetDict = {
            1: "点赞成功",
            2: "收藏成功"
        }
        resDict = {
            "code": 200,
            "msg": targetDict[res.behaviorType]
        }
        return Response(resDict)

    def update(self, request, *args, **kwargs):
        """更改行为"""
        serializers_data = BehaviorPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_behavior(serializers_data.data, request)
        return Response(BEHAVIOR_SUCCESS)


class CourseView(BasePermissionModel,
                 viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin):
    """课程详情视图"""
    queryset = Courses.objects.filter(q4).all()
    serializer_class = CourseSerializer
    # filter_class = CourseFilter
    # filter_backends = (DjangoFilterBackend, OrderingFilter)
    pagination_class = None

    # def get_queryset(self):
    #     uuid = self.request.query_params.get("uuid", None)
    #     if not uuid:
    #         raise ParamError(UUID_ERROR)
    #     qs = super().get_queryset().filter(uuid=uuid).all()
    #     if not qs:
    #         raise ParamError(COURSE_NOT_EXISTS)
    #     selfUuid = self.request.META.get("HTTP_TOKEN")
    #     return qs

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(COURSE_NOT_EXISTS)
        courses = instance.relatedCourse.all()
        user = request.user.get("userObj")
        behavior = Behavior.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=instance.uuid,
                                           behaviorType=3).first()
        try:
            instance.realPopularity += 1
            instance.save()
            for c in courses:
                may = MayLike.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=c.uuid).first()
                if may:
                    if may.likeType == 3:
                        may.likeType = 2
                        may.save()
                else:
                    MayLike.objects.create(
                        userUuid=user,
                        courseUuid=c,
                        likeType=2,
                    )
            if behavior:
                behavior.updateTime = datetime_to_unix(datetime.now())
                behavior.save()
            else:
                Behavior.objects.create(
                    userUuid=user,
                    courseUuid=instance,
                    behaviorType=3
                )
        except Exception as e:
            logging.error(str(e))
            raise ParamError("行为记录失败")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CourseCommentsView(BasePermissionModel,
                         viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin):
    """课程评论获取"""
    queryset = Comments.objects.filter(isDelete=False)
    serializer_class = CommentsSerializer

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要查看评论的课程")
        qs = super().get_queryset().filter(Q(isDelete=False, courseUuid__uuid=uuid) & (
                Q(interfaceStatus=2) | Q(checkStatus=2) | Q(
            userUuid__uuid=self.request.user.get("uuid")))).exclude(checkStatus=3).order_by("-createTime").all()
        return qs


class CommentView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """评论视图"""
    queryset = Comments.objects.filter(isDelete=False)
    serializer_class = CommentsSerializer
    filter_class = CommentFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """发表评论"""
        serializers_data = CommentPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        user = request.user.get("userObj")
        comment = serializers_data.create_comment(serializers_data.validated_data, user, request)
        # 评论内容审核
        textWorker.delay(comment.uuid)
        return Response(COMMENT_SEND_SUCCESS)


class CommentLikeView(BasePermissionModel,
                      viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin):
    """评论视图"""
    queryset = CommentsLike.objects.filter(status=1)
    serializer_class = CommentLikeSerializer

    def create(self, request, *args, **kwargs):
        """用户添加账户"""
        # 增
        serializers_data = CommentLikePostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_comment_like(serializers_data.validated_data, request)
        return Response(COMMENT_LIKE_CREATE_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        uuid = request.data.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要取消点赞的评论")
        commentL = CommentsLike.objects.filter(userUuid__uuid=request.user.get("uuid"), commentUuid__uuid=uuid,
                                               status=1).first()
        if commentL:
            commentL.status = 2
            try:
                commentL.save()
            except Exception as e:
                logging.error(str(e))
                raise ParamError("取消失败")
        return Response(COMMENT_LIKE_CANCEL_SUCCESS)


class CourseSourceView(BasePermissionModel,
                       viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin):
    """课程课件视图"""
    queryset = Courses.objects.filter(q4)
    serializer_class = ChapterListSerializer
    pagination_class = None

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要查看的课程")
        course = super().get_queryset().filter(uuid=uuid).first()
        user = self.request.user.get("userObj")
        qs = course.chapterCourseUuid.filter(chapterStyle__in=[2, 3], status=1).all()
        behavior = Behavior.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=course.uuid,
                                           behaviorType=5).first()
        if not if_study_course(course, user, behavior):
            raise ParamError("你还没有购买该课程，请购买")
        return qs


class LivesView(BasePermissionModel,
                viewsets.GenericViewSet,
                mixins.ListModelMixin,
                mixins.RetrieveModelMixin):
    """首页直播列表"""
    authentication_classes = []
    permission_classes = []
    queryset = CourseLive.objects.filter(q5, qRange).order_by("-weight").all()[:5]
    serializer_class = LivesSerializer
    pagination_class = None


class LivesMoreView(BasePermissionModel,
                    viewsets.GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin):
    """大咖直播展示更多"""
    queryset = CourseLive.objects.filter(q5, qRange).order_by("-weight")
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        newQueryset = []
        for c in qs.all():
            if c.courseUuid and c.courseUuid.status == 1:
                newQueryset.append(c.courseUuid)
        return newQueryset


class CourseListView(BasePermissionModel,
                     viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    """课程排行视图"""
    queryset = Courses.objects.filter(q4)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        lookType = self.request.query_params.get("type")
        qs = super().get_queryset()
        if lookType == "rank":
            return qs.order_by("-vPopularity").all()
        elif lookType == "free":
            return qs.filter(coursePermission=1).order_by("-weight").all()
        else:
            raise ParamError("参数错误")


class CoursesSearchView(BasePermissionModel,
                        viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    """搜索课程视图"""
    authentication_classes = []
    permission_classes = []
    queryset = Courses.objects.filter(q4)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        keword = self.request.query_params.get("keyword")
        if not keword:
            raise ParamError("请输入搜索关键字")
        user = self.request.user.get("userObj")
        try:
            UserSearch.objects.create(
                userUuid=user,
                keyword=keword,
            )
        except Exception as e:
            logging.error(str(e))
            raise ParamError("记录搜索历史失败")
        hot = HotSearch.objects.filter(keyword=keword).first()
        try:
            if hot:
                hot.searchNum = hot.searchNum + 1
                hot.save()
            else:
                HotSearch.objects.create(
                    keyword=keword,
                    searchNum=1,
                )
        except Exception as e:
            logging.error(str(e))
            raise ParamError("更新热搜次数失败")
        return qs.filter(name__contains=keword).all()


class HotSearchView(BasePermissionModel,
                    viewsets.GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin):
    """热搜词视图"""
    authentication_classes = []
    permission_classes = []
    queryset = HotSearch.objects.filter(status=1).order_by("-weight", "searchNum").all()[:10]
    serializer_class = HotSearchSerializer
    pagination_class = None


class SearchHistoryView(BasePermissionModel,
                        viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin):
    """搜索历史"""
    queryset = UserSearch.objects
    serializer_class = SearchHistorySerializer
    # filter_backends = (DjangoFilterBackend, OrderingFilter)
    pagination_class = None

    def get_queryset(self):
        selfUuid = self.request.user.get("uuid")
        qs = super().get_queryset()
        res = qs.filter(userUuid__uuid=selfUuid, isDelete=False).order_by("-createTime").all()
        reList = []
        markList = []
        for re in res:
            if re.keyword not in markList:
                reList.append({"keyword": re.keyword})
                markList.append(re.keyword)
        return reList[:10]

    def destroy(self, request, *args, **kwargs):
        # 清空搜索记录
        selfUuid = self.request.user.get("uuid")
        try:
            UserSearch.objects.filter(userUuid__uuid=selfUuid).update(isDelete=True)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("清空失败")
        return Response(CLEAR_SUCCESS)


class DefaultSearchView(BasePermissionModel,
                        viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin):
    authentication_classes = []
    permission_classes = []
    queryset = HotSearch.objects.filter(status__in=[1, 2], isDefault=True).order_by("-weight", "searchNum").all()[:1]
    serializer_class = HotSearchSerializer
    pagination_class = None


class CouponsView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """优惠券视图"""
    queryset = Coupons.objects.filter(q6).filter(totalNumber__gt=F("receivedNumber")).order_by("-createTime").all()
    serializer_class = CouponsSerializer


class UserCouponsView(BasePermissionModel,
                      viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin):
    """用户优惠券视图"""
    queryset = UserCoupons.objects
    serializer_class = UserCouponsSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(userUuid__uuid=self.request.user.get("uuid"))
        type = self.request.query_params.get("type")
        if type == "overdue":
            qs = qs.exclude(qRangeCoupons)
        elif type == "due":
            qs = qs.filter(qRangeCoupons)
        else:
            raise ParamError("参数错误")
        return qs.order_by("-createTime").all()

    def create(self, request, *args, **kwargs):
        """用户领取优惠券"""
        # 增
        serializers_data = UserCouponsPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        data = serializers_data.create_user_coupon(serializers_data.validated_data, request)
        return Response(data)


class ExpertsView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """专家序视图"""
    queryset = Experts.objects.filter(enable=True)
    serializer_class = ExpertSerializer
    filter_class = ExpertFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        """查询"""
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(EXPERT_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ExpertCoursesView(BasePermissionModel,
                        viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    """专家课程视图"""
    queryset = Courses.objects.filter(status=1)
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        uuid = self.request.query_params.get("uuid")
        if not uuid:
            raise ParamError("请选择要查看课程的专家")
        expert = Experts.objects.filter(uuid=uuid).first()
        if not expert:
            raise ParamError("未查询到专家信息")
        return qs.filter(expertUuid__uuid=uuid).all()


class SearchLikeView(BasePermissionModel,
                     viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    """搜索模糊匹配视图"""
    authentication_classes = []
    permission_classes = []
    queryset = Courses.objects
    serializer_class = SearchLikeSerializer
    pagination_class = None

    # filter_class = SearchLikeFilter
    # filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    # search_fields = ('name',)

    # def retrieve(self, request, *args, **kwargs):
    #     """查询"""
    #     try:
    #         instance = self.get_object()
    #     except Exception as e:
    #         logging.error(str(e))
    #         raise ParamError(COURSE_NOT_EXISTS)
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)

    def get_queryset(self):
        keyword = self.request.query_params.get("keyword")
        if not keyword:
            return []
        qs = super().get_queryset()
        return qs.filter(name__contains=keyword).filter(q4).all()[:10]


class SharesView(BasePermissionModel,
                 viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin):
    """分销记录视图"""
    queryset = Shares.objects.filter(q7)
    serializer_class = ShareSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """用户产生分销记录"""
        # 增
        user = request.user.get("userObj")
        if not user.userTelUuid.first():
            return http_return(400, "请绑定手机号后分享")
        serializers_data = SharesPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_share(serializers_data.validated_data, request)
        return Response(SHARE_SUCCESS)


class MemberCardView(BasePermissionModel,
                     viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    queryset = Goods.objects.filter(q8)
    serializer_class = MemberCardSerializer
    pagination_class = None


class ExchangeCodeView(APIView):
    """兑换会员"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        code = request.POST.get("code", None)
        if not code:
            return http_return(400, "请输入兑换码")
        invite = InviteCodes.objects.filter(status=1, code=code).first()
        if not invite:
            return http_return(400, "兑换码不可用")
        user = request.user.get("userObj")
        try:
            invite.status = 2
            invite.userUuid = user
            invite.usedTime = datetime_to_unix(datetime.now()) * 1000
            invite.save()
            inviteSet = invite.inviteSetUuid
            if not inviteSet:
                return http_return(400, "未获取到兑换码批次信息")
            goods = Goods.objects.filter(duration=inviteSet.contentTime, status=1, goodsType=3).first()
            if not goods:
                return http_return(400, "未获取到会员卡信息")
            startTime = datetime_to_unix(datetime.now())
            endTime = datetime_to_unix(datetime.now() + timedelta(days=goods.duration))
            UserInviteLog.objects.create(
                userUuid=user,
                name=invite.inviteSetUuid.name,
                dayTime=goods.duration,
                startTime=startTime,
                endTime=endTime,
                getWay=2,
                inviteSetUuid=invite.inviteSetUuid,
                inviteCode=code,
            )
            UserMember.objects.create(
                userUuid=user,
                startTime=startTime,
                endTime=endTime,
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "兑换失败")
        return http_return(200, "兑换成功")


class FeedbackView(BasePermissionModel,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    """反馈视图"""
    queryset = Feedback.objects
    serializer_class = FeedbackSerializer

    def create(self, request, *args, **kwargs):
        """用户提交反馈"""
        # 增
        serializers_data = FeedbackPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_feedback(serializers_data.validated_data, request)
        return Response(FEEDBACK_SUCCESS)


class ChatsView(BasePermissionModel,
                viewsets.GenericViewSet,
                mixins.ListModelMixin,
                mixins.RetrieveModelMixin):
    """专家发言课件视图"""
    queryset = ChatsRoom.objects
    serializer_class = ChatsSerializer

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid")
        if not uuid:
            raise ParamError("请选择需要查看消息的聊天室")
        room = super().get_queryset().filter(uuid=uuid).first()
        if not room:
            raise ParamError("聊天室不存在")
        return room.roomChatsUuid.filter(msgStatus=1).exclude(talkType="del").order_by("msgTime").all()


class DiscussView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """专家发言课件视图"""
    queryset = ChatsRoom.objects
    serializer_class = DiscussSerializer

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid")
        isQuestion = self.request.query_params.get("isQuestion")
        if not uuid:
            raise ParamError("请选择需要查看评论的聊天室")
        room = super().get_queryset().filter(uuid=uuid).first()
        if not room:
            raise ParamError("聊天室不存在")
        res = room.roomDiscussUuid.filter(msgStatus=1, talkType="txt")
        if isQuestion == 1:
            res = res.filter(isQuestion=True)
        return res.order_by("msgTime").all()


class DiscussDelView(BasePermissionModel,
                     viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.RetrieveModelMixin):
    queryset = Discuss.objects
    serializer_class = DiscussSerializer

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(BANNER_NOT_EXISTS)
        instance.talkType = "del"
        instance.save()
        return Response(DEL_SUCCESS)


class CoursesSearchViewSet(HaystackViewSet):
    """
    课程搜索搜索
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    index_models = [Courses]
    serializer_class = CoursesIndexSerializer

    def get_queryset(self, index_models=[]):
        text = self.request.query_params.get("text")
        if not text:
            raise ParamError("请输入搜索关键字")
        user = self.request.user.get("userObj")
        try:
            UserSearch.objects.create(
                userUuid=user,
                keyword=text,
            )
        except Exception as e:
            logging.error(str(e))
            raise ParamError("记录搜索历史失败")
        hot = HotSearch.objects.filter(keyword=text).first()
        try:
            if hot:
                hot.searchNum = hot.searchNum + 1
                hot.save()
            else:
                HotSearch.objects.create(
                    keyword=text,
                    searchNum=1,
                )
        except Exception as e:
            logging.error(str(e))
            raise ParamError("更新热搜次数失败")
        super().get_queryset()
        if self.queryset is not None and isinstance(self.queryset, self.object_class):
            queryset = self.queryset.filter(status=1).all()
        else:
            queryset = self.object_class()._clone()
            if len(index_models):
                queryset = queryset.models(*index_models)
            elif len(self.index_models):
                queryset = queryset.models(*self.index_models)
        return queryset


class CashAccountListView(BasePermissionModel,
                          viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.RetrieveModelMixin):
    """账户视图"""
    queryset = CashAccount.objects.filter(status=1)
    serializer_class = CashAccountSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        selfUuid = self.request.user.get("uuid")
        res = qs.filter(userUuid__uuid=selfUuid)
        return res


class CashAccountView(BasePermissionModel,
                      viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.RetrieveModelMixin):
    """账户视图"""
    queryset = CashAccount.objects.filter(status=1)
    serializer_class = CashAccountSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """用户添加账户"""
        # 增
        serializers_data = CashAccountPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_cash_account(serializers_data.validated_data, request)
        return Response(ACCOUNT_CREATE_SUCCESS)

    def retrieve(self, request, *args, **kwargs):
        # 查
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(ACCOUNT_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # 改
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(ACCOUNT_NOT_EXISTS)
        serializer_data = CashAccountPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        checkMsg = serializer_data.update_cash_account(instance, serializer_data.data)
        if checkMsg:
            return Response(PUT_SUCCESS)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(ACCOUNT_NOT_EXISTS)
        instance.status = 3
        instance.save()
        return Response(DEL_SUCCESS)


class PromoteView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.RetrieveModelMixin):
    """推广中心课程列表视图"""
    queryset = Goods.objects.filter(status=1, goodsType__in=[1, 2], rewardStatus=True)
    serializer_class = PromoteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        coursesUuidList = [g.content for g in qs.all() if g.content]
        return Courses.objects.filter(status=1, uuid__in=coursesUuidList).order_by("-weight", "-createTime").all()


class PromoteCouponsView(BasePermissionModel,
                         viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.RetrieveModelMixin):
    """推广中心优惠券视图"""
    queryset = Coupons.objects.filter(goodsUuid__rewardStatus=True, couponType=1, status=1).filter(qRangeEnd)
    serializer_class = PromoteCouponsSerializer


class StudyHistoryView(BasePermissionModel, APIView):
    """浏览历史视图"""

    pagination_class = None

    def get(self, request):
        selfUuid = request.user.get("uuid")
        qs = Behavior.objects.filter(behaviorType=3, isDelete=False, userUuid__uuid=selfUuid).order_by(
            "-createTime").all()
        serializer = StudyHistorySerializer(qs, many=True)
        result = []
        for cdate, items in groupby(list(serializer.data),
                                    key=lambda x: unix_time_to_datetime(x["createTime"]).date()):
            result.append({
                "date": cdate,
                "items": list(items),
            })
        return Response(result)

    def delete(self, request):
        """删除浏览历史"""
        uuidList = request.data.get("uuidList", None)
        if not uuidList:
            raise ParamError("请选择要删除的浏览记录")
        try:
            Behavior.objects.filter(uuid__in=uuidList, userUuid__uuid=request.user.get("uuid")).update(isDelete=True)
        except Exception as e:
            logging.error(str(e))
            raise ParamError("删除失败")
        return Response(DEL_SUCCESS)


class CouponsCourseView(BasePermissionModel,
                        viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.RetrieveModelMixin):
    """优惠券可用课程"""
    queryset = Goods.objects.filter(status=1, isCoupon=True).all()
    serializer_class = CourseListSerializer

    def get_queryset(self):
        uuid = self.request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要使用的优惠券")
        userCoupon = UserCoupons.objects.filter(uuid=uuid, status=1).first()
        if not userCoupon:
            raise ParamError("未获取到优惠券信息")
        qs = super().get_queryset()
        couponType = userCoupon.couponsUuid.couponType
        accountMoney = userCoupon.couponsUuid.accountMoney if userCoupon.couponsUuid and userCoupon.couponsUuid.accountMoney else 0
        scopeList = [int(sc) for sc in userCoupon.couponsUuid.scope.split(",") if sc != ""]
        if couponType == 2:
            qs = qs.filter(goodsType__in=scopeList).filter(realPrice__lte=accountMoney)
        elif couponType == 3:
            qs = qs.filter(realPrice__lte=accountMoney)
        else:
            raise ParamError("未知优惠券类型")
        uuidList = qs.values("content").distinct()
        return Courses.objects.filter(q4, uuid__in=uuidList).all()


class BuyCoursesView(BasePermissionModel,
                     viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.RetrieveModelMixin):
    """已购课程视图"""
    queryset = Behavior.objects.filter(isDelete=False)
    serializer_class = BuyCoursesSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        selfUuid = self.request.user.get("uuid")
        queryInfo = qs.filter(userUuid__uuid=selfUuid, behaviorType=5).all()
        return queryInfo


class CourseUseCouponsView(BasePermissionModel,
                           viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.DestroyModelMixin,
                           mixins.RetrieveModelMixin):
    """已购课程视图"""
    queryset = UserCoupons.objects.filter(status=1)
    serializer_class = UserCouponsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        uuid = self.request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要查看可用优惠券的课程")
        good = Goods.objects.filter(content=uuid).first()
        if not good or not good.isCoupon:
            return []
        res = qs.filter(userUuid__uuid=self.request.user.get("uuid")).filter(qRangeCouponsUse).order_by(
            "-createTime").all()
        objQueryset = []
        for r in res:
            coupon = r.couponsUuid
            if coupon:
                if coupon.couponType == 1 and coupon.goodsUuid.content == uuid and good.realPrice >= coupon.money:
                    objQueryset.append(r)
                elif coupon.couponType == 2 and str(good.goodsType) in coupon.scope.split(
                        ",") and good.realPrice >= coupon.accountMoney and good.realPrice >= coupon.money:
                    objQueryset.append(r)
                elif coupon.couponType == 3 and good.realPrice >= coupon.accountMoney and good.realPrice >= coupon.money:
                    objQueryset.append(r)
        return objQueryset


class GetShareImgView(APIView):
    """
    获取分享链接
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        if not user.userTelUuid.first():
            return http_return(400, "请绑定手机号后分享")
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要分享的课程")
        course = Courses.objects.filter(uuid=uuid).first()
        if not course:
            return http_return(400, "课程不存在")
        checkShare = Shares.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=uuid).first()
        if not checkShare:
            good = Goods.objects.filter(content=course.uuid, rewardStatus=True).first()
            price = 0
            if good:
                price = float(int(good.realPrice * good.rewardPercent * 10 / 10000) / 10)
            toolDir = os.path.join(BASE_DIR, 'imageTools')
            avatarPath = os.path.join(toolDir, user.uuid + ".png")
            backgroundUrlPath = os.path.join(toolDir, course.uuid + user.uuid + ".png")
            coursePath = os.path.join(toolDir, user.uuid + course.uuid + ".png")
            try:
                avatar = user.avatar if user.avatar else DEFAULT_AVATAR
                download_image(avatar, avatarPath, "avatar")  # 下载头像
                centerUrlName = os.path.join(toolDir, "QRcenter.jpg")
                sharUrl = SHARE_HOST + "/" + course.uuid + "/" + user.uuid
                fontPath = os.path.join(toolDir, "wFont.ttf")
                logoPath = os.path.join(toolDir, "logo.png")
                shareImg = course.shareImg if course.shareImg else DEFAULT_SHARE_COURSE
                download_image(shareImg, coursePath, "course")
                nickName = user.nickName
                if match_tel(nickName):
                    nickName = get_default_name(nickName)
                code_tool(backgroundUrlPath, sharUrl, centerUrlName, price, nickName, fontPath, logoPath, coursePath,
                          avatarPath)
                upload = UploadTool()
                cresInfo = upload.put_file(backgroundUrlPath)
                if cresInfo["code"] != 200:
                    return http_return(400, "文件上传失败")
                backgroundUrl = cresInfo["data"]["url"] + "?x-oss-process=image/resize,w_600,h_696/rounded-corners,r_30"
                checkShare = Shares.objects.create(
                    courseUuid=course,
                    userUuid=user,
                    shareUrl=sharUrl,
                    realPrice=good.realPrice,
                    rewardPercent=good.rewardPercent,
                    shareImg=backgroundUrl
                )
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "获取分享图失败")
            finally:
                delete_file([avatarPath, backgroundUrlPath, coursePath])
        resList = list()
        resList.append(checkShare.shareImg)
        return Response(resList)


class FollowExpertView(APIView):
    """
    关注，取消关注专家
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def post(self, request):
        uuid = request.data.get("uuid", None)
        operaType = request.data.get("type", None)
        if not uuid:
            return http_return(400, "请选择要关注的专家")
        expert = Experts.objects.filter(uuid=uuid).first()
        if not expert:
            return http_return(400, "专家不存在")
        userUuid = request.user.get("uuid")
        user = User.objects.filter(uuid=userUuid).first()
        checkFollow = FollowExpert.objects.filter(userUuid__uuid=userUuid, expertUuid__uuid=uuid).first()
        if operaType == "follow":
            if checkFollow:
                if checkFollow.status != 1:
                    checkFollow.status = 1
                    try:
                        checkFollow.save()
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, "关注失败")
            else:
                FollowExpert.objects.create(userUuid=user, expertUuid=expert)
            return http_return(200, "关注成功")
        else:
            if checkFollow:
                if checkFollow.status == 1:
                    checkFollow.status = 2
                    try:
                        checkFollow.save()
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, "取消关注失败")
            return http_return(200, "取消关注成功")


class LikeRoomListView(APIView):
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        likeRooms = LikeRoom.objects.filter(userUuid__uuid=request.user.get("uuid"), isDelete=False, type=1).order_by(
            "-createTime").all()
        rooms = [like.roomUuid for like in likeRooms if like.roomUuid]
        pg = MyPageNumberPagination()
        pager_rooms = pg.paginate_queryset(queryset=rooms, request=request, view=self)
        ser = RoomSerializer(instance=pager_rooms, context={"request": request}, many=True)
        return pg.get_paginated_response(ser.data)

    def post(self, request):
        roomUuid = request.data.get("uuid", None)
        if not roomUuid:
            return http_return(400, "请选择要收藏的直播间")
        room = ChatsRoom.objects.filter(uuid=roomUuid).first()
        if not room:
            return http_return(400, "直播间不存在")
        userUuid = request.user.get("uuid")
        checkLike = LikeRoom.objects.filter(userUuid__uuid=userUuid, roomUuid__uuid=roomUuid, type=1).first()
        if checkLike:
            if checkLike.isDelete:
                checkLike.isDelete = False
                try:
                    checkLike.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, "收藏失败")
        else:
            LikeRoom.objects.create(
                userUuid=request.user.get("userObj"),
                roomUuid=room,
                remarks="收藏聊天室",
                type=1
            )
        return http_return(200, "收藏成功")

    def delete(self, request):
        uuid = request.data.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要取消收藏的聊天室")
        userUuid = request.user.get("uuid")
        checkLike = LikeRoom.objects.filter(userUuid__uuid=userUuid, roomUuid__uuid=uuid, type=1).first()
        if checkLike:
            if not checkLike.isDelete:
                checkLike.isDelete = True
                try:
                    checkLike.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, "取消收藏失败")
        return http_return(200, "取消收藏成功")


class RoomDetailView(APIView):
    """聊天室详情视图"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        uuid = request.query_params.get("uuid")
        if uuid:
            chapter = Chapters.objects.filter(uuid=uuid, chapterStyle=1).first()
            if not chapter:
                return http_return(400, "章节不存在")
            course = chapter.courseUuid
            user = request.user.get("userObj")
            behavior = Behavior.objects.filter(userUuid=user.uuid, courseUuid__uuid=course.uuid, behaviorType=5,
                                               isDelete=False).first()
            if not if_study_course(course, user, behavior):
                return http_return(400, "你还没有购买该课程，请购买")
            room = chapter.roomUuid
            checkRight = LikeRoom.objects.filter(userUuid__uuid=request.user.get("uuid"), roomUuid__uuid=room.uuid,
                                                 type=2).first()
            if not checkRight:
                LikeRoom.objects.create(
                    userUuid=request.user.get("userObj"),
                    roomUuid=room,
                    type=2
                )
        else:
            roomUuid = request.query_params.get("roomUuid", None)
            if not roomUuid:
                return http_return(400, "请选择要进入的聊天室")
            right = LikeRoom.objects.filter(userUuid__uuid=request.user.get("uuid"), roomUuid__uuid=roomUuid,
                                            type=2).first()
            if not right:
                return http_return(400, "没有购买该课程，不能进入直播间")
            room = ChatsRoom.objects.filter(uuid=roomUuid).first()
        if room and room.startTime > datetime_to_unix(datetime.now()):
            return http_return(400, "直播未开始")
        data = RoomSerializer(room, many=False, context={"request": request}).data
        return Response(data)


class CheckRoomRight(APIView):
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要进入的聊天室")
        right = LikeRoom.objects.filter(userUuid__uuid=request.user.get("uuid"), roomUuid__uuid=uuid,
                                        type=2).first()
        haveRight = True if right else False
        return http_return(200, "成功", haveRight)


class RelatCourseView(APIView):
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择课程")
        course = Courses.objects.filter(uuid=uuid, status=1).first()
        if not course:
            return http_return(400, "未获取到课程信息")
        courses = course.relatedCourse.filter(status=1).order_by("-createTime").all()
        pg = MyPageNumberPagination()
        pager_course = pg.paginate_queryset(queryset=courses, request=request, view=self)
        ser = CourseListSerializer(instance=pager_course, many=True)
        return pg.get_paginated_response(ser.data)


class RoomChatsDetailView(APIView):
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        uuid = request.query_params.get("uuid", None)
        if not uuid:
            raise ParamError("请选择要进入的聊天室")
        if IM_PLATFORM == "TM":
            room = ChatsRoom.objects.filter(tmId=uuid).first()
        else:
            room = ChatsRoom.objects.filter(huanxingId=uuid).first()
        if not room:
            raise ParamError("聊天室不存在")
        chat = Chats.objects.filter(roomUuid=room, msgStatus=1).order_by("msgSeq")
        isQuestion = request.query_params.get("isQuestion", None)
        if isQuestion != None:
            targetDict = {"true": True, "false": False}
            chat = chat.filter(isQuestion=targetDict[str(isQuestion)])
        displayPos = request.query_params.get("displayPos", None)
        if displayPos != None:
            chat = chat.filter(displayPos=displayPos)
        pg = MyPageNumberPagination()
        pager_chat = pg.paginate_queryset(queryset=chat.all(), request=request, view=self)
        ser = ChatsHistorySerializer(instance=pager_chat, many=True)
        return pg.get_paginated_response(ser.data)


class DelChatView(APIView):
    """删除聊天记录"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def put(self, request):
        uuid = request.data.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择要删除信息的用户")
        msgTime = request.data.get("msgTime", None)
        if not msgTime:
            return http_return(400, "请选择发消息时间")
        content = """"msg_time":{0}""".format(str(msgTime))
        try:
            Chats.objects.filter(fromAccountUuid__uuid=uuid, content__contains=content).update(
                msgStatus=3
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "删除失败")
        return http_return(200, "删除成功")


class PutWallView(APIView):
    """上墙"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def put(self, request):
        uuid = request.data.get("uuid", None)
        if not uuid:
            return http_return(400, "请选择上墙信息的用户")
        msgTime = request.data.get("msgTime", None)
        if not msgTime:
            return http_return(400, "请选择上墙消息时间")
        content = """"msg_time":{0}""".format(str(msgTime))
        try:
            Chats.objects.filter(fromAccountUuid__uuid=uuid, content__contains=content).update(
                isWall=True
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "上墙失败")
        return http_return(200, "上墙成功")


class BanSayView(APIView):
    """用户禁言"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        roomId = request.data.get("roomId", None)
        if not roomId:
            return http_return(400, "请选择要查看的转态的聊天室")
        room = ChatsRoom.objects.filter(tmId=roomId).first()
        if not room:
            return http_return(400, "聊天室不存在")
        userUuid = request.data.get("userUuid", None)
        if not userUuid:
            return http_return(400, "请选择要查看状态的用户")
        user = User.objects.filter(uuid=userUuid).first()
        if not user:
            return http_return(400, "用户不存在")
        banSay = BanSay.objects.filter(roomUuid=roomId, userUuid=userUuid, status=1).first()
        return http_return(200, "成功", {"isBan": True if banSay else False})

    def post(self, request):
        roomId = request.data.get("roomId", None)
        if not roomId:
            return http_return(400, "请选择要查看的转态的聊天室")
        room = ChatsRoom.objects.filter(tmId=roomId).first()
        if not room:
            return http_return(400, "聊天室不存在")
        userUuid = request.data.get("userUuid", None)
        if not userUuid:
            return http_return(400, "请选择要查看状态的用户")
        user = User.objects.filter(uuid=userUuid).first()
        if not user:
            return http_return(400, "用户不存在")
        expire = request.data.get("expire", 0)
        if not isinstance(expire, int):
            return http_return(400, "expire需要时整数")
        if expire < 0:
            return http_return(400, "expire需要大于等于0")
        api = ServerAPI()
        res = api.mute(roomId, userUuid, expire)
        if not res:
            return http_return(400,"操作失败")
        if expire:
            return http_return(200, "禁言成功，禁言时间{}s".format(expire))
        else:
            return http_return(200, "恢复禁言成功")
        banSay = BanSay.objects.filter(roomUuid=userUuid, userUuid=userUuid).first()
        if banSay:
            if banSay.status == 2:
                try:
                    banSay.status = 1
                    banSay.expire = int(expire)
                    banSay.save()
                except Exception as e:
                    logging.error(str(e))
        else:
            try:
                BanSay.objects.create(
                    roomUuid=chatRoomId,
                    userUuid=userName,
                    expire=int(expire)
                )
            except Exception as e:
                logging.error(str(e))


    def put(self, request):
        roomId = request.data.get("roomId", None)
        if not roomId:
            return http_return(400, "请选择要查看的转态的聊天室")
        room = ChatsRoom.objects.filter(tmId=roomId).first()
        if not room:
            return http_return(400, "聊天室不存在")
        userUuid = request.data.get("userUuid", None)
        if not userUuid:
            return http_return(400, "请选择要查看状态的用户")
        user = User.objects.filter(uuid=userUuid).first()
        if not user:
            return http_return(400, "用户不存在")
        banSay = BanSay.objects.filter(roomUuid=userUuid, userUuid=userUuid).first()
        if banSay:
            if banSay.createTime + timedelta(seconds=banSay.expire) <= datetime.now():
                return http_return(400, "禁言时间未过，不能解禁")
            else:
                banSay.status = 2
                try:
                    banSay.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, "解禁失败")
        return http_return(200, "解禁成功")


"""定时迁移数据"""
# scheduler = None
# try:
#     scheduler = BackgroundScheduler()
#
#
#     @register_job(scheduler, 'cron', hour='1', minute='30', id='task_migrate')
#     def migrate_job():
#         if version == "debug":
#             pass
#         elif version == "test":
#             pass
#         elif version == "ali_test":
#             endTime = get_day_zero_time(datetime.now())
#             startTime = endTime - timedelta(days=1)
#             get_user(startTime, endTime)  # 从hbb迁移到本系统
#             post_user(startTime, endTime)  # 本系统迁移到hbb
#
#
#     register_events(scheduler)
#     scheduler.start()
# except Exception as e:
#     logging.error(str(e))
#     scheduler.shutdown()
