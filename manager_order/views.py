from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.models import Orders, OrderDetail, Refund, RefundOperation

# 用户的消费记录视图
from manager_order.filters import OrderDetailFilter, RefundFilter
from manager_order.serializers import OrderDetailSerializer, RefundBasicSerializer, RefundDetailSerializer, \
    RefundPostSerializer, RefundUpdateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


# 订单列表  分销表
from utils.errors import ParamError
from utils.msg import POST_SUCCESS, REFUND_NOT_EXISTS, PUT_SUCCESS


class OrderDetailView(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.RetrieveModelMixin):

    queryset = OrderDetail.objects.all().select_related('orderUuid')
    serializer_class = OrderDetailSerializer
    filter_class = OrderDetailFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    @transaction.atomic
    # 后台管理申请退款， 入口是子订单列表详情点击申请退款-》退款表中新增一条记录，退款订单关联的是父订单的记录
    def create(self, request, *args, **kwargs):
        serializer_data = RefundPostSerializer(data=request.data)
        result = serializer_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializer_data.errors)
        serializer_data.createRefund(serializer_data.validated_data, request)
        return Response(POST_SUCCESS)

    # 取消申请退款
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError("子订单不存")
        # 子订单 退款状态检查  等待处理或者财务不通过的退款
        refund = instance.refundOrderDetailUuid.filter(refundMoneyStatus__in=[1, 3]).first()
        if not refund:
            raise ParamError("没有可以取消申请退款的订单")
        # 处理退款中，或者退款关闭 -》 取消退款
        # 退款记录表
        RefundOperation.objects.create(
            adminUserUuid=request.user,
            refundMoneyStatus=1,
            refundUuid=refund,
            operation="{0}取消退款".format(request.user.nickName),
            remark=""
        )
        refund.refundMoneyStatus = 4
        refund.save()
        return Response({'code': 200, "msg": "取消申请退款成功"})


# 退款
class RefundView(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.RetrieveModelMixin):

    queryset = Refund.objects.all().select_related('orderDetailUuid').\
        select_related("creatorUuid").select_related("receiverUuid")
    serializer_class = RefundBasicSerializer
    filter_class = RefundFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    @action(methods=['get'], detail=True)
    def detailInfo(self, request, pk):
        return Response(RefundDetailSerializer(self.get_object()).data)

    # 财务对于退款 通过还是不通过
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(REFUND_NOT_EXISTS)

        try:
            orderNum = instance.orderDetailUuid.orderUuid.orderNum
            if not orderNum:
                raise ParamError("没有订单编号")
        except Exception as e:
            raise ParamError("没有订单编号")

        try:
            payAmount = instance.orderDetailUuid.orderUuid.payAmount
            if not payAmount:
                raise ParamError("没有订单实际支付金额")
        except Exception as e:
            raise ParamError("没有订单实际支付金额")

        if instance.refundMoney > payAmount:
            raise ParamError("退款金额超出付款金额")

        if not instance.refundMoneyStatus == 1:
            raise ParamError("当前退款状态无法修改！")
        serializers_data = RefundUpdateSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.updateRefund(instance, serializers_data.data, request)
        return Response(PUT_SUCCESS)











