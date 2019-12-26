#!/usr/bin/env python3
# -*- coding: utf-8 -*-
DEL_SUCCESS = {'code': 200, 'msg': '删除成功'}
PUT_SUCCESS = {'code': 200, 'msg': '修改成功'}
POST_SUCCESS = {'code': 200, 'msg': '创建成功'}
CHANGE_SUCCESS = {'code': 200, 'msg': '更改状态成功'}
REMOVE_SUCCESS = {'code': 200, 'msg': '移除成功'}
MAX_WEIGHT_SUCCESS = {'code': 200, 'msg': '置顶成功'}
EXCHANGE_NUMBER_SUCCESS = {'code': 200, 'msg': '顺序更改成功'}
USER_ROLES_SUCCESS = {'code': 200, 'msg': '用户分配角色成功'}

#
ADD_AMDIN_SUCCESS = {'code': 200, 'msg': '添加管理员成功'}

# h5
CLEAR_SUCCESS = {'code': 200, 'msg': '清空成功'}
USER_COUPON_SUCCESS = {'code': 200, 'msg': '优惠券领取成功'}
BEHAVIOR_SUCCESS = {'code': 200, 'msg': '取消成功'}
BEHAVIOR_FAIL = {'code': 400, 'msg': '失败'}
SHARE_SUCCESS = {'code': 200, 'msg': '添加分销记录成功'}
FEEDBACK_SUCCESS = {'code': 200, 'msg': '反馈成功'}
COMMENT_SEND_SUCCESS = {'code': 200, 'msg': '发表成功'}

# 用户模块
USER_NOT_EXISTS = {'code': 400, 'msg': '用户不存在'}
USER_EMAIL_EXISTS = {'code': 400, 'msg': '邮箱重复'}
USER_EMAIL_ERROR = {'code': 400, 'msg': '邮箱格式错误'}
USER_TEL_EXISTS = {'code': 400, 'msg': '电话号码重复'}
USER_TEL_ERROR = {'code': 400, 'msg': '电话号码错误'}
USER_NICKNAME_EXISTS = {'code': 400, 'msg': '用户昵称重复'}

USER_PWD_ERRORS = {'code': 400, 'msg': '两次密码不一致'}

# 角色模块
ROLE_NOT_EXISTS = {'code': 400, 'msg': '角色不存在'}
ROLE_NAME_EXISTS = {'code': 400, 'msg': '角色名重复'}
ROLE_REMARK_EXISTS = {'code': 400, 'msg': '角色备注重复'}

# 权限模块
PERMISSION_NOT_EXISTS = {'code': 400, 'msg': '权限不存在'}
PERMISSION_NAME_EXISTS = {'code': 400, 'msg': '权限名重复'}
PERMISSION_CODE_EXISTS = {'code': 400, 'msg': '权限编码重复'}

# 地区公共模块
API_QUERY_ERROR = {'code': 400, 'msg': '未查询到地区信息'}

# 标签模块

TAG_PARENT_ERROR = {"code": 400, "msg": "父标签有误"}
TAG_NOT_EXISTS = {"code": 400, "msg": "对象不存在"}
TAG_NAME_EXISTS = {"code": 400, "msg": "标签名已存在"}
TAG_NUM_EXISTS = {"code": 400, "msg": "标签顺序已存在"}

# 轮播图模块
BANNER_QUERY_ERROR = {'code': 400, 'msg': '未查询到轮播图信息'}
BANNER_NAME_EXISTS = {'code': 400, 'msg': '轮播图名字已存在'}

# 首页标签模块
TAG_QUERY_ERROR = {'code': 400, 'msg': '未查询到标签信息'}
# 登录验证模块
REDIS_NOT_CONNECT_ERROR = {'code': 400, 'msg': "服务器连接redis失败"}

# 栏目模块
SECTION_EXISTS_ERROR = {"code": 400, "msg": "栏目已存在"}
SECTION_NOT_EXISTS = {"code": 400, "msg": "栏目不存在"}
COURSESOURCE_NOT_EXISTS = {"code": 400, "msg": "课件不存在"}
SECTION_COURSE_ERROR = {"code": 400, "msg": "课程选择有误"}

# 轮播图
BANNER_NOT_EXISTS = {"code": 400, "msg": "轮播图不存在"}

# 评论
COMMENTS_NOT_EXISTS = {"code": 400, "msg": "评论不存在"}

# 不存在
REFUND_NOT_EXISTS = {"code": 400, "msg": "退款不存在"}

# 搜索关键词
HOT_SEARCH_NOT_EXISTS = {"code": 400, "msg": "关键词不存在"}
HOT_SEARCH_KEYWORD_ERROR = {"code": 400, "msg": "关键词已存在"}

# 大咖直播
COURSE_LIVE_NOT_EXISTS = {"code": 400, "msg": "大咖直播不存在"}

# 猜你喜欢
MAY_LIKE_NOT_EXISTS = {"code": 400, "msg": "猜你喜欢不存在"}

# 专家模块
EXPERT_EXISTS_ERROR = {"code": 400, "msg": "专家已存在"}
EXPERT_NOT_EXISTS = {"code": 400, "msg": "专家不存在"}

# 课程须知
MUSTREAD_EXISTS_ERROR = {"code": 400, "msg": "须知已存在"}
MUSTREAD_NOT_EXISTS = {"code": 400, "msg": "须知不存在"}

# 课件库模块
COURSESOURCE_EXISTS_ERROR = {"code": 400, "msg": "课件名已存在"}
DURATION_VALUE_ERROR = {"code": 400, "msg": "课程时长有误"}
PPT_VALUE_ERROR = {"code": 400, "msg": "PPT上传的格式有误"}
PAGES_VALUE_ERROR = {"code": 400, "msg": "PPT页数有误"}

# H5-课程查询
COURSE_NOT_EXISTS = {"code": 400, "msg": "课程不存在"}
SECTION_NOT_EXISTS = {"code": 400, "msg": "栏目不存在"}
SECTION_COURSE_EXISTS_ERROR = {"code": 400, "msg": "栏目下有课程，禁止更改状态"}
EXPERT_NOT_EXISTS = {"code": 400, "msg": "专家不存在"}
UUID_ERROR = {"code": 400, "msg": "请选择要查看的课程"}
BEHAVIOR_ERROR = {"code": 400, "msg": "行为记录失败"}

# 订单相关
ORDER_NOT_EXISTS = {'code': 400, 'msg': '订单不存在'}

# 固定栏目展示
SHOW_NUM_ERROR = {'code': 400, 'msg': '展示数量有误'}

TIMESTAMP_TO_DATETIME_ERROR = {'code': 400, 'msg': '时间戳转时间格式错误!'}
DATETIME_TO_TIMESTAMP_ERROR = {'code': 400, 'msg': '时间格式转时间戳错误!'}
TIME_RANGE_ERROR = {'code': 400, 'msg': '开始时间大于结束时间'}
ENDTIME_RANGE_ERROR = {'code': 400, 'msg': '结束时间早于现在时间'}

# 优惠卷
COUPONS_NOT_EXISTS = {'code': 400, 'msg': '优惠卷不存在'}
DEL_COUPONS_ERROR = {'code': 400, 'msg': '优惠卷已有用户领取，暂无法删除'}
UPDATE_COUPONS_ERROR = {'code': 400, 'msg': '优惠卷已有用户领取，暂无法修改'}

#  课程管理
CHAPTER_STYLE_NULL_ERROR = {'code': 400, 'msg': '课程形式必填'}
CHAPTER_STYLE_ERROR = {'code': 400, 'msg': '课程形式有误'}
COURSE_PRICE_ERROR = {'code': 400, 'msg': '课程价格有误'}
START_MC_ERROR = {'code': 400, 'msg': '开始时间或专家必填'}
START_TIME_ERROR = {'code': 400, 'msg': '开始时间有误'}
START_TIME_FORBIDDEN = {'code': 400, 'msg': '当前直播状态禁止修改'}
REWARDS_PERCENT_ERROR = {'code': 400, 'msg': '分销比例有误'}
COURSE_SOURCE_TYPE_ERROR = {'code': 400, 'msg': '课件类型有误'}
COURSE_SOURCE_ERROR = {'code': 400, 'msg': '课件必填'}
PRE_CHAPTER_ERROR = {'code': 400, 'msg': '预计章节数有误'}
CHAPTER_NOT_EXISTS = {'code': 400, 'msg': '章节不存在'}
FORBIDDEN_CHANGE_STATUS = {'code': 400, 'msg': '该课程禁止修改状态'}
NOT_CHANGE_STATUS_ERROR = {'code': 400, 'msg': '课程状态未改变'}
MAX_WEIGHT_ERROR = {'code': 400, 'msg': '权重值已最大'}
CHAT_ROOM_NOT_EXISTS = {'code': 400, 'msg': '直播间不存在'}
EXCHANGE_OBJ_ERROR = {'code': 400, 'msg': '更改对象有误'}

# h5-提现账户管理
ACCOUNT_NOT_EXISTS = {'code': 400, 'msg': '订单不存在'}
ACCOUNT_CREATE_SUCCESS = {'code': 200, 'msg': '添加成功'}

# h5-评论点赞
COMMENT_LIKE_NOT_ESISTS = {'code': 400, 'msg': "取消点赞失败"}
COMMENT_LIKE_CREATE_SUCCESS = {'code': 200, 'msg': '点赞成功'}
COMMENT_LIKE_CANCEL_SUCCESS = {'code': 200, 'msg': '取消成功'}


# 直播素材
LIVE_COURSE_BANNER_EXISTS = {'code': 400, 'msg': "直播素材已存在"}
LIVE_COURSE_NOT_EXISTS = {'code': 400, 'msg': "直播课件不存在"}
LIVE_COURSE_NAME_EXISTS = {'code': 400, 'msg': "直播课件名已存在"}
LIVE_COURSE_MSG_NOT_EXISTS = {"code": 400, "msg": "直播消息不存在"}

# 提现
WITHDRAWAL_NOT_EXISTS = {"code": 400, "msg": "提现不存在"}

# 直播课
LIVE_COURSE_START_SUCCESS = {"code": 200, "msg": "开始直播课成功"}
LIVE_COURSE_END_SUCCESS = {"code": 200, "msg": "结束直播课成功"}

# 对接我们封装的环信接口
IM_ERROR = {"code": 400, "msg": "IM通讯出错"}
IM_NOT_FOUND_ERROR = {"code": 400, "msg": "IM通讯群或者指定的用户不存在"}

MSG_NOT_EXISTS = {"code": 400, "msg": "该消息不存在"}

