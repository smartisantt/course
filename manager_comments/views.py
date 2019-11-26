import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from client.models import Comments
from manager_comments.filters import CommentsFilter
from manager_comments.serializers import CommentsSerializer
from utils.errors import ParamError
from utils.msg import *


class CommentsView(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = Comments.objects.filter(isDelete=0)
    serializer_class = CommentsSerializer
    filter_class = CommentsFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)

    # def create(self, request, *args, **kwargs):
    #     # 增
    #     serializers_data = CouponsPostSerializer(data=request.data)
    #     result = serializers_data.is_valid(raise_exception=False)
    #     if not result:
    #         raise ParamError(serializers_data.errors)
    #     serializers_data.create_coupons(serializers_data.data, request)
    #     return Response(POST_SUCCESS)
    #
    # # 修改优惠卷
    # def update(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #     except Exception as e:
    #         raise ParamError(COUPONS_NOT_EXISTS)
    #     if instance.receivedNumber:
    #         raise ParamError(UPDATE_COUPONS_ERROR)
    #     serializers_data = CouponsPostSerializer(data=request.data, partial=True)
    #     result = serializers_data.is_valid(raise_exception=False)
    #     if not result:
    #         raise ParamError(serializers_data.errors)
    #     serializers_data.update_coupons(instance, serializers_data.data)
    #     return Response(PUT_SUCCESS)
    #
    #
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            logging.error(str(e))
            raise ParamError(COMMENTS_NOT_EXISTS)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 删
        try:
            instance = self.get_object()
        except Exception as e:
            raise ParamError(COMMENTS_NOT_EXISTS)
        instance.isDelete = True
        instance.save()
        return Response(DEL_SUCCESS)

    # 审核通过
    @action(methods=['put'], detail=True)
    def enable(self, request, pk):
        comment = self.get_object()
        comment.checkStatus = 2
        comment.save()
        return Response(CHANGE_SUCCESS)

    # 审核不通过
    @action(methods=['put'], detail=True)
    def disable(self, request, pk):
        comment = self.get_object()
        comment.checkStatus = 3
        comment.save()
        return Response(CHANGE_SUCCESS)