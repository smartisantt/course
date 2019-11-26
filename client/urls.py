#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path

from rest_framework.routers import DefaultRouter

from client.socketViews import websocketLink
from client.userViews import *
from client.views import *
from client.payViews import *

urlpatterns = [
    path('sendcode/', send_code, name='send_code'),  # 发送验证码
    path('register/', register, name='register'),  # 注册
    path('login/', login, name='login'),  # 登录
    path('logout/', logout, name='logout'),  # 退出登录
    path('changepwd/', change_password, name='change_password'),  # 修改密码
    path('changetel/', change_tel, name='change_tel'),  # 修改手机号
    path('changeinfo/', change_info, name='change_info'),  # 修改个人信息
    path('wechatlogin/', wechat_login, name='wechat_login'),  # 微信登录
    path('bindtel/', bind_tel, name='bind_tel'),  # 微信登录绑定手机号
    path('bindwechat/', bind_wechat, name='bind_wechat'),  # 手机号绑定微信
    path('realauth/', bind_real_info, name='bind_real_info'),  # 绑定手机号和设置交易密码
    path('querytel/', query_tel, name='query_tel'),  # 查询手机号是否已注册

    path('websocketLink/<str:token>/<str:uuid>/', websocketLink, name='websocketLink'),  # 聊天室发送消息

    path('wxpayparams/', WXPayParams.as_view()),  # 公众号端获取微信支付参数
    path('wxpayresult/', WXPayResult.as_view()),  # 公众号端发起微信支付后，微信异步回调结果通知
    path('wxpayquery/', WXPayQuery.as_view()),  # 公众号端发起微信支付后，微信异步回调结果通知

    path('exchange/', ExchangeCodeView.as_view()),  # 兑换码兑换课程
    path('studyHistory/', StudyHistoryView.as_view()),  # 浏览历史
    path('cashRequest/', CashRequest.as_view()),  # 提现申请路由
    path('billList/', BillListView.as_view()),  # 用户流水列表

]

router = DefaultRouter()
router.register('banner', BannerView)  # 轮播图
router.register('tags', TagsView)  # 首页标签
router.register('section', SectionView)  # 首页展示模块
router.register('sectionMore', SectionMoreView)  # 首页模块展示更多
router.register('mayLike', MayLikeView)  # 首页猜你喜欢
router.register('categroy', CategroyView)  # 首页分类筛选
router.register('behavior', BehaviorView)  # 用户行为查询
router.register('courseDetail', CourseView)  # 查看课程详情
router.register('courseComments', CourseCommentsView)  # 查看课程评论
router.register('comment', CommentView)  # 发表评论
router.register('commentLike', CommentLikeView)  # 评论点赞
router.register('courseSource', CourseSourceView)  # 课件路由
router.register('lives', LivesView)  # 首页直播列表
router.register('livesMore', LivesMoreView)  # 更多直播
router.register('course', CourseListView)  # 课程排行列表、免费专区
router.register('userInfo', UserInfoView)  # 用户详细信息
router.register('courseSearch', CoursesSearchView)  # 搜索课程
router.register('searchLike', SearchLikeView)  # 模糊匹配
router.register('hotKeyword', HotSearchView)  # 热搜词
router.register('searchHistory', SearchHistoryView)  # 搜索历史
router.register('searchHistory/clear', SearchHistoryView)  # 清空搜索历史
router.register('defaultSearch', DefaultSearchView)  # 默认搜索词
router.register('coupons', CouponsView)  # 优惠券列表
router.register('userCoupons', UserCouponsView)  # 用户优惠券列表
router.register('expert', ExpertsView)  # 专家级视图
router.register('expertCourses', ExpertCoursesView)  # 专家课程视图
router.register('share', SharesView)  # 分享记录
router.register('memberCard', MemberCardView)  # 会员卡
router.register('feedback', FeedbackView)  # 用户反馈
router.register('room', RoomView)  # 聊天室信息
router.register('chats', ChatsView)  # 聊天室专家发言记录
router.register('discussDel', DiscussDelView)  # 删除聊天记录
router.register('courses/search', CoursesSearchViewSet, base_name='courses_search')  # 课程搜索视图
router.register('cashAccountList', CashAccountListView)  # 提现账户列表---------暂时未使用
router.register('cashAccount', CashAccountView)  # 提现账户管理---------暂时未使用
router.register('promote', PromoteView)  # 推广中心课程列表
router.register('promoteCoupons', PromoteCouponsView)  # 推广中心课程列表
router.register('couponsCourse', CouponsCourseView)  # 优惠券可用课程
router.register('buyCourses', BuyCoursesView)  # 已购课程接口
router.register('courseCoupons', CourseUseCouponsView)  # 课程可用优惠券

urlpatterns += router.urls
