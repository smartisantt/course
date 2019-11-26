import django_filters

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

