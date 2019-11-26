import django_filters

from client.models import Comments
from common.models import Coupons, COUPONS_TYPE_CHOICES, Courses, COURSE_TYPE_CHOICES, UserCoupons, Goods


class CouponsFilter(django_filters.FilterSet):
    couponType = django_filters.ChoiceFilter(choices=COUPONS_TYPE_CHOICES)
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Coupons
        fields = "__all__"



class UserCouponsFilter(django_filters.FilterSet):
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")  # searchTime_before   searchTime_after

    class Meta:
        model = UserCoupons
        fields = ("status", "couponsUuid")


class CommentsFilter(django_filters.FilterSet):
    courseName = django_filters.CharFilter(method='filter_by_courseName')     # 课程名称
    nickName = django_filters.CharFilter(method='filter_by_nickName')         # 用户昵称
    searchTime = django_filters.DateTimeFromToRangeFilter("createTime")          # searchTime_before   searchTime_after

    def filter_by_courseName(self, queryset, name, value):
        return queryset.filter(courseUuid__name__icontains=value)

    def filter_by_nickName(self, queryset, name, value):
        return queryset.filter(userUuid__nickName__icontains=value)

    class Meta:
        model = Comments
        fields = ("checkStatus", "interfaceStatus")