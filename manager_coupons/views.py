from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
# Create your views here.

from common.models import Coupons, Courses, UserCoupons, Goods
from manager_coupons.filters import CouponsFilter, UserCouponsFilter
from manager_coupons.serializers import CouponsSerializer, CouponsPostSerializer, \
    UserCouponsSerializer
from utils.errors import ParamError
from utils.msg import POST_SUCCESS, COUPONS_NOT_EXISTS, PUT_SUCCESS, CHANGE_SUCCESS, DEL_SUCCESS, DEL_COUPONS_ERROR, \
    UPDATE_COUPONS_ERROR


class CouponsView(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = Coupons.objects.filter(status=1)
    serializer_class = CouponsSerializer
    filter_class = CouponsFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    def create(self, request, *args, **kwargs):
        # 增
        serializers_data = CouponsPostSerializer(data=request.data)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.create_coupons(serializers_data.data, request)
        return Response(POST_SUCCESS)

    # 修改优惠卷
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COUPONS_NOT_EXISTS)
        if instance.receivedNumber:
            raise ParamError(UPDATE_COUPONS_ERROR)
        serializers_data = CouponsPostSerializer(data=request.data, partial=True)
        result = serializers_data.is_valid(raise_exception=False)
        if not result:
            raise ParamError(serializers_data.errors)
        serializers_data.update_coupons(instance, serializers_data.data)
        return Response(PUT_SUCCESS)


    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COUPONS_NOT_EXISTS)
        # 领取数量为0 才能删除
        if not instance.receivedNumber:
            instance.status = 3
            instance.save()
            return Response(DEL_SUCCESS)
        else:
            raise ParamError(DEL_COUPONS_ERROR)


class UserCouponsView(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = UserCoupons.objects.filter(userUuid__status__in=[1, 3, 4]).all()
    serializer_class = UserCouponsSerializer
    filter_class = UserCouponsFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)


