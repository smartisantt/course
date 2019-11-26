from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from common.models import Orders, OrderDetail, Payment, User, Withdrawal

# 用户的消费记录视图
from manager_distribution.filters import CourseRepreslFilter, OrderBasicFilter, OrderBasic2Filter, WithdrawalFilter
from manager_distribution.serializers import CourseRepresSerializer, OrderBasicSerializer, OrderBasic2Serializer, \
    WithdrawalSerializer, WithdrawalUpdateSerializer
from manager_order.filters import OrderDetailFilter
from manager_order.serializers import OrderDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


# 订单列表  分销表
from utils.errors import ParamError
from utils.msg import USER_NOT_EXISTS, DEL_SUCCESS, CHANGE_SUCCESS, WITHDRAWAL_NOT_EXISTS, PUT_SUCCESS
from utils.qFilter import USER_Q, DISTRIBUTE_Q, DISTRIBUTE_Q2


class CourseRepresView(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.RetrieveModelMixin):

    queryset = User.objects.filter(Q(isClasser=True)&USER_Q )
    serializer_class = CourseRepresSerializer
    filter_class = CourseRepreslFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    def destroy(self, request, *args, **kwargs):
        # 冻结 /  恢复 分销权限
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(USER_NOT_EXISTS)
        instance.shareStatus = 2 if instance.shareStatus==1 else 1 # 这里只改变管理员状态为删除状态， 无法再登录后台
        instance.save()
        return Response(CHANGE_SUCCESS)


# 课代表详情 >> 交易记录
class OrderDetailView(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin):
    # 课代表详情里的交易记录  订单是支付状态 分销金额不为空，大于0
    queryset = OrderDetail.objects.filter(DISTRIBUTE_Q).\
        select_related("orderUuid")
    serializer_class = OrderBasicSerializer
    filter_class = OrderBasicFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


# 菜单：【课代表分成交易管理】
class CourseRepresTradeView(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin):
    queryset = OrderDetail.objects.filter(DISTRIBUTE_Q2).\
        select_related("orderUuid")
    serializer_class = OrderBasic2Serializer
    filter_class = OrderBasic2Filter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


# 菜单：【课代表体现交易管理】
class CourseRepresWithdrawView(viewsets.GenericViewSet,
                               mixins.ListModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.RetrieveModelMixin):
    queryset = Withdrawal.objects.all()
    serializer_class = WithdrawalSerializer
    filter_class = WithdrawalFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(WITHDRAWAL_NOT_EXISTS)
        if not instance.withdrawalStatus == 1:
            raise ParamError("当前提现状态无法受理提现！")
        # 校验提现金额 大于1元 小于500元
        if instance.withdrawalMoney < 100:
            raise ParamError("提现金额需大于1元")
        if instance.withdrawalMoney > 50000:
            raise ParamError("提现金额需小于500元")
        if instance.withdrawalType != 2:
            raise ParamError("目前仅支持微信退款")
        if not instance.wxAccount:
            raise ParamError("未获取提现用户的openid")
        if not instance.userUuid.realName:
            raise ParamError("未获取提现用户的真实姓名")

        serializers_data = WithdrawalUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.updateWithdrawal(instance, serializers_data.data, request)
        return Response(PUT_SUCCESS)


