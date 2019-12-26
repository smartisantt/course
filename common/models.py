#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import uuid
from django.utils import timezone

from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.
from django.db import models

from common.modelChoices import *


class UUIDTools(object):
    """
    生成uuid
    """

    @staticmethod
    def uuid4_hex():
        return uuid.uuid4().hex


class BaseModel(models.Model):
    uuid = models.CharField(primary_key=True, max_length=64, unique=True, default=UUIDTools.uuid4_hex)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", null=True)
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间", null=True)

    class Meta:
        abstract = True


class Tags(BaseModel):
    """
    标签表
    """
    name = models.CharField(max_length=64, verbose_name="标签名", null=True)  # 标签名
    parentUuid = models.ForeignKey('self', on_delete=models.CASCADE, to_field="uuid", verbose_name="父标签",
                                   null=True, related_name="children")  # 父标签
    weight = models.IntegerField(verbose_name='排序编号', null=True)  # 排列顺序
    tagType = models.IntegerField(choices=TAG_CHOICES, default=1)  # 标签类型
    level = models.IntegerField(choices=TAG_LEVEL_CHOICES, null=True)  # 标签级别
    enable = models.BooleanField(default=1)  # 是否在前端展示

    class Meta:
        db_table = "tb_tags"

    def __str__(self):
        return self.name


class HotSearch(BaseModel):
    """
    热搜表
    """
    keyword = models.CharField(max_length=128, verbose_name="热搜词", null=True)
    weight = models.IntegerField(default=0, verbose_name="权重值", null=True)
    searchNum = models.IntegerField(default=0, null=True)  # 搜索次数
    icon = models.BooleanField(default=False, null=True)  # 是否有特效
    status = models.IntegerField(choices=HOT_SEARCH_STATUS_CHOICES, default=1)
    isDefault = models.BooleanField(default=False, null=True)  # 是否是默认词，存在搜索框，默认为0不是
    searchType = models.BooleanField(default=False, null=True)  # 热搜类型，默认为0用户真实搜索 1 为后台管理人员添加的

    class Meta:
        db_table = "tb_hot_search"

    def __str__(self):
        return self.keyword


class Courses(BaseModel):
    """
    课程表
    """
    courseNum = models.IntegerField(auto_created=True, unique=True, null=True)  # 自增课程编号
    expertUuid = models.ForeignKey("Experts", on_delete=models.CASCADE, to_field="uuid",
                                   related_name="expertCourseUuid",
                                   verbose_name="专家", null=True)  # 新系统逻辑 课程关联专家
    courseType = models.IntegerField(choices=COURSE_TYPE_CHOICES, verbose_name="课程类型", default=1)  # 课程类型 1为单次课，2为系列课
    name = models.CharField(max_length=64, null=True, verbose_name="课程名")  # 课程名
    subhead = models.CharField(max_length=200, verbose_name="副标题", null=True)  # 副标题
    briefIntro = models.CharField(max_length=512, null=True)  # 介绍
    preChapter = models.IntegerField(verbose_name="预计章节数量", default=0, null=True)  # 章节数量
    # courseStyle = models.IntegerField(choices=COURSE_STYLE_CHOICES, verbose_name="上课方式",
    #                                   null=True)  # 上课方式，1为音频，2为视频，3直播课   这个应该在章节表
    duration = models.IntegerField(verbose_name="课程时长", default=0)  # 课程时长，默认30min ,单位秒
    startTime = models.BigIntegerField(verbose_name="开始时间", null=True)  # 开始时间，时间戳存储
    endTime = models.BigIntegerField(verbose_name="结束时间", null=True)  # 结束时间，时间戳存储
    adAddr = models.CharField(max_length=1024, verbose_name="广告地址", default=None, null=True)  # 广告
    adPosition = models.IntegerField(default=0, null=True)  # 广告播放位置
    courseBanner = models.TextField(verbose_name="课程封面", null=True)  # 课程封面 存多个地址，用，分割
    courseThumbnail = models.TextField(verbose_name="缩略图", null=True)  # 缩略图，存多个地址，用，分割
    shareUrl = models.CharField(max_length=1024, verbose_name="分享地址", null=True)  # 分享地址
    shareImg = models.CharField(max_length=1024, verbose_name="分享图", null=True)  # 分享图
    infoType = models.IntegerField(choices=INFO_TYPE_CHOICES, default=1)  # 课程说明存储类型 1富文本 2 逗号分隔图片
    info = models.TextField(verbose_name="课程说明", null=True)  # 课程说明  富文本
    tags = models.ManyToManyField(Tags, related_name="courseTags")  # 课程标签
    coursePermission = models.IntegerField(choices=COURSES_PERMISSION_CHOICES, verbose_name="课程权限",
                                           null=True)  # 课程权限 1为免费，2为vip，3为精品课
    updateStatus = models.IntegerField(choices=COURSE_UPDATE_STATUS, null=True, default=3)
    # 课程更新状态1：已完结 2：更新中,3未开始 4 直播结束 5 直播中  6 直播未开始
    gifts = models.ManyToManyField("Goods", related_name="giftCourse")
    keywords = models.CharField(max_length=512, verbose_name="关键词", null=True)  # 关键词(逗号分隔)
    vPopularity = models.IntegerField(verbose_name="虚拟人气", default=0)  # 虚拟人气
    realPopularity = models.IntegerField(verbose_name="实际人气", default=0)  # 实际人气
    relatedCourse = models.ManyToManyField("self", related_name="courseRelate")
    mustRead = models.TextField(null=True)  # 购买须知，单独抽象出来一张表
    status = models.IntegerField(choices=COURSES_FORBIDDEN_CHOICES, default=1,
                                 verbose_name="状态")  # 状态，1为启用，2为停用，3为下架，4为删除
    introduction = models.CharField(max_length=512, null=True)  # 课程导语
    weight = models.IntegerField(default=0, null=True)  # 权重值 默认为0
    o_room_id = models.IntegerField(null=True)  # 对接老数据的关联主键 课程(对应room表)
    o_room_type = models.IntegerField(null=True)  # o_room_id 来自两张表， 1 代表 ims_chat_room（音频视频） 2 代表ims_rb_room（直播）

    # o_topic_id = models.IntegerField(default=0)  # 对接老数据的关联主键  课件

    class Meta:
        db_table = "tb_courses"

    def __str__(self):
        return self.name


class MustRead(BaseModel):
    """
    购买须知
    """
    mustReadNum = models.IntegerField(auto_created=True, unique=True, null=True)
    name = models.CharField(max_length=128, default="课程须知模板")  # 课程须知模板名
    content = models.TextField(default="如果你已经阅读此须知，则代表已同意好呗呗相关协议")  # 课程须知模板
    mustReadType = models.IntegerField(choices=MUSTREAD_TYPE_CHOICES, null=True)  # 课程类型
    enable = models.BooleanField(default=True, null=True)  # 启用状态

    class Meta:
        db_table = "tb_must_read"

    def __str__(self):
        return self.name


class Section(BaseModel):
    """
     栏目表
    """
    name = models.CharField(max_length=64, verbose_name='课程板块名', null=True)  # 课程板块名字
    intro = models.CharField(max_length=512, null=True, blank=True)  # 板块介绍
    sectionType = models.IntegerField(default=1)  # 板块类型 1课程板块
    enable = models.BooleanField(default=True)  # 禁用状态，默认不禁用
    showType = models.IntegerField(choices=SECTION_SHOW_TYPE, default=1)  # 展示方式 1：列表布局 2：卡片布局
    showNum = models.IntegerField(default=2, null=True)  # 默认展示条数
    weight = models.IntegerField(default=0)  # 权重值，用于排序
    courses = models.ManyToManyField("Courses", through="SectionCourse", related_name="courseSections")
    isShow = models.BooleanField(default=False, null=True)  # 是否首页展示，默认不展示

    class Meta:
        db_table = "tb_section"

    def __str__(self):
        return self.name


class SectionCourse(BaseModel):
    """
    栏目课程中间表
    """
    courseUuid = models.ForeignKey('Courses', on_delete=models.CASCADE, related_name='courseSectionUuid',
                                   to_field='uuid', null=True)  # 课程uuid
    sectionUuid = models.ForeignKey('Section', on_delete=models.CASCADE, related_name='sectionCourseUuid',
                                    to_field='uuid', null=True)  # 板块uuid
    weight = models.IntegerField(default=0, null=True)  # 权重值，用于排序
    status = models.IntegerField(choices=SECTION_COURSE_SHOW_STATUS, default=2)  # 1:首页展示 2：首页不展示 3:删除

    class Meta:
        db_table = "tb_section_courses"


class Chapters(BaseModel):
    """
    章节表
    """
    courseUuid = models.ForeignKey('Courses', on_delete=models.CASCADE, related_name='chapterCourseUuid',
                                   to_field='uuid', verbose_name="课程id", null=True)  # 课程id
    courseSourceUuid = models.ForeignKey("CourseSource", to_field="uuid", on_delete=models.CASCADE, null=True,
                                         related_name="courseSourceChapter")  # 课件
    expertUuid = models.ForeignKey("Experts", on_delete=models.CASCADE, to_field="uuid",
                                   related_name="courseExpertUuid",
                                   verbose_name="专家", null=True)
    tryInfoUuid = models.ForeignKey("CourseSource", to_field="uuid", on_delete=models.CASCADE, null=True,
                                    related_name="courseTrySourceChapter")  # 试听课件
    roomUuid = models.ForeignKey("ChatsRoom", to_field="uuid", on_delete=models.CASCADE, null=True,
                                 related_name="roomChapterUuid")  # 关联聊天室
    name = models.CharField(max_length=255, null=True)  # 章节名
    serialNumber = models.IntegerField(verbose_name="章节序号", null=True, default=1)  # 章节序号
    chapterStyle = models.IntegerField(choices=COURSE_STYLE_CHOICES, null=True)  # 上课方式 1:直播 2:音频 3:视频
    duration = models.IntegerField(null=True)  # 课程时长
    startTime = models.BigIntegerField(null=True)  # 开始时间，时间戳，11位 毫秒为单位
    endTime = models.BigIntegerField(null=True)  # 开始时间，时间戳，11位 毫秒为单位
    ad = models.CharField(max_length=1024, verbose_name="广告地址", null=True)  # 广告
    adPosition = models.IntegerField(default=0, null=True)  # 广告播放位置
    chapterBanner = models.CharField(max_length=1024, verbose_name="课程封面", null=True)  # 存多个地址，用，分割
    info = models.TextField(verbose_name="章节说明", null=True)  # 课程说明
    keywords = models.CharField(max_length=512, verbose_name="关键词", null=True)  # 关键词
    status = models.IntegerField(choices=COURSES_FORBIDDEN_CHOICES, default=1, null=True)
    updateStatus = models.IntegerField(choices=COURSE_UPDATE_STATUS, null=True, default=3)
    # 课程更新状态1：已完结 2：更新中,3未开始 4 直播结束 5 直播中  6 直播未开始
    isTry = models.IntegerField(default=0, null=True)  # 1免费，0收费
    o_room_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键 课程
    o_topic_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键 章节
    o_compere_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键 主持人
    o_expert_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键 专家

    class Meta:
        db_table = "tb_chapters"

    def __str__(self):
        return self.name


class ChatsRoom(BaseModel):
    """聊天室表"""
    name = models.CharField(max_length=255, null=True)  # 聊天室名称
    huanxingId = models.CharField(max_length=64, null=True)  # 环信聊天室的ID
    tmId = models.CharField(max_length=64, null=True)  # 腾讯聊天室的ID
    studyNum = models.IntegerField(null=True)  # 学习次数
    startTime = models.BigIntegerField(null=True)  # 开始时间
    actualStartTime = models.BigIntegerField(null=True)  # 实际开始时间
    liveStatus = models.IntegerField(choices=LIVE_STATUS_CHOICES, default=1)  # 直播状态
    endTime = models.BigIntegerField(null=True)  # 结束时间
    banner = models.CharField(max_length=512, null=True)  # 聊天室列表图
    liveCourseUuid = models.ForeignKey('LiveCourse', on_delete=models.CASCADE, related_name='liveCourseChatsRoom',
                                       to_field='uuid', null=True)  # 直播课件uuid
    mcUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="roomMcUuid",
                               null=True)  # 主持人
    inviterUuid = models.ManyToManyField("User", verbose_name="嘉宾",
                                         related_name="roomInviterUuid")  # 嘉宾
    ownerUuid = models.ForeignKey("User", verbose_name="环信建群的人", on_delete=models.CASCADE, null=True,
                                  related_name="roomOwnerUuid")  # 环信建群的人
    expertUuid = models.ForeignKey("Experts", on_delete=models.CASCADE, to_field="uuid",
                                   related_name="roomExpertUuid",
                                   verbose_name="专家", null=True)

    class Meta:
        db_table = "tb_chats_room"


class CourseSource(BaseModel):
    """
    课件库
    """
    name = models.CharField(max_length=255, null=True)  # 课件名字
    sourceUrl = models.CharField(max_length=1024, null=True)  # 课件地址,
    sourceType = models.IntegerField(null=True, choices=COURSESOURCE_TYPE_CHOICES)
    # 课件类型，1代表视频，2代表音频
    fileSize = models.IntegerField(verbose_name="文件大小", null=True)  # 课件大小，单位kb
    expertUuid = models.ForeignKey("Experts", related_name="expertCourseSourse", to_field="uuid",
                                   on_delete=models.CASCADE, null=True)  # 课件专家
    duration = models.IntegerField(null=True)  # 课件时长， 针对音频视频
    enable = models.BooleanField(default=True, null=True)  # 是否被禁用，0为禁用，1为启用
    pages = models.IntegerField(null=True)  # PPT页数
    o_topic_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键  课件
    o_media_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键  音频 视频

    class Meta:
        db_table = "tb_course_source"

    def __str__(self):
        return self.name


class CoursePPT(BaseModel):
    """
    PPT表
    """
    liveCourseBanner = models.ForeignKey("LiveCourseBanner", to_field="uuid", on_delete=models.CASCADE,
                                         related_name="courseSourcePpt", null=True)  # 关联的课件
    imgUrl = models.CharField(max_length=1024, null=True)  # 图片地址
    sortNum = models.IntegerField(null=True)  # 图片顺序
    enable = models.BooleanField(default=True, null=True)  # 默认为1可以使用
    o_topic_id = models.IntegerField(default=0)  # 对接老数据的关联主键  课件-- 关联我们的课件库
    o_ppt_id = models.IntegerField(default=0)  # 对接老数据的关联主键  ppt->coursesource->chapter

    class Meta:
        db_table = "tb_course_ppt"


class Experts(BaseModel):
    """
    专家表
    """
    userUuid = models.OneToOneField("User", on_delete=models.CASCADE, related_name='expertInfoUuid', null=True)  # 关联用户
    name = models.CharField(max_length=32, verbose_name="专家名", null=True)  # 专家名
    avatar = models.CharField(max_length=1024, verbose_name="专家头像", null=True)  # 专家头像
    tel = models.CharField(max_length=32, verbose_name="专家手机号", null=True)  # 专家手机号
    hospital = models.CharField(max_length=512, null=True)  # 专家所在医院， 组织
    department = models.CharField(max_length=128, null=True)  # 专家所在科室， 部门
    jobTitle = models.CharField(max_length=128, null=True)  # 专家职称       头衔
    tags = models.ManyToManyField(Tags, related_name="tagsExperts")  # 专家标签
    specialty = models.CharField(max_length=1024, null=True)  # 专家特长
    isStar = models.BooleanField(default=False, null=True)  # 明星专家，默认为0不是明星专家
    intro = models.CharField(max_length=1024, null=True)  # 专家介绍
    careerInfo = models.CharField(max_length=1024, null=True)  # 专家介绍
    enable = models.BooleanField(default=True)  # 禁用状态，默认不禁用
    o_expert_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键
    o_user_id = models.IntegerField(null=True)  # 对接老数据的关联主键
    isRegisterHuanxin = models.BooleanField(default=False, null=True)  # 该用户是否注册环信账号 用户名：用户的uuid 密码：用户的uuid+hxpwd

    class Meta:
        db_table = "tb_experts"

    def __str__(self):
        return self.name


class Mc(BaseModel):
    """
    主持人表
    """
    userUuid = models.OneToOneField("User", on_delete=models.CASCADE, related_name='mcInfoUuid', null=True)
    name = models.CharField(max_length=32, verbose_name="专家名", null=True)  # 主持名
    organization = models.CharField(max_length=64, null=True)  # 主持组织
    department = models.CharField(max_length=64, null=True)  # 主持人部门
    avatar = models.CharField(max_length=1024, verbose_name="专家头像", null=True)  # 专家头像
    specialty = models.CharField(max_length=1024, null=True)  # 主持人特长
    o_compere_id = models.IntegerField(default=0)  # 对接老数据的关联主键
    o_user_id = models.IntegerField(default=0)  # 对接老数据的关联主键 用户的id
    isRegisterHuanxin = models.BooleanField(default=False, null=True)  # 该用户是否注册环信账号 用户名：用户的uuid 密码：用户的uuid+hxpwd

    class Meta:
        db_table = "tb_mc"

    def __str__(self):
        return self.name


class Shares(BaseModel):
    """
    COURSE_LIVE_SEARCH_Q表  记录用户分享连接的信息
    """
    courseUuid = models.ForeignKey("Courses", to_field="uuid", on_delete=models.CASCADE, verbose_name="关联课程",
                                   null=True)  # 课程号
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", verbose_name="分享人",
                                 related_name="shareUserUuid", null=True)
    shareUrl = models.CharField(max_length=1024, verbose_name="COURSE_LIVE_SEARCH_Q链接",
                                null=True)  # COURSE_LIVE_SEARCH_Q链接
    enable = models.BooleanField(default=False, verbose_name="是否禁用")  # 是否禁用，默认0不禁用
    realPrice = models.BigIntegerField(verbose_name="课程价格", null=True)  # 课程价格 单位分
    rewardPercent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)  # 提成比列
    shareType = models.IntegerField(default=0)  # 分享类型,预留
    shareImg = models.CharField(max_length=1024, null=True)  # 分型图片地址

    class Meta:
        db_table = "tb_shares"


class Goods(BaseModel):
    """
    商品表
    """
    goodsId = models.IntegerField(auto_created=True, null=True,
                                  unique=True)  # 商品编号，编号规则：商品类型首字母开头+9位数字编码，如课程：C100000001
    name = models.CharField(max_length=512, null=True)  # 商品名
    icon = models.CharField(max_length=1024, null=True)  # 商品图片
    content = models.CharField(max_length=512, null=True)  # 商品的uuid
    duration = models.IntegerField(null=True)  # 会员卡时长
    discount = models.DecimalField(default=1.0, decimal_places=2, max_digits=3, null=True)  # 折扣比例 默认为1
    originalPrice = models.BigIntegerField(verbose_name="划线价", null=True)  # 划线价 单位是分
    realPrice = models.BigIntegerField(verbose_name="真实价", null=True)  # 真实价格 单位是分
    goodsType = models.IntegerField(choices=GOODS_TYPE_CHOICES, default=1, null=True)  # 商品类型
    isGift = models.BooleanField(null=True, default=0)  # 是否是赠品，默认为0不是
    inventory = models.IntegerField(default=1000)  # 库存数量
    parentUuid = models.ForeignKey("self", related_name="childrenUuid", on_delete=models.CASCADE, null=True)  # 父级商品
    rewardStatus = models.BooleanField(default=0, verbose_name="是否分销", null=True)  # 是否分销，默认不分销
    rewardPercent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                      verbose_name="分销百分比", null=True, default=0)  # 分销比例，使用django
    isCoupon = models.BooleanField(default=True, null=True)  # 是否能用全站优惠券，默认为1，能用
    status = models.IntegerField(choices=COURSES_FORBIDDEN_CHOICES, default=1, null=True)
    o_product_id = models.IntegerField(null=True)  # 原商品id 原来的room_ids

    class Meta:
        db_table = "tb_goods"

    def __str__(self):
        return self.name


class Orders(BaseModel):
    """
    父订单表(一个订单可以包含多个商品信息)
    """
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="orderUserUuid",
                                 verbose_name="购买人", null=True)  # 关联用户
    shareUserUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid",
                                      related_name="orderShareUserUuid", null=True)
    orderNum = models.CharField(max_length=128, verbose_name="订单号", null=True, unique=True)  # 订单号，规则：年月日时分秒+6位随机数字
    buyerName = models.CharField(max_length=255, null=True)  # 购买人名字
    buyerTel = models.CharField(max_length=20, null=True)  # 购买人电话
    buyerAddr = models.CharField(max_length=512, null=True)  # 购买人地址
    channel = models.CharField(max_length=1024, null=True)  # 购买渠道(某某门店...)
    channelNum = models.CharField(max_length=64, null=True)  # 购买渠道编码(门店编码)
    orderOrgPrice = models.BigIntegerField(null=True)  # 原价
    orderPrice = models.BigIntegerField(null=True)  # 应付金额  (原价 - 优惠卷)
    payAmount = models.BigIntegerField(null=True)  # 实付金额   (应付金额-使用积分)
    payType = models.IntegerField(choices=PAY_CHOICES, default=1, null=True)  # 付款方式
    endTime = models.IntegerField(null=True)  # 订单完成时间
    orderStatus = models.IntegerField(choices=ORDER_STATUS_CHOICES, default=1, null=True)  # 订单状态
    payStatus = models.IntegerField(choices=PAY_STATUS_CHOICES, default=1, null=True)  # 支付状态
    couponUuid = models.CharField(max_length=255, null=True)  # 使用优惠券uuid， 多个优惠卷
    shareMoney = models.BigIntegerField(verbose_name="返现金额", null=True)  # 父订单返现金额=所有子订单返现金额
    shareMoneyStatus = models.IntegerField(choices=SHARE_MONEY_STATUS_CHOICES, default=1)  # 返现金额状态
    billNum = models.CharField(max_length=64, null=True)  # 支付流水单号
    o_user_id = models.IntegerField(null=True)  # 原用户id
    wxPayStatus = models.CharField(max_length=64, default="NOTPAY")

    class Meta:
        db_table = "tb_orders"

    def __str__(self):
        return self.orderNum


class OrderDetail(BaseModel):
    """
    订单详情表    订单（1）  ----   订单详情（多）
    """
    goodsUuid = models.ForeignKey("Goods", on_delete=models.CASCADE, to_field="uuid", related_name="goodsFlashUuid",
                                  verbose_name="商品id", null=True)  # 商品id
    orderUuid = models.ForeignKey("Orders", on_delete=models.CASCADE, to_field="uuid", null=True,
                                  related_name="orderDetailUuid")  # 快照关联的订单
    detailNum = models.CharField(max_length=64, null=True)  # 第几个子订单   主订单_1  主订单_2
    o_product_id = models.BigIntegerField(null=True)  # 原商品id(原room表id)
    goodsName = models.CharField(max_length=512, verbose_name="商品名", null=True)  # 商品名
    goodsCount = models.IntegerField(null=True)  # 商品数量
    goodsType = models.IntegerField(choices=GOODS_TYPE_CHOICES, default=1, null=True)  # 商品类型
    isGift = models.BooleanField(null=True, default=0)  # 是否是赠品，默认为0不是
    shareMoney = models.BigIntegerField(verbose_name="返现金额", null=True)  # 子订单的 里的单个商品的返现金额
    goodsImg = models.CharField(max_length=1024, verbose_name="商品照片", null=True)  # 商品照片
    originalPrice = models.BigIntegerField(verbose_name="划线价", null=True)  # 划线单价 单位是分
    goodsPrice = models.BigIntegerField(verbose_name="商品当前真实价格", null=True)  # 商品当前价格（真实价格单价）
    expressPrice = models.BigIntegerField(verbose_name="快递费用", null=True)  # 商品快递费用，单位分
    totalPrice = models.BigIntegerField(verbose_name="商品当前总价", null=True)  # 商品当前总价 goodsPrice*goodsCount
    couponPrice = models.BigIntegerField(verbose_name="优惠卷优惠金额", null=True)  # 单位分
    payPrice = models.BigIntegerField(verbose_name="商品应付总价", null=True)  # 实际支付金额

    # 商品应付总价  = totalPrice+ expressPrice - couponPrice

    class Meta:
        db_table = "tb_order_detail"


class OrderExpress(BaseModel):
    """
    物流信息表
    """
    orderUuid = models.ForeignKey("OrderDetail", on_delete=models.CASCADE, to_field="uuid",
                                  related_name="orderGoodsExpress",
                                  null=True)
    deliveryNum = models.CharField(max_length=255, null=True)  # 运单号
    expressDate = models.IntegerField(null=True)  # 填写快递日期
    lastQueryDate = models.DateTimeField(null=True)  # 上次查询时间
    com = models.CharField(max_length=64, null=True)  # 快递公司名字
    expressDetail = models.TextField(null=True)
    # 物流的详细信息
    #  为空这是无效快递或者没有填写快递
    #  快递单当前状态，包括0在途，1揽收，2疑难，3签收，4退签，5派件，6退回  7未录入单号 8暂无物流信息 9个状态
    expressState = models.IntegerField(default=7)  # 当前快递状态

    class Meta:
        db_table = 'tb_order_express'


class Payment(BaseModel):
    """
    支付详情表
    """
    orderNum = models.OneToOneField("Orders", on_delete=models.CASCADE, to_field="orderNum",
                                    related_name="orderNumPayment", null=True)  # 订单号
    payWay = models.CharField(max_length=32, null=True)  # 支付方式代码 “WXPAY” 微信支付
    payWayName = models.CharField(max_length=32, null=True)  # 支付方式名称  微信支付 苹果内购
    partner = models.CharField(max_length=64, null=True)  # 微信支付相关秘钥？
    payTransNo = models.CharField(max_length=64, null=True)  # 交易流水号
    payStatus = models.BooleanField(default=0)  # 是否付款
    payAmount = models.BigIntegerField(null=True)  # 支付金额
    payTime = models.BigIntegerField(null=True)  # 支付时间 毫秒时间戳
    payType = models.IntegerField(null=True)  # 支付类型 1现金 4积分
    cardNo = models.CharField(max_length=64, null=True)  # 优惠卡号
    usedPoints = models.IntegerField(null=True)  # 积分
    expPrice = models.BigIntegerField(null=True)  # 现金金额

    class Meta:
        db_table = "tb_payment"


# 用户权限管理
class Permissions(BaseModel):
    """
    权限表
    """
    icon = models.CharField(max_length=255, null=True, verbose_name="菜单icon")
    method = models.CharField(max_length=15, verbose_name="请求方式", null=True)
    url = models.CharField(max_length=1024, verbose_name="请求的url", null=True)
    menuName = models.CharField(max_length=128, verbose_name="菜单名/权限", blank=True, null=True)
    remark = models.CharField(max_length=255, null=True, verbose_name="备注信息")
    sortNum = models.IntegerField(verbose_name='排序编号', null=True)  # 排列顺序
    enable = models.BooleanField(default=True)  # 是否禁用，默认1不禁用
    parentUuid = models.ForeignKey('self', on_delete=models.CASCADE, to_field='uuid',
                                   null=True, default=None, related_name="subMenu")

    class Meta:
        db_table = 'tb_permissions'

    def __str__(self):
        return self.menuName


class Role(BaseModel):
    """
     角色表
    """
    name = models.CharField(max_length=128, verbose_name="角色名称", blank=True, null=True)
    remark = models.CharField(max_length=512, null=True)  # 角色说明
    status = models.IntegerField(choices=ROLE_STATUS_CHOICES, default=1)
    permissions = models.ManyToManyField(Permissions, related_name='role')

    class Meta:
        db_table = 'tb_role'

    def __str__(self):
        return self.name


class WechatAuth(BaseModel):
    """微信认证用户"""
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE,
                                 related_name='userWechatUuid', to_field='uuid', null=True)  # 关联用户
    name = models.CharField(max_length=64, null=True)  # 微信用户名
    sex = models.IntegerField(choices=GENDER_CHOICES, default=3)  # 微信用户性别
    avatar = models.CharField(max_length=512, blank=True, null=True)  # 用户头像
    province = models.CharField(max_length=255, null=True)  # 用户所在省份
    city = models.CharField(max_length=255, null=True)  # 用户所在城市
    openid = models.CharField(max_length=64, null=True)  # 微信登录openid
    unionid = models.CharField(max_length=64, null=True)  # 微信登录unionid
    status = models.IntegerField(choices=USER_STATUS_CHOICES, default=1)  # 前端用户状态

    class Meta:
        db_table = "tb_wechat_auth"


class TelAuth(BaseModel):
    """手机号认证用户"""
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE,
                                 related_name='userTelUuid', to_field='uuid', null=True)  # 关联用户
    tel = models.CharField(max_length=32, blank=True, null=True)
    password = models.CharField(max_length=255, null=True)  # 密码 老数据存的密码
    salt = models.CharField(max_length=32, null=True)  # 加密使用
    passwd = models.CharField(max_length=255, null=True)  # 新密码
    status = models.IntegerField(choices=USER_STATUS_CHOICES, default=1)  # 前端用户状态
    userSource = models.IntegerField(choices=USER_SOURCE_TYPE, default=1)  # 用户来源 1数据迁移 2新注册 3迁移并登录过 4后台添加

    class Meta:
        db_table = "tb_tel_auth"


class User(BaseModel):
    """
     用户表
    """
    userNum = models.IntegerField(auto_created=True, unique=True, null=True)  # 自增非主键用户号
    nickName = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    realName = models.CharField(max_length=32, blank=True, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, default=3)
    tel = models.CharField(max_length=32, blank=True, null=True)
    birthday = models.DateField(verbose_name="出生日期", blank=True, null=True)
    point = models.IntegerField(verbose_name="用户积分", default=0)
    avatar = models.CharField(verbose_name="用户头像", max_length=512, blank=True, null=True)
    lastLoginTime = models.BigIntegerField(null=True)  # 上次登录时间
    status = models.IntegerField(choices=USER_STATUS_CHOICES, default=1)  # 前端用户状态
    managerStatus = models.IntegerField(choices=MANAGER_STATUS_CHOICES, default=4)  # 后端管理员状态, 默认不能登录后台
    remark = models.CharField(max_length=1024, null=True)  # 用户备注
    inviter = models.CharField(max_length=32, null=True)  # 邀请人
    roles = models.ManyToManyField(Role, related_name='user')  # 角色
    isClasser = models.BooleanField(default=False)  # 是否是课代表
    shareStatus = models.IntegerField(choices=SHARE_STATUS_CHOICES, default=1)  # 是否有分销权限
    isShopper = models.BooleanField(default=False)  # 是否是店主
    o_user_id = models.CharField(max_length=64, null=True)  # 好呗呗用户id
    location = models.CharField(max_length=64, null=True)  # 所在省市区
    intro = models.CharField(max_length=255, null=True)  # 户用简介
    userRoles = models.IntegerField(choices=USER_ROLE_CHOICES, default=3)  # 用户角色
    passwd = models.CharField(max_length=255, null=True)  # 新密码
    openid = models.CharField(max_length=64, null=True)  # 微信登录openid
    unionid = models.CharField(max_length=64, null=True)  # 微信登录unionid
    income = models.BigIntegerField(default=0)  # 累计收益
    banlance = models.BigIntegerField(default=0)  # 收益余额
    registerPlatform = models.IntegerField(choices=USER_REGISTER_CHOICES, null=True, default=4)  # 用户注册平台
    idCard = models.CharField(max_length=255, null=True)  # 身份证号
    tradePwd = models.CharField(max_length=255, null=True)  # 交易密码
    isRegisterHuanxin = models.BooleanField(default=False, null=True)  # 该用户是否注册环信账号 用户名：用户的uuid 密码：用户的uuid+hxpwd
    circleImg = models.CharField(max_length=1024, null=True)  # 圆角头像地址
    isMajia = models.BooleanField(default=False)  # 是否是马甲用户

    class Meta:
        db_table = 'tb_user'

    # def is_authenticated(self):
    #     return True

    def __str__(self):
        return self.nickName


class Coupons(BaseModel):
    """
    优惠券
    """
    name = models.CharField(max_length=64, null=True)  # 优惠券名称
    startTime = models.BigIntegerField(null=True)  # 优惠券有效开始时间
    endTime = models.BigIntegerField(null=True)  # 优惠券有效结束时间
    couponType = models.IntegerField(choices=COUPONS_TYPE_CHOICES, null=True)
    source = models.IntegerField(choices=COUPONS_SOURCE_CHOICES, default=1)  # 优惠券来源
    totalNumber = models.IntegerField(null=True)  # 优惠券发放数量
    usedNumber = models.IntegerField(null=True)  # 使用优惠券数量（领用数量在此不计）
    receivedNumber = models.IntegerField(null=True)  # 领用优惠券数量（使用数量在此不计）
    accountMoney = models.IntegerField(null=True)  # 优惠券满减要求
    money = models.IntegerField(null=True)  # 优惠金额
    remarks = models.CharField(max_length=255, null=True)  # 备注
    creator = models.CharField(max_length=64, null=True)  # 存储创建者的uuid
    status = models.IntegerField(choices=COUPONS_STATUS_CHOICES, default=1)  # 优惠券状态
    isPromotion = models.BooleanField(default=False, null=True)  # 促销商品 + 优惠卷 叠加使用
    # courseUuid = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True,
    #                                related_name="courseCouponsUuid")              # 课程uuid  单品卷管理的课程
    goodsUuid = models.ForeignKey(Goods, on_delete=models.CASCADE, null=True,
                                  related_name="goodsCouponsUuid")  # 课程uuid  商品的优惠卷

    # singleCourse = models.BooleanField(default=False, null=True)  # 品类卷  单次课
    # seriesCourse = models.BooleanField(default=False, null=True)  # 品类卷  系列课
    scope = models.CharField(max_length=1024, null=True)  # 使用逗号分割的 字符串

    class Meta:
        db_table = "tb_coupons"

    def __str__(self):
        return self.name


class UserCoupons(BaseModel):
    """
    用户领取优惠券记录
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='userCouponsUuid', to_field='uuid', null=True)  # 关联用户
    couponsUuid = models.ForeignKey(Coupons, on_delete=models.CASCADE,
                                    related_name='couponsUserUuid', to_field='uuid')  # 关联优惠券
    orderUuid = models.ForeignKey(Orders, null=True, on_delete=models.CASCADE,
                                  to_field="uuid", related_name='couponsOrderUuid')  # 关联的订单
    status = models.IntegerField(choices=USER_COUPONS_STATUS_CHOICES, default=1)  # 用户优惠券状态

    class Meta:
        db_table = "tb_user_coupons"


class Bill(BaseModel):
    """
    交易流水表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, to_field="uuid", related_name="userBillUuid",
                                 null=True)  # 用户
    billType = models.IntegerField(choices=BILL_TYPE_CHOICES, default=2)  # 流水类型
    remarks = models.CharField(max_length=512, null=True)  # 流水备注
    money = models.BigIntegerField(verbose_name="收益支出数值")  # 金额(单位分)

    class Meta:
        db_table = "tb_bill"


class Wallet(BaseModel):
    """
    用户钱包表
    """
    userUuid = models.OneToOneField("User", on_delete=models.CASCADE, to_field="uuid", related_name="userWallet",
                                    null=True)
    income = models.BigIntegerField(null=True)  # 累计收益
    banlance = models.BigIntegerField(null=True)  # 余额
    cash = models.BigIntegerField(null=True)  # 已提现金额

    class Meta:
        db_table = "tb_wallet"


class MemberCard(BaseModel):
    """
    会员卡类型表(member_card_price)
    """
    name = models.CharField(max_length=64, null=True)  # 会员卡名字
    duration = models.IntegerField(null=True)  # 会员时长
    originalPrice = models.BigIntegerField(verbose_name="划线价", null=True)  # 划线价 单位是分
    realPrice = models.BigIntegerField(verbose_name="真实价", null=True)  # 真实价格 单位是分
    discount = models.DecimalField(default=1.0, decimal_places=2, max_digits=3, null=True)  # 折扣比例 默认为1
    useNote = models.CharField(max_length=255, null=True)  # 使用说明
    cardImgUrl = models.CharField(max_length=255, null=True)  # 会员卡图片
    o_member_card_price_id = models.CharField(max_length=64, null=True)  # 好呗呗表id

    class Meta:
        db_table = "tb_member_card"


class UserMember(BaseModel):
    """
    VIP表(ims_user_member)
    """
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="userMemberInfo",
                                 null=True)  # 关联用户
    startTime = models.BigIntegerField(null=True)  # 会员开始时间
    endTime = models.BigIntegerField(null=True)  # 会员结束时间
    o_user_id = models.CharField(max_length=64, null=True)  # 好呗呗表id
    remarks = models.CharField(max_length=64, null=True)  # 来源

    class Meta:
        db_table = "tb_user_member"


class InviteCodes(BaseModel):
    """
    好呗呗兑换码表（ims_invite_codes）
    """
    code = models.CharField(max_length=64, null=True)  # 兑换码
    o_lot_id = models.BigIntegerField(null=True)  # 邀请批次id(对应批次表id)
    inviteSetUuid = models.ForeignKey("InviteSet", on_delete=models.CASCADE, to_field="uuid",
                                      related_name="setInviteCodes",
                                      null=True)  # 本平台对应uuid
    no = models.BigIntegerField(null=True)  # 序号
    status = models.IntegerField(null=True)  # 邀请卡状态 1正常 2已使用
    o_user_id = models.CharField(max_length=64, null=True)  # 使用者hbbid
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="userInviteCode",
                                 null=True)  # 使用者uuid
    o_user_uname = models.CharField(max_length=64, null=True)  # 使用者用户名
    usedTime = models.BigIntegerField(null=True)  # 使用时间
    o_invite_codes_id = models.CharField(max_length=64, null=True)  # 好呗呗表id

    class Meta:
        db_table = "tb_invite_code"


class InviteSet(BaseModel):
    """
    兑换码批次表（ims_invite_code）
    """
    name = models.CharField(max_length=255, null=True)  # 兑换批次名称
    numbers = models.IntegerField(null=True)  # 兑换码数量
    usedNumbers = models.IntegerField(null=True)  # 已使用数量
    startTime = models.BigIntegerField(null=True)  # 开始时间
    endTime = models.BigIntegerField(null=True)  # 结束时间
    contentType = models.IntegerField(null=True)  # 兑换类型 1：课程 2：专栏 3：会员卡
    o_content_id = models.BigIntegerField(null=True)  # 兑换对象id
    contentName = models.CharField(max_length=64, null=True)  # 兑换对象名称
    contentTime = models.IntegerField(null=True)  # 兑换对象有效期（会员卡时有效）
    useNote = models.CharField(max_length=1024, null=True)  # 使用说明
    storeId = models.CharField(max_length=64, null=True)  # 商店id
    useLimit = models.IntegerField(null=True)  # 单人使用次数限制
    o_invite_code_id = models.CharField(max_length=64, null=True)  # 好呗呗表id

    class Meta:
        db_table = "tb_invite_set"


class UserInviteLog(BaseModel):
    """
    兑换码使用日志(ims_user_member_charge_log)
    """
    o_user_id = models.BigIntegerField(null=True)  # 好呗呗uid
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="userMemberLogInfo",
                                 null=True)  # 关联用户,本平台uuid
    name = models.CharField(max_length=64, null=True)  # 使用会员卡名称
    dayTime = models.IntegerField(null=True)  # 有效期，单位天
    startTime = models.BigIntegerField(null=True)  # 开始时间
    endTime = models.BigIntegerField(null=True)  # 结束时间
    getWay = models.IntegerField(null=True)  # 获取方式1：购买 2：兑换
    hbbOrderNo = models.CharField(max_length=64, null=True)  # 好呗呗交易订单号
    o_lot_id = models.BigIntegerField(null=True)  # 邀请批次Id
    inviteSetUuid = models.ForeignKey("InviteSet", on_delete=models.CASCADE, to_field="uuid",
                                      related_name="setInviteUseCodes",
                                      null=True)  # 本平台对应批次表uuid
    inviteCode = models.CharField(max_length=32, null=True)  # 兑换邀请码
    o_user_member_charge_log_id = models.CharField(max_length=64, null=True)  # 好呗呗表id

    class Meta:
        db_table = "tb_invite_uselog"


class Withdrawal(BaseModel):
    """
    提现记录表
    """
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid", related_name="userWithdrawalUuid",
                                 null=True)  # 关联用户
    withdrawalMoney = models.IntegerField(null=True)  # 申请提现金额
    arrivalAccountTime = models.DateTimeField(null=True)  # 实际到帐时间
    preArrivalAccountTime = models.DateTimeField(null=True)  # 预计到帐时间  写死： 0 - 2 个工作日
    withdrawalStatus = models.IntegerField(choices=CASH_WITHDRAWAL_STATUS_CHOICES, null=True, default=1)  # 提现状态
    withdrawalType = models.IntegerField(choices=CASH_WITHDRAWAL_TYPE_CHOICES, null=True)  # 提现方式   暂时仅支持微信 2
    wxAccount = models.CharField(max_length=256, null=True)  # 微信账号，存微信的openId
    serviceCharge = models.IntegerField(null=True)  # 转账手续费
    billNum = models.CharField(max_length=512, null=True)  # 交易流水 微信提现成功存储 付款单号payment_no
    remarks = models.CharField(max_length=512, null=True)  # 未通过原因

    class Meta:
        db_table = "tb_withdrawal"


# 大咖直播
class CourseLive(BaseModel):
    weight = models.IntegerField(default=0, verbose_name="权重值", null=True)
    icon = models.CharField(max_length=255, null=True)  # 图片
    startTime = models.BigIntegerField(null=True)  # 有效起始时间
    endTime = models.BigIntegerField(null=True)  # 有效结束时间
    status = models.IntegerField(choices=COURSE_LIVE_STATUS_CHOICES, default=1)
    courseUuid = models.ForeignKey('Courses', on_delete=models.CASCADE, related_name='courseLiveUuid',
                                   to_field='uuid', null=True)  # 课程uuid

    class Meta:
        db_table = 'tb_course_live'


# 退款管理
class Refund(BaseModel):
    refundNum = models.CharField(max_length=255, null=False)  # 退款编号
    # orderUuid = models.ForeignKey(Orders, null=True, on_delete=models.CASCADE,
    #                               to_field="uuid", related_name='refundOrderUuid')  # 关联的 父订单表
    orderDetailUuid = models.ForeignKey(OrderDetail, null=True, on_delete=models.CASCADE,
                                        to_field="uuid", related_name='refundOrderDetailUuid')  # 关联的 子订单表
    refundMoney = models.IntegerField(null=True)  # 申请退款的金额
    refundReason = models.CharField(max_length=255, null=True)  # 退款原因
    refundMoneyStatus = models.IntegerField(choices=REFUND_MONEY_STATUS_CHOICES, default=1)  # 退款状态
    refundMoneyWay = models.IntegerField(choices=REFUND_MONEY_WAY_CHOICES, default=1)  # 退款返回路径 , 暂时只支持微信
    creatorUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid",
                                    related_name="creatorUserUuid", null=True)  # 发起人
    receiverUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid",
                                     related_name="receiverUserUuid", null=True)  # 受理人

    class Meta:
        db_table = 'tb_refund'


class RefundOperation(BaseModel):
    """后台人员操作退款记录表"""
    adminUserUuid = models.ForeignKey("User", on_delete=models.CASCADE, to_field="uuid",
                                      related_name="creatorOperationUuid", null=True)  # 操作人
    refundMoneyStatus = models.IntegerField(choices=REFUND_MONEY_STATUS_CHOICES, default=1)  # 退款状态
    refundUuid = models.ForeignKey("Refund", on_delete=models.CASCADE, to_field="uuid",
                                   related_name="refundOperationUuid", null=True)  # 发起人
    operation = models.CharField(max_length=1024, null=True)  # 记录： 谁 做了 什么
    remark = models.CharField(max_length=1024, null=True)  # 备注的内容

    class Meta:
        db_table = "tb_refund_operation_record"


class Feedback(BaseModel):
    """
    用户反馈表
    """
    type = models.IntegerField(null=True)  # 反馈问题类型 1产品建议 2功能异常 3其他问题
    content = models.CharField(max_length=1024, null=True)
    icon = models.CharField(max_length=1024, null=True)
    tel = models.CharField(max_length=20, null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userFeedbackUuid', to_field='uuid')
    status = models.IntegerField(default=0)  # 处理状态 0未处理 1已处理
    replyInfo = models.CharField(max_length=1024, null=True)  # 回复信息
    isRead = models.BooleanField(default=False)  # 用户是否已读

    class Meta:
        db_table = 'tb_feedback'


class Message(BaseModel):
    """
    消息表
    """
    type = models.IntegerField(choices=MESSAGE_TYPE_CHOICES, default=1)  # 消息类型 1上课提醒
    title = models.CharField(max_length=255, null=True)  # 消息标题
    content = models.CharField(max_length=1024, null=True)  # 消息内容
    target = models.CharField(max_length=1024, null=True)  # 跳转目标
    publishState = models.IntegerField(default=0)  # 0未推送 1 极光发布成功 2 极光推送失败  3 修改成功 4 修改失败 5 删除成功 6 删除失败 7 增加成功 8 增加失败
    scheduleId = models.CharField(max_length=256, null=True)  # 定时 推送唯一标识符
    isDelete = models.BooleanField(default=False)  # 是否删除
    isRead = models.BooleanField(default=False)  # 是否已读

    class Meta:
        db_table = "tb_message"


class Tasks(BaseModel):
    # 任务表
    name = models.CharField(max_length=255, null=True)  # 任务名称
    icon = models.CharField(max_length=1024, null=True)  # 任务图片
    taskType = models.IntegerField(choices=TASK_TYPE_CHOICES, default=1)  # 任务类型
    totalNum = models.IntegerField(default=0)  # 完成此任务的目标数
    point = models.IntegerField(null=True)  # 任务积分
    enable = models.BooleanField(default=False)  # 禁用状态
    weight = models.IntegerField(default=0)  # 排列顺序
    displayPos = models.CharField(max_length=256, null=True)  # 显示位置  逗号分隔 1 H5 2 app

    class Meta:
        db_table = "tb_tasks"


class UserTask(BaseModel):
    """用户任务记录表"""
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userTaskUuid',
                                 to_field='uuid')  # 关联用户

    taskUuid = models.ForeignKey(Tasks, on_delete=models.CASCADE, null=True, related_name='taskUuid',
                                 to_field='uuid')  # 关联任务
    point = models.IntegerField(default=0)
    subUuid = models.CharField(max_length=64, null=True)  # 积分减少的关联事件的uuid
    remark = models.CharField(max_length=1024, null=True)  # 用户增加积分减少积分备注

    class Meta:
        db_table = "tb_user_task"


class LiveCourseBanner(BaseModel):
    name = models.CharField(max_length=255, null=True)  # banner素材名字
    sourceUrl = models.CharField(max_length=1024, null=True)  # banner素材地址,
    sourceType = models.IntegerField(null=True, choices=LIVE_COURSE_BANNER_TYPE_CHOICES)
    fileSize = models.IntegerField(null=True)  # 课件大小
    duration = models.IntegerField(null=True)  # 课件时长， 针对音频视频
    enable = models.BooleanField(default=True, null=True)  # 是否被禁用，0为禁用，1为启用
    pages = models.IntegerField(null=True)  # PPT页数
    o_topic_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键  课件
    o_media_id = models.IntegerField(default=0, null=True)  # 对接老数据的关联主键  音频 视频

    class Meta:
        db_table = "tb_live_course_banner"


class LiveCourseMsg(BaseModel):
    # 直播课发送课件集合表(多)
    liveCourseUuid = models.ForeignKey("LiveCourse", on_delete=models.CASCADE, null=True,
                                       related_name='liveCourseMsgUuid', to_field='uuid')  # 消息集合
    name = models.CharField(max_length=256, null=True)  # 单条消息内容名称
    sourceUrl = models.CharField(max_length=1024, null=True)  # 课件地址
    sourceType = models.IntegerField(choices=LIVE_SOURCE_MSG_TYPE_CHOICES, null=True)  # 课件类型
    fileSize = models.IntegerField(null=True)  # 课件大小，单位kb
    sortNum = models.IntegerField(default=0)  # 排列顺序 越小越靠前面
    enable = models.BooleanField(default=True)  # 默认1  启用
    duration = models.IntegerField(null=True, default=0)  # 课程时长单位秒

    class Meta:
        db_table = "tb_live_course_msg"


class LiveCourse(BaseModel):
    # 包含直播素材 和 打包好的课件
    name = models.CharField(max_length=256, null=True)
    enable = models.BooleanField(default=True)  # 默认1  启用
    liveCourseBannerUuid = models.ForeignKey(LiveCourseBanner, on_delete=models.CASCADE, null=True,
                                             related_name='liveCourseBannerUuid', to_field='uuid')  # 包含直播素材

    class Meta:
        db_table = "tb_live_course"


class WxEnterprisePaymentToWallet(BaseModel):
    # 微信企业付款到零钱
    mch_appid = models.CharField(max_length=256, null=True)
    mchid = models.CharField(max_length=32, null=True)
    device_info = models.CharField(max_length=32, null=True)  # 设备号，这里存操作人的uuid
    partner_trade_no = models.CharField(max_length=32,
                                        null=True, unique=True)  # 商户订单号 只能是字母或者数字，不能包含有其他字符
    # 存放提现 或者 退款的 uuid
    openid = models.CharField(max_length=32, null=True)  # 商户appid下，某用户的openid
    re_user_name = models.CharField(max_length=64, null=True)  # 收款用户真实姓名。
    desc = models.CharField(max_length=256, null=True)  # 企业付款备注，必填。注意：备注中的敏感词会被转成字符*
    spbill_create_ip = models.CharField(max_length=256, null=True)  # IP地址
    amount = models.IntegerField(null=True)  # 企业付款金额，单位为分
    payment_no = models.CharField(max_length=256, null=True)  # 企业付款成功，返回的微信付款单号
    remark = models.CharField(max_length=256, null=True)  # 企业付款成功，返回的微信付款单号
    payment_time = models.DateTimeField(null=True)  # 企业付款成功时间

    class Meta:
        db_table = "tb_enterprise_payment_to_wallet"


class YunxinChatroom(BaseModel):
    creator = models.CharField(max_length=64, null=True)  # 聊天室属主的账号accid
    roomid = models.CharField(max_length=64, null=True)
    name = models.CharField(max_length=128, null=True)  # 聊天室名称，长度限制128个字符
    broadcasturl = models.CharField(max_length=128, null=True)  # 直播地址，长度限制1024个字符
    announcement = models.CharField(max_length=1024, null=True)  # 公告，长度限制4096个字符
    # 聊天室是否处于全体禁言状态，全体禁言时仅管理员和创建者可以发言
    muted = models.BooleanField(max_length=1024, null=True)
    # 队列管理权限：0:所有人都有权限变更队列，1:只有主播管理员才能操作变更。默认0
    queuelevel = models.IntegerField(default=0, null=True)

    class Meta:
        db_table = "tb_yunxin_chatroom"


class YunxinAuth(BaseModel):
    """网易云信用户"""
    userUuid = models.ForeignKey("User", on_delete=models.CASCADE,
                                 related_name='userYunxinUuid', to_field='uuid', null=True)  # 关联用户
    accid = models.CharField(max_length=32, null=False, unique=True)  # 网易云通信ID，最大长度32字符，必须保证一个
    name = models.CharField(max_length=64, null=True)  # 微信用户名
    gender = models.IntegerField(choices=YUNXIN_GENDER_CHOICES, default=0)  # 微信用户性别
    icon = models.CharField(max_length=512, blank=True, null=True)  # 用户头像

    class Meta:
        db_table = "tb_yunxin_auth"


class PayLog(BaseModel):
    """支付日志表"""

    userUuid = models.ForeignKey("User", on_delete=models.CASCADE,
                                 related_name='paylogUserUuid', to_field='uuid', null=True)  # 关联用户
    appid = models.CharField(null=True, max_length=64)
    mch_id = models.CharField(null=True, max_length=64)
    nonce_str = models.CharField(null=True, max_length=64)
    sign_type = models.CharField(null=True, max_length=64)
    body = models.CharField(null=True, max_length=512)
    out_trade_no = models.CharField(null=True, max_length=64)
    fee_type = models.CharField(null=True, max_length=64)
    total_fee = models.IntegerField(null=True)
    spbill_create_ip = models.CharField(null=True, max_length=64)
    goods_tag = models.CharField(null=True, max_length=64)
    notify_url = models.CharField(null=True, max_length=255)
    trade_type = models.CharField(null=True, max_length=64)
    product_id = models.CharField(null=True, max_length=64)
    openid = models.CharField(null=True, max_length=255)
    device_info = models.CharField(null=True, max_length=64)
    sign = models.CharField(null=True, max_length=512)

    class Meta:
        db_table = "tb_pay_log"
