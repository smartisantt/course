import django_filters
from django_filters.widgets import BooleanWidget

from client.models import Chats
from common.modelChoices import COURSE_TYPE_CHOICES, COURSES_PERMISSION_CHOICES, COURSES_FORBIDDEN_CHOICES, \
    COURSESOURCE_TYPE_CHOICES, COURSE_UPDATE_STATUS, CHATS_DISPLAY_POSE
from common.models import Courses, Chapters, User
from utils.timeTools import timeChange


class CourseFilter(django_filters.FilterSet):
    name = django_filters.CharFilter("name", lookup_expr="icontains")  # 模糊匹配
    # expertName = django_filters.CharFilter("name", lookup_expr="icontains")
    expertName = django_filters.CharFilter(method="filter_by_expertName")
    coursePermission = django_filters.ChoiceFilter("coursePermission", choices=COURSES_PERMISSION_CHOICES)
    courseType = django_filters.ChoiceFilter("courseType", choices=COURSE_TYPE_CHOICES)
    status = django_filters.ChoiceFilter("status", choices=COURSES_FORBIDDEN_CHOICES)
    chapterStyle = django_filters.ChoiceFilter(choices=COURSESOURCE_TYPE_CHOICES, method="filter_by_chapterStyle")
    createTime = django_filters.DateTimeFromToRangeFilter("createTime")
    updateTime = django_filters.DateTimeFromToRangeFilter("updateTime")
    startTime = django_filters.DateTimeFromToRangeFilter("startTime", method="filter_by_startTime")
    updateStatus = django_filters.ChoiceFilter("updateStatus", choices=COURSE_UPDATE_STATUS)
    tagName = django_filters.CharFilter(method="filter_by_tagName")

    def filter_by_expertName(self, queryset, name, value):
        return queryset.filter(expertUuid__name__icontains=value)

    def filter_by_tagName(self, queryset, name, value):
        return queryset.filter(tags__name__icontains=value)

    def filter_by_chapterStyle(self, queryset, name, value):
        return queryset.filter(chapterCourseUuid__chapterStyle__exact=value)

    def filter_by_startTime(self, queryset, name, value):
        startTime_before = 999999999999999
        startTime_after = 1000000000
        if value.start:
            startTime_after = timeChange(value.start, 3)
        if value.stop:
            startTime_before = timeChange(value.stop, 3)
        return queryset.filter(startTime__gte=startTime_after, startTime__lte=startTime_before)

    class Meta:
        model = Courses
        fields = "__all__"


class ChapterFilter(django_filters.FilterSet):
    courseUuid = django_filters.CharFilter("courseUuid", lookup_expr="exact")
    chapterName = django_filters.CharFilter("name", lookup_expr="icontains")
    serialNumber = django_filters.NumberFilter("serialNumber", lookup_expr="exact")
    status = django_filters.ChoiceFilter("status", choices=COURSES_FORBIDDEN_CHOICES)
    createTime = django_filters.DateTimeFromToRangeFilter("createTime")
    startTime = django_filters.DateTimeFromToRangeFilter("startTime", method="filter_by_startTime")

    def filter_by_startTime(self, queryset, name, value):
        startTime_before = 999999999999999
        startTime_after = 1000000000
        if value.start:
            startTime_after = timeChange(value.start, 3)
        if value.stop:
            startTime_before = timeChange(value.stop, 3)
        return queryset.filter(startTime__gte=startTime_after, startTime__lte=startTime_before)

    class Meta:
        model = Chapters
        fields = "__all__"


class DummyUserFilter(django_filters.FilterSet):
    nickName = django_filters.CharFilter("nickName", lookup_expr="exact")

    class Meta:
        model = User
        fields = "__all__"


class ChatsHistoryFilter(django_filters.FilterSet):
    # uuid = django_filters.CharFilter(method='filter_by_uuid')
    displayPos = django_filters.ChoiceFilter(choices=CHATS_DISPLAY_POSE)
    isQuestion = django_filters.BooleanFilter("isQuestion", widget=BooleanWidget())


    class Meta:
        model = Chats
        fields = ("displayPos", "isQuestion")
