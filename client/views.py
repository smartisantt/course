from datetime import timedelta
from itertools import groupby

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from client.filters import CommentFilter, ExpertFilter
from client.insertQuery import if_study_course
from client.queryFilter import *
from client.serializers import *
from utils.clientAuths import ClientAuthentication
from utils.clientPermission import ClientPermission
from utils.errors import ParamError
from utils.funcTools import http_return
from utils.msg import *
from utils.qFilter import HOT_SEARCH_Q
from drf_haystack.viewsets import HaystackViewSet
from client.tasks import textWorker


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
        for sc in qs.sectionCourseUuid.filter(status=1).all():
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
        for re in res:
            queryList.append(re.courseUuid)
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
        tag = qs.filter(uuid=tagUuid)
        if not tag:
            raise ParamError("标签不存在")
        tagChildren = tag.first().children.filter(enable=True).all()
        courses = Courses.objects.filter(
            Q(tags__uuid=tagUuid) | Q(tags__uuid__in=[t.uuid for t in tagChildren if tagChildren]))
        return courses.order_by("-weight").all()


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
        queryList = []
        for qinfo in qs.filter(userUuid__uuid=selfUuid, behaviorType=behaviorType).all():
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
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        behavior = Behavior.objects.filter(userUuid__uuid=user.uuid, courseUuid__uuid=instance.uuid,
                                           behaviorType=3).filter(qRangeToday).first()
        try:
            for c in courses:
                MayLike.objects.create(
                    userUuid=user,
                    courseUuid=c,
                    likeType=2,
                )
            if not behavior:
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
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
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
        user = User.objects.filter(uuid=self.request.user.get("uuid")).first()
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
    queryset = CourseLive.objects.filter(q5, qRange).all()[:5]
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
            return qs.filter(coursePermission=1).order_by("-updateTime").all()
        else:
            raise ParamError("参数错误")


class UserInfoView(BasePermissionModel,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    queryset = User.objects.filter(q5)
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        selfUuid = self.request.user.get("uuid")
        return qs.filter(uuid=selfUuid)


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
        selfUuid = self.request.user.get("uuid")
        user = User.objects.filter(uuid=selfUuid).first()
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
    queryset = HotSearch.objects.filter(HOT_SEARCH_Q).order_by("-weight", "searchNum").all()[:10]
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
        return qs.filter(userUuid__uuid=selfUuid, isDelete=False).values("keyword").distinct().reverse()[:10]

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
        return qs.all()

    def create(self, request, *args, **kwargs):
        """用户领取优惠券"""
        # 增
        serializers_data = UserCouponsPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        data = serializers_data.create_user_coupon(serializers_data.validated_data, request)
        # resInfo = {
        #     "code": 200,
        #     "msg": "优惠券领取成功",
        #     "data": data
        # }
        return Response(data)


class ExpertsView(BasePermissionModel,
                  viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """专家序视图"""
    queryset = Experts.objects.filter(enable=False)
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
    queryset = Courses.objects
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
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
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
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
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


class RoomView(BasePermissionModel,
               viewsets.GenericViewSet,
               mixins.ListModelMixin,
               mixins.RetrieveModelMixin):
    """聊天室详情视图"""
    queryset = Chapters.objects.filter(status=1)
    serializer_class = RoomSerializer
    pagination_class = None

    def get_queryset(self):
        """获取聊天室信息"""
        uuid = self.request.query_params.get("uuid")
        if not uuid:
            raise ParamError("请选择要进入的聊天室")
        qs = super().get_queryset().filter(uuid=uuid, chapterStyle=1).first()
        course = qs.courseUuid
        user = User.objects.filter(uuid=self.request.user.get("uuid")).first()
        if not if_study_course(course, user):
            raise ParamError("你还没有购买该课程，请购买")
        return qs.roomUuid


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
        selfUuid = self.request.user.get("uuid")
        if not text:
            raise ParamError("请输入搜索关键字")
        user = User.objects.filter(uuid=selfUuid).first()
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
            queryset = self.queryset.all()
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
        coursesUuidList = [g.content for g in qs.all()]
        return Courses.objects.filter(status=1, uuid__in=coursesUuidList).order_by("-weight", "-createTime").all()


class PromoteCouponsView(BasePermissionModel,
                         viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.RetrieveModelMixin):
    """推广中心优惠券视图"""
    queryset = Coupons.objects.filter(couponType=1, status=1).filter(qRange)
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
            raise ParamError("请选择要查看可用优惠券的类型")
        good = Goods.objects.filter(content=uuid).first()
        if not good:
            return []
        res = qs.filter(userUuid__uuid=self.request.user.get("uuid")).order_by("-createTime").all()
        objQueryset = []
        for r in res:
            coupon = r.couponsUuid
            if coupon:
                if coupon.couponType == 1 and coupon.goodsUuid.content == uuid:
                    objQueryset.append(r)
                elif coupon.couponType == 2 and str(good.goodsType) in coupon.scope.split(","):
                    objQueryset.append(r)
                elif coupon.couponType == 3 and good.realPrice > coupon.accountMoney:
                    objQueryset.append(r)
        return objQueryset
