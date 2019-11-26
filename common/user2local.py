"""
用户信息对应
==========================================
hbb_user      User
==========================================
phone         tel
uname         userName
email         email
sex           gender       性别 1：男、2：女
location      location     所在省市区
is_audit      is_audit     是否通过审核 1：未通过 2：通过(本系统)---->是否通过审核：0-未通过，1-已通过
is_active     is_active    是否激活 1：激活 2：未激活（本系统）----->是否已激活 1：激活、0：未激活
ctime         createTime   注册时间
identity      identity     身份标识（1：用户，2：组织）
intro         intro        户用简介
id_del        isDelete     是否禁用，0不禁用，1：禁用
uid           hbbId        用户在好呗呗ID

=================================================================
会员卡表
ims_member_price     MemberCard
=================================================================
name               name    会员卡名称
validity_period       duration  会员卡时长
line_through_price    originalPrice  会员卡划线价格
price                 realPrice    会员卡实际价格
discount              discount    会员卡折扣
use_note              use_note     使用说明
ims_member_card_desc(img_url)  cardImgUrl  会员卡图片

====================================================================
用户会员权益记录表
ims_user_member    UserMember
====================================================================
uid              userId      用户id
mc_id            cardId      会员卡id
create_time      createTime  创建时间
begin_time       startTime   会员开始时间
end_time         endTime     会员结束时间

"""
import datetime
import os, django
import time
from hashlib import md5

from pymysql.cursors import DictCursor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()

import pymysql

from common.models import User, UserMember, MemberCard, InviteSet, UserInviteLog, InviteCodes, Goods, TelAuth, \
    WechatAuth

""" mysql 数据库配置 """
# 打开数据库连接 HBB 数据库
DBHOST = 'rm-2ze7srd8bw76fyl52o.mysql.rds.aliyuncs.com'
DBUSER = 'prod_hbb_ts1'
DBPWD = 'Ts@HbbPr0d2018'
DATABASE = 'prod_ts_comm'

db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
# db = pymysql.connect('127.0.0.1', 'root', 'hbb123', 'hbb_db', charset='utf8')
# 使用cursor()方法获取操作游标
cursor = db.cursor(DictCursor)


def string_to_datetime(mystr, rule='%Y-%m-%d %H:%M:%S'):
    """
    将string转为 datetime.datetime
    :param mydate:
    :return:
    """
    if isinstance(mystr, str):
        return datetime.datetime.strptime(mystr, rule)
    else:
        return mystr


def unix_time_to_datetime(unix_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    try:
        _time = datetime.datetime.fromtimestamp(unix_time)
    except ValueError:
        try:
            _time = datetime.datetime.fromtimestamp(unix_time)
        except ValueError:
            _time = unix_time
    return _time


def datetime_to_unix(_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    if isinstance(_time, datetime.date):
        return time.mktime(_time.timetuple()) * 1000
    else:
        return _time


def get_user_info(start):
    """导入用户信息"""
    sql = """
    select 
    A.uid as o_user_id,
    A.uname as nickName,
    A.phone as tel,
    A.email as email,
    A.sex as gender,
    A.location as location,
    A.is_audit as isAudit,
    A.is_active as isActive,
    A.ctime as createTime,
    A.identity as identity,
    A.intro as intro,
    A.password as password,
    A.login_salt as salt,
    B.user_group_id as userRoles
    from
    hbb_user as A 
    left join hbb_user_group_link as B 
    on A.uid = B.uid 
    order by A.uid 
    limit 1000
    offset 
    """ + start
    cursor.execute(sql)
    datas = cursor.fetchall()
    for data in datas:

        if not User.objects.filter(o_user_id=str(data['o_user_id'])).exists() and data['o_user_id']:
            uid = data['o_user_id']
            # 生成用户头像并存储
            md5Str = md5(str(uid).encode('utf-8')).hexdigest()
            # print(md5Str,md5Str[0])
            avatar = "http://sns.hbbclub.com/data/upload/avatar/{0}/{1}/{2}/original_100_100.jpg".format(
                md5Str[0] + md5Str[1], md5Str[2] + md5Str[3], md5Str[4] + md5Str[4])
            data["avatar"] = avatar
            if not data["userRoles"]:
                data["userRoles"] = 3
            sql2 = """
            select 
            type_uid 
            from hbb_login 
            where 
            uid=
            """ + str(uid) + " and " + "type='weixin'"
            cursor.execute(sql2)
            openid_info = cursor.fetchone()
            if openid_info != None:
                data["openId"] = openid_info["type_uid"]
            user = User.objects.create(**data)
            try:
                user.createTime = unix_time_to_datetime(data["createTime"])
                user.save()
            except:
                continue


def get_user_member():
    """会员信息导入"""
    sql3 = """
        select 
        uid,
        create_time,
        begin_time,
        end_time 
        from 
        ims_user_member
        order by uid
        """
    cursor.execute(sql3)
    member_list = cursor.fetchall()
    for member in member_list:
        insert_data1 = {}
        insert_data1["startTime"] = int(datetime_to_unix(member["begin_time"]))
        insert_data1["endTime"] = int(datetime_to_unix(member["end_time"]))
        insert_data1["createTime"] = int(member["create_time"])
        insert_data1["o_user_id"] = str(member["uid"])
        UserMember.objects.create(**insert_data1)


def update_user_member():
    members = UserMember.objects.all()
    for member in members:
        if member.o_user_id:
            user = User.objects.filter(o_user_id=member.o_user_id).first()
            try:
                member.userUuid = user if user else None
                member.save()
            except:
                continue


def get_member_card():
    """
    获取会员卡类型表
    :return:
    """
    sql = """
    select 
    id,
    name,
    validity_period,
    line_through_price,
    price,
    discount,
    use_note 
    from 
    ims_member_card_price 
    """
    cursor.execute(sql)
    cards = cursor.fetchall()
    for card in cards:
        if not MemberCard.objects.filter(o_member_card_price_id=card['id']).exists() and card['id']:
            insert_data = {}
            insert_data["name"] = card["name"]
            insert_data["duration"] = card["validity_period"]
            insert_data["originalPrice"] = int(card["line_through_price"] * 100) if card["line_through_price"] else None
            insert_data["realPrice"] = int(card["price"] * 100)
            insert_data["discount"] = card["discount"]
            insert_data["useNote"] = card["use_note"]
            insert_data["o_member_card_price_id"] = card["id"]
            insert_data[
                "cardImgUrl"] = "http://hbb-dev.oss-cn-beijing.aliyuncs.com/card/desc/j5r7AC8hFP1522739851689.png"
            MemberCard.objects.create(**insert_data)


def get_invite_set():
    """
    兑换码批次表（ims_invite_code）
    :return:
    """
    sql = """
    select 
    id,
    name,
    numbers,
    begin_time,
    end_time,
    used_numbers,
    content_type,
    content_id,
    content_name,
    content_validity_period,
    use_note,
    store_cd,
    use_limit 
    from
    ims_invite_code 
    """
    cursor.execute(sql)
    sets = cursor.fetchall()
    for set in sets:
        if not InviteSet.objects.filter(o_invite_code_id=set['id']).exists() and set['id']:
            insert_data = {}
            insert_data["name"] = set["name"]
            insert_data["numbers"] = set["numbers"]
            insert_data["usedNumbers"] = set["used_numbers"]
            insert_data["startTime"] = int(set["begin_time"]) * 1000
            insert_data["endTime"] = int(set["end_time"]) * 1000
            insert_data["contentType"] = set["content_type"]
            insert_data["o_content_id"] = set["content_id"]
            insert_data["contentName"] = set["content_name"]
            insert_data["contentTime"] = set["content_validity_period"]
            insert_data["useNote"] = set["use_note"]
            insert_data["storeId"] = set["store_cd"]
            insert_data["useLimit"] = set["use_limit"]
            insert_data["o_invite_code_id"] = set["id"]
            InviteSet.objects.create(**insert_data)


def get_invite_codes():
    """
    好呗呗兑换码表（ims_invite_codes）
    :return:
    """
    sql = """
    select 
    id,
    code,
    lot_id,
    no,
    status,
    used_uid,
    used_uname,
    used_time 
    from
    ims_invite_codes 
    order by id 
    """
    cursor.execute(sql)
    for code in cursor.fetchall():
        if not InviteCodes.objects.filter(o_invite_codes_id=code['id']).exists() and code['id']:
            insert_data = {}
            insert_data["code"] = code["code"]
            insert_data["o_lot_id"] = str(code["lot_id"])
            insert_data["no"] = code["no"]
            insert_data["status"] = code["status"]
            usedHbbId = str(code["used_uid"])
            insert_data["o_user_id"] = usedHbbId if code["used_uid"] else None
            user = User.objects.filter(o_user_id=usedHbbId).first()
            insert_data["userUuid"] = user.uuid if user else None
            insert_data["o_user_uname"] = code["used_uname"]
            insert_data["usedTime"] = code["used_time"]
            insert_data["o_invite_codes_id"] = str(code["id"])
            InviteCodes.objects.create(**insert_data)


def update_invite_codes():
    """更新关系"""
    codes = InviteCodes.objects.all()
    for code in codes:
        invite = InviteSet.objects.filter(o_invite_code_id=code.o_lot_id).first()
        try:
            code.inviteSetUuid = invite if invite else None
            code.save()
        except:
            continue


def get_invite_uselog():
    """
    兑换码使用日志(ims_user_member_charge_log)
    :return:
    """
    sql = """
    select 
    id,
    uid,
    name,
    validity_period,
    begin_time,
    end_time,
    get_way,
    order_no,
    invite_lot_id,
    create_time,
    invite_code 
    from 
    ims_user_member_charge_log
    """
    cursor.execute(sql)
    for log in cursor.fetchall():
        if not UserInviteLog.objects.filter(o_user_member_charge_log_id=log['id']).exists() and log['id']:
            insert_data = {}
            uid = str(log["uid"])
            insert_data["o_user_id"] = uid
            user = User.objects.filter(o_user_id=uid).first()
            insert_data["userUuid"] = user
            insert_data["name"] = log["name"]
            insert_data["dayTime"] = log["validity_period"]
            insert_data["startTime"] = datetime_to_unix(log["begin_time"])
            insert_data["endTime"] = datetime_to_unix(log["end_time"])
            insert_data["getWay"] = log["get_way"]
            insert_data["hbbOrderNo"] = log["order_no"]
            invitLotId = log["invite_lot_id"]
            insert_data["o_lot_id"] = invitLotId
            invite = InviteSet.objects.filter(o_invite_code_id=invitLotId).first()
            insert_data["inviteSetUuid"] = invite
            insert_data["inviteCode"] = log["invite_code"]
            insert_data["o_user_member_charge_log_id"] = log["id"]
            insert_data["createTime"] = log["create_time"]
            UserInviteLog.objects.create(**insert_data)


def update_card_to_goods():
    cards = MemberCard.objects.all()
    for c in cards:
        Goods.objects.create(
            name=c.name,
            icon=c.cardImgUrl,
            duration=c.duration,
            originalPrice=c.originalPrice,
            realPrice=c.realPrice,
            discount=c.discount,
            content=c.useNote,
            goodsType=3,
        )


def create_auth():
    for u in User.objects.order_by("userNum").all():
        if u.tel:
            try:
                TelAuth.objects.create(
                    userUuid=u,
                    tel=u.tel,
                    password=u.password,
                    salt=u.salt,
                    passwd=u.passwd,
                    userSource=u.userSource
                )
            except Exception as e:
                print(e)
        if u.openid:
            try:
                WechatAuth.objects.create(
                    userUuid=u,
                    name=u.nickName,
                    sex=u.gender,
                    avatar=u.avatar,
                    openid=u.openid,
                    unionid=u.unionid
                )
            except Exception as e:
                print(e)


if __name__ == "__main__":
    # for i in range(0, 245):
    #     get_user_info(str(i * 1000))  # 用户信息
    # get_user_member()  # 获取会员信息，不能重复调用--------
    # update_user_member()  # 更新关系
    # get_member_card()  # 获取vip类型
    # get_invite_set()  # 获取兑换码批次信息
    # for i in range(12, 149):  # 获取兑换码信息
    #     get_invite_codes(str(i * 1000))
    # update_invite_codes()  # 更新验证码关系
    # get_invite_uselog()  # 获取兑换码使用日志信息
    create_auth()
