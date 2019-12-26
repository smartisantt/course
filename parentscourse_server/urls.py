"""parentscourse_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from manager import urls as managerUrl
from client import urls as clientUrl
from manager_rabc import urls as managerRabcUrl
from manager_user import urls as managerUserUrl
from manager_course import urls as managerCourse
from manager_order import urls as managerOrderUrl
from manager_coupons import urls as managerCouponsUrl
from manager_distribution import urls as managerDistributionUrl
from manager_comments import urls as managerCommentsUrl
from manager_chatroom import urls as managerChatroomUrl
from manager_auth import urls as managerAuthUrl
from public import urls as publicUrl
from im_app import urls as imUrl

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/manage/', include((managerUrl, 'manager'), namespace='manager')),
    path('api/manage/lessonManage/', include((managerCourse, 'manager_course'), namespace='manager_course')),
    path('api/client/', include((clientUrl, 'client'), namespace='client')),
    path('api/manage/roles/', include((managerRabcUrl, 'manager_rabc'), namespace='manager_rabc')),
    path('api/manage/userManage/', include((managerUserUrl, 'manager_user'), namespace='manager_user')),
    path('api/manage/', include((managerCommentsUrl, 'manager_comments'), namespace='manager_comments')),
    path('api/manage/', include((managerChatroomUrl, 'manager_chatroom'), namespace='manager_chatroom')),
    path('api/manage/orderManage/', include((managerOrderUrl, 'manager_order'), namespace='manager_order')),
    path('api/manage/dividedManagement/', include((managerDistributionUrl, 'manager_distribution'), namespace='manager_distribution')),
    path('api/manage/', include((managerCouponsUrl, 'manager_coupons'), namespace='manager_coupons')),
    path('api/manage/auth/', include((managerAuthUrl, 'manager_auth'), namespace='manager_auth')),
    path('api/public/', include((publicUrl, 'public'), namespace='public')),
    path('api/im/', include((imUrl, 'im_app'), namespace='im_app')),
]
