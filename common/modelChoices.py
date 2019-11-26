#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 用户性别
GENDER_CHOICES = (
    (1, "男"),
    (2, "女"),
    (3, "保密")
)

YUNXIN_GENDER_CHOICES = (
    (0, "保密"),
    (1, "男"),
    (2, "女")
)


COURSE_TYPE_CHOICES = (
    (1, "单次课"),
    (2, "系列课"),
)

COURSESOURCE_TYPE_CHOICES = (
    (1, "视频"),
    (2, "音频")
)

LIVE_COURSE_BANNER_TYPE_CHOICES = (
    (1, "视频"),
    (2, "音频"),
    (3, "PPT"),
    (4, "图片"),
)

# 用户状态
USER_STATUS_CHOICES = (
    (1, "正常"),
    (2, "删除"),
    (3, "禁止登录"),
    (4, "禁止发言")
)

# 后台编辑普通用户的状态
USER_MODIFY_STATUS_CHOICES = (
    (1, "正常"),
    (3, "禁用"),
)

# 用户注册平台来源
USER_REGISTER_CHOICES = (
    (1, "H5"),
    (2, "App"),
    (3, "小程序"),
    (4, "老数据用户"),
    (5, "后台添加用户")
)

# 后台管理员状态
MANAGER_STATUS_CHOICES = (
    (1, "管理员正常"),
    (2, "管理员删除"),
    (3, "管理员禁用"),
    (4, "非管理员"),
)

# 后台编辑管理员用户的状态
MANAGER_MODIFY_STATUS_CHOICES = (
    (1, "正常"),
    (3, "禁用"),
)

# 标签大类型
TAG_CHOICES = (
    (1, "课程"),
    (2, "专家"),
    (3, "看点")
)
TAG_LEVEL_CHOICES = (
    (1, "一级标签"),
    (2, "二级标签"),
    (3, "三级标签"),
)

# 登录方式
LOGIN_TYPE_CHOICES = (
    ("USERPASSWD", "账号密码"),
    ("PHONE", "验证码"),
    ("WECHAT", "微信"),
    ("QQ", "QQ登录"),
    ("ADMINPWD", "后台账号密码"),
    ("ADMINPHONE", "后台验证码"),
)

# 审核状态
CHECK_STATUS_CHOICES = (
    (1, "待审核"),
    (2, "审核通过"),
    (3, "审核未通过"),
    (4, "建议人工复审")
)

# 优惠券使用状态
COUPONS_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 轮播图状态
BANNER_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 轮播图状态
BANNER_MODIFY_CHOICES = (
    (1, "normal"),
    (2, "forbidden")
)

# 大咖直播状态
COURSE_LIVE_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 轮播图状态
JUMP_TYPE_CHOICES = (
    (1, "课程"),
    (2, "外部链接")
    # (3, "活动"),      # 这个版本没有活动，是活动选择外部链接
)

# 用户优惠券使用状态
USER_COUPONS_STATUS_CHOICES = (
    (1, "领取未使用"),
    (2, "领取已使用"),
    (3, "挂单中")
)

COURSE_STYLE_CHOICES = (
    (1, "直播"),
    (2, "音频"),
    (3, "视频")
)

WARE_TYPE_CHOICES = (
    (1, "音频"),
    (2, "视频"),
    (3, "PPT")
)

COURSES_PERMISSION_CHOICES = (
    (1, "免费课"),
    (2, "VIP课"),
    (3, "精品课")
)

COURSES_FORBIDDEN_CHOICES = (
    (1, "启用"),
    (2, "停用"),
    (3, "下架"),
    (4, "删除")
)
COURSE_UPDATE_STATUS = (

    (1, "已完结"),
    (2, "更新中"),
    (3, "未开始")

)

# 角色状态
ROLE_STATUS_CHOICES = (
    (1, "启用"),
    (2, "停用"),
    (3, "删除")
)

# 优惠券类型
COUPONS_TYPE_CHOICES = (
    (1, "单品券"),
    (2, "品类券"),
    (3, "通用券")
)

# 优惠券来源类型
COUPONS_SOURCE_CHOICES = (
    (1, "好呗呗"),
    (2, "店铺")
)

# 课程权限类型
COURSE_RIGHT_TYPE_CHOICES = (
    (1, "赠送"),
    (2, "购买")
)

# 商品类型
GOODS_TYPE_CHOICES = (
    (1, "单次课"),
    (2, "系列课"),
    (3, "会员卡"),
    (4, "虚拟物品"),
    (5, "实物"),
    (6, "专题"),
    (7, "训练营"),
)

# 聊天室角色
CHATS_USER_ROLE = (
    (1, "普通用户"),
    (2, "专家"),
    (3, "主持人"),
    (4, "嘉宾")
)

# 商品类型
GOODS_TYPE = (
    (1, "赠品"),
    (2, "其他")
)

# 商品状态
GOODS_STATUS = (
    (1, "可售"),
    (2, "暂停销售"),
    (3, "下架"),
)

USER_ROLE_CHOICES = (
    (1, "管理员"),
    (2, "巡逻员"),
    (3, "正常用户"),
    (4, "禁言用户"),
    (5, "个人认证"),
    (6, "机构认证"),
)

# 课程说明存储类型
INFO_TYPE_CHOICES = (
    (1, "富文本"),
    (2, "逗号分隔图片")
)

# 返现金额状态
SHARE_MONEY_STATUS_CHOICES = (
    (1, "无分销"),
    (2, "待结算"),
    (3, "已结算"),
    (4, "已取消"),  # 表示这个订单在结算前已被用户退款，所以分成也相应取消
)

# 订单状态  物流状态
ORDER_STATUS_CHOICES = (
    (1, "未发货"),
    (2, "已发货"),
    (3, "已完成"),
    (4, "申请退货中"),
    (5, "已退货")
)

# 支付状态
PAY_STATUS_CHOICES = (
    (1, "未付款"),
    (2, "已付款"),
    (3, "退款中"),
    (4, "已退款"),
    (5, "超时"),
    (6, "用户取消"),
    (7, "管理员取消")
)

# 退款状态
REFUND_MONEY_STATUS_CHOICES = (
    (1, "等待处理"),
    (2, "退款成功"),
    (3, "退款财务不通过"),
    (4, "取消申请退款"),
)

# 退款 通过受理 暂不处理
REFUND_MONEY_CHECK_CHOICES = (
    (2, "退款成功"),
    (3, "退款财务不通过")
)

# 退款 通过受理 暂不处理
WITHDRAWAL_MONEY_CHECK_CHOICES = (
    (2, "提现成功"),
    (3, "提现财务不通过")
)

# 退款路径
REFUND_MONEY_WAY_CHOICES = (
    (1, "账户余额"),
    (2, "支付宝"),
    (3, "微信"),
    (4, "银行卡"),
)

# 个人流水类型
BILL_TYPE_CHOICES = (
    (1, "分成收入"),
    (2, "提现支出")
)

# 首页展示样式
SECTION_SHOW_TYPE = (
    (1, "横排"),
    (2, "竖排")
)

# 首页课程展示状态
SECTION_COURSE_SHOW_STATUS = (
    (1, "展示"),
    (2, "不展示"),
    (3, "删除")
)

# 用户来源类型
USER_SOURCE_TYPE = (
    (1, "数据迁移"),
    (2, "新注册"),
    (3, "数据迁移并登陆过")
)

# 猜你喜欢优先级
MAY_LIKE_TYPE = (
    (1, "已购相关课程"),
    (2, "浏览过的相关课程"),
    (3, "后台配置")
)

# 必读类型
MUSTREAD_TYPE_CHOICES = (
    (1, "单次课"),
    (2, "系列课"),
    (3, "专题课"),
    (4, "训练营"),
    (5, "活动"),
    (6, "实物"),
    (7, "会员")
)
# 猜你喜欢装填类型
MAY_LIKE_STATUS_TYPE = (
    (1, "启用"),
    (2, "禁用"),
    (3, "删除")
)

# 付款方式
PAY_CHOICES = (
    (1, "微信"),
    (2, "支付宝"),
    (3, "其他")
)

# 点赞评论状态
COMMENT_LIKE_CHOICES = (
    (1, "点赞"),
    (2, "取消点赞")
)

# 分销状态
SHARE_STATUS_CHOICES = (
    (1, "启动分销权限"),
    (2, "冻结分销权限")
)

# 提现状态 实际返回前端状态 1：待受理 2：受理成 3:未通过（包含4）
CASH_WITHDRAWAL_STATUS_CHOICES = (
    (1, "待受理"),
    (2, "受理成功"),
    (3, "财务不通过"),
    (4, "转账失败")
)

# 提现方式
CASH_WITHDRAWAL_TYPE_CHOICES = (
    (1, "银行转账"),
    (2, "微信"),
    (3, "支付宝"),
)

HOT_SEARCH_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 轮播图改变状态
HOT_SEARCH_MODIFY_CHOICES = (
    (1, "normal"),
    (2, "forbidden")
)

# 用户提现账户类型
ACCOUNT_TYPE_CHOICES = (
    (1, "银行账号"),
    (2, "微信账号"),
    (3, "支付宝账号")
)

# 用户提现账户状态
CASH_ACCOUNT_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 消息类型
MESSAGE_TYPE_CHOICES = (
    (1, "上课提醒"),
    (2, "其他")
)

# 任务类型
TASK_TYPE_CHOICES = (
    (1, "新手任务"),
    (2, "学习任务"),
    (3, "分享任务"),
    (4, "签到任务"),
    (5, "活动任务"),
)

# 直播课件消息类型
LIVE_SOURCE_MSG_TYPE_CHOICES = (
    (1, "音频"),
    (2, "视频"),
    (3, "图片"),
    (4, "文字")
)

LIVE_MSG_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

LIVE_COURSE_MSGS_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

LIVE_COURSE_STATUS_CHOICES = (
    (1, "normal"),
    (2, "forbidden"),
    (3, "destroy")
)

# 业务类型
BUSINESS_TYPE = (
    (1, "微信提现业务"),
    (2, "微信退款业务"),
)
