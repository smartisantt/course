#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from common.models import *
from common.modelChoices import *


class Chats(BaseModel):
    """
    聊天记录表
    """
    expertUuid = models.ForeignKey(Experts, on_delete=models.CASCADE, null=True, related_name='expertChatsUuid',
                                   to_field='uuid')  # 关联专家
    roomUuid = models.ForeignKey(ChatsRoom, on_delete=models.CASCADE, null=True,
                                 related_name='roomChatsUuid',
                                 to_field='uuid')  # 关联聊天室
    # currPPTUuid = models.ForeignKey(CoursePPT, on_delete=models.CASCADE, null=True, related_name='PPTChatUuid',
    #                                 to_field='uuid')  # 关联当前的单张PPT 修改将单张ppt url存储在content
    userRole = models.IntegerField(choices=CHATS_USER_ROLE, default=1)  # 聊天室用户角色 1：用户 2：专家 3：主持人 4：嘉宾
    talkType = models.CharField(max_length=64, null=True)
    # 发言类型 txt 文字 voice 音频 img 图片 ppt_pos PPT  qna 回答提问(上墙) del 删除  video 视频
    content = models.TextField(null=True)  # 发言内容,如果是多媒体，存储地址
    msgSeq = models.IntegerField(null=True)  # 消息序号
    msgStatus = models.IntegerField(null=True)  # 对话状态(1-正常,2-撤回)
    msgTime = models.BigIntegerField(null=True)  # 前端创建消息时间 时间戳 秒
    duration = models.IntegerField(null=True)  # 语音时长，单位秒
    # currPptId = models.IntegerField(null=True)  # 当前

    o_ppt_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键  ppt
    o_subject_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键 ims_chat_subject
    o_topic_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键
    o_user_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键

    class Meta:
        db_table = "tb_chats"


class Discuss(BaseModel):
    """
    直播课讨论录表 -- C端用户说的表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userDissUuid',
                                 to_field='uuid')  # 关联用户
    roomUuid = models.ForeignKey(ChatsRoom, on_delete=models.CASCADE, null=True,
                                 related_name='roomDiscussUuid',
                                 to_field='uuid')  # 关联聊天室
    msgStatus = models.IntegerField(null=True)  # 对话状态(1-正常,2-撤回)
    content = models.TextField(null=True)  # 发言内容,如果是多媒体，存储地址
    msgSeq = models.IntegerField(null=True)  # 消息序号
    msgTime = models.BigIntegerField(null=True)  # 前端创建消息时间 单位毫秒时间戳
    isQuestion = models.BooleanField(default=False, null=True)  # 是否是提问 0 不是提问
    isAnswer = models.BooleanField(default=False, null=True)  # 是否是提问 0 没有回复 1 已回复
    talkType = models.CharField(max_length=64, null=True)  # 发言类型 txt del

    o_discuss_id = models.IntegerField(default=0)  # 对接老数据的关联主键
    o_topic_id = models.IntegerField(default=0)  # 对接老数据的关联主键
    o_user_id = models.IntegerField(default=0)  # 对接老数据的关联主键

    class Meta:
        db_table = "tb_discuss"


class UserReadChats(BaseModel):
    """用户对专家发言已读未读"""
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userReadChatUuid',
                                 to_field='uuid')  # 关联用户
    chatUuid = models.ForeignKey(Chats, on_delete=models.CASCADE, null=True, related_name='chatReadUuid',
                                 to_field='uuid')  # 关联用户

    class Meta:
        db_table = "tb_user_read_chats"


class Behavior(BaseModel):
    """
    用户对于课程行为表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userBehaviorUuid',
                                 to_field='uuid')  # 关联用户
    courseUuid = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True, related_name='behaviorUuid',
                                   to_field='uuid')  # 课程
    behaviorType = models.IntegerField(null=True)  # 行为类型 1：点赞  2：收藏 3：上课浏览记录 4：COURSE_LIVE_SEARCH_Q/分享 5: 购买记录
    remarks = models.CharField(max_length=1024, null=True)  # 标记内容
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = "tb_behavior"


class Comments(BaseModel):
    """
    评论表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userCommentUuid',
                                 to_field='uuid')  # 关联用户
    courseUuid = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True, related_name='commentUuid',
                                   to_field='uuid')  # 课程
    content = models.CharField(max_length=1024, null=True)  # 标记内容
    checkStatus = models.IntegerField(choices=CHECK_STATUS_CHOICES, default=1)  # 人工审核状态
    checkInfo = models.CharField(max_length=255, null=True)  # 审核信息
    interfaceStatus = models.IntegerField(choices=CHECK_STATUS_CHOICES, default=1)  # 接口审核状态
    interfaceInfo = models.CharField(max_length=255, null=True)  # 审核信息
    replayUuid = models.ForeignKey("self", on_delete=models.CASCADE, to_field='uuid', related_name="childrenUuid",
                                   null=True)
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = "tb_comment"


class CommentsLike(BaseModel):
    """记录评论点赞信息"""
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userLikeCommentUuid',
                                 to_field='uuid')  # 关联用户
    commentUuid = models.ForeignKey(Comments, on_delete=models.CASCADE, null=True, related_name='commentLikeUserUuid',
                                    to_field='uuid')  # 关联评论内容
    status = models.IntegerField(choices=COMMENT_LIKE_CHOICES, default=1)  # 点赞状态 1点赞 2取消点赞

    class Meta:
        db_table = "tb_comment_like"


class LoginLog(BaseModel):
    """
    登录日志表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='loginLogUuid',
                                 to_field='uuid')  # 关联用户
    ipAddr = models.CharField(max_length=64, null=True)  # 登录IP
    devNO = models.CharField(max_length=64, null=True)  # 设备编号
    platform = models.CharField(max_length=32)  # 后台管理端 h5
    loginType = models.CharField(max_length=32, choices=LOGIN_TYPE_CHOICES, null=True)  # 登录方式

    class Meta:
        db_table = "tb_login_log"


class ReceivingInfo(BaseModel):
    """
    收货信息
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userReceivingInfoUuid',
                                 to_field='uuid',
                                 null=True, verbose_name="用户")
    area = models.CharField(max_length=64, null=True)  # 地区
    address = models.CharField(max_length=255, verbose_name='收货地址', null=True)  # 详细地址
    isDefault = models.IntegerField(default=False)  # 1 不设置为默认地址， 2设置为默认地址
    contact = models.CharField(max_length=32, null=False)  # 收件人
    tel = models.CharField(max_length=20, null=True)  # 收货人电话号码
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = "tb_receiving_info"


class Banner(BaseModel):
    """
    轮播图
    """
    name = models.CharField(max_length=64, null=True)  # 轮播图名称
    orderNum = models.IntegerField(null=True)  # 显示序号  数字越小越优先显示(优先级)
    icon = models.CharField(max_length=255, null=True)  # 轮播图片
    startTime = models.BigIntegerField(null=True)  # 有效起始时间
    endTime = models.BigIntegerField(null=True)  # 有效结束时间
    type = models.IntegerField(choices=JUMP_TYPE_CHOICES, null=True)  # 跳转类型   活动  课程  外部链接
    target = models.CharField(max_length=255, null=True)  # 跳转目标
    status = models.IntegerField(choices=BANNER_STATUS_CHOICES, default=1)  # 轮播图状态

    class Meta:
        db_table = 'tb_banner'


class UserSearch(BaseModel):
    """
    用户搜索记录
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userSearchUuid',
                                 to_field='uuid')  # 关联用户
    keyword = models.CharField(max_length=512, null=True)  # 搜索关键字
    isDelete = models.BooleanField(default=False)  # 热搜词状态

    class Meta:
        db_table = 'tb_uer_search'


class MayLike(BaseModel):
    """
    猜你喜欢
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userLikeUuid',
                                 to_field='uuid', null=True)  # 关联用户
    courseUuid = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True, related_name='courseLikeUuid',
                                   to_field='uuid')  # 课程
    likeType = models.IntegerField(choices=MAY_LIKE_TYPE, default=1)  # 猜你喜欢来源类型（优先级，用数字排序做一级排序）
    weight = models.IntegerField(null=True)  # 二级排序
    startTime = models.BigIntegerField(null=True)  # 展示开始时间
    endTime = models.BigIntegerField(null=True)  # 展示结束时间
    status = models.IntegerField(choices=MAY_LIKE_STATUS_TYPE, default=1)  # 猜你喜欢状态 1启用 2禁用 3删除

    class Meta:
        db_table = 'tb_uer_maylike'


class FollowExpert(BaseModel):
    """用户关注专家"""
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userFollowUuid',
                                 to_field='uuid', null=True)  # 关联用户
    expertUuid = models.ForeignKey(Experts, on_delete=models.CASCADE, null=True, related_name='expertFollowUuid',
                                   to_field='uuid')  # 课程
    status = models.IntegerField(default=1)  # 1关注 2取消关注

    class Meta:
        db_table = 'tb_follow_expert'


class CashAccount(BaseModel):
    """用户提现账号管理"""
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userCashAccountUuid',
                                 to_field='uuid', null=True)  # 关联用户
    name = models.CharField(max_length=64, null=True)  # 账户名称
    accountType = models.IntegerField(choices=ACCOUNT_TYPE_CHOICES, default=3)  # 提现账户类型 1银行卡 2微信 3支付宝
    accountNO = models.CharField(max_length=64, null=True)  # 账号
    status = models.IntegerField(choices=CASH_ACCOUNT_STATUS_CHOICES, default=1)  # 用户提现账户状态

    class Meta:
        db_table = 'tb_cash_account'
