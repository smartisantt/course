import datetime
import logging
import os, django
import time
from hashlib import md5

from pymysql.cursors import DictCursor

from client.clientCommon import datetime_to_unix

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()

import pymysql

from common.models import User, UserMember, MemberCard, InviteSet, UserInviteLog, InviteCodes, Goods, TelAuth, \
    WechatAuth

""" mysql 数据库配置 """
DBHOST = 'rm-2ze7srd8bw76fyl52o.mysql.rds.aliyuncs.com'
DBUSER = 'prod_hbb_ts1'
DBPWD = 'Ts@HbbPr0d2018'
DATABASE = 'prod_ts_comm'

db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
cursor = db.cursor(DictCursor)


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


def get_user_sql(startTime, endTime):
    sql = """
    select 
    A.uid as o_user_id,
    A.uname as nickName,
    A.phone as tel,
    A.email as email,
    A.sex as gender,
    A.location as location,
    A.ctime as createTime,
    A.intro as intro,
    A.password as password,
    A.login_salt as salt,
    B.user_group_id as userRoles
    from
    hbb_user as A 
    left join hbb_user_group_link as B 
    on A.uid = B.uid 
    where A.ctime between {0} and {1}
    """.format(datetime_to_unix(startTime), datetime_to_unix(endTime))
    return sql


def get_user(startTime, endTime):
    """导入用户信息"""
    sql = get_user_sql(startTime, endTime)
    cursor.execute(sql)
    for data in cursor.fetchall():
        if not User.objects.filter(o_user_id=str(data['o_user_id'])).exists():
            uid = data['o_user_id']
            # 生成用户头像并存储
            md5Str = md5(str(uid).encode('utf-8')).hexdigest()
            # print(md5Str,md5Str[0])
            avatar = "http://sns.hbbclub.com/data/upload/avatar/{0}/{1}/{2}/original_100_100.jpg".format(
                md5Str[0] + md5Str[1], md5Str[2] + md5Str[3], md5Str[4] + md5Str[4])
            tel = data.get("tel", None)
            try:
                user = User.objects.create(
                    nickName=data.get("nickName"),
                    email=data.get("email"),
                    gender=data.get("gender"),
                    tel=tel,
                    location=data.get("location"),
                    intro=data.get("intro"),
                    userRoles=data.get("userRoles", 3),
                    avatar=avatar,
                )
            except Exception as e:
                logging.error(e)
                break
            sql2 = """
            select 
            type_uid 
            from hbb_login 
            where 
            uid={0} and type={1}
            """.format(str(uid), 'weixin')
            cursor.execute(sql2)
            openid_info = cursor.fetchone()
            if openid_info:
                try:
                    WechatAuth.objects.create(
                        userUuid=user,
                        name=data.get("nickName"),
                        unionid=openid_info["type_uid"],
                    )
                except Exception as e:
                    logging.error(str(e))
                    break
            if tel:
                try:
                    TelAuth.objects.create(
                        userUuid=user,
                        tel=tel,
                        userSource=1,
                    )
                except Exception as e:
                    logging.error(str(e))
                    break
    return


def post_user_sql(user):
    phone = user.userTelUuid.first().tel if user.userTelUuid.first() else ""
    sql = """
    insert into hbb_user (uname,phone,sex,location,ctime,intro,userRoles) 
    value ({0},{1},{2},{3},{4},{5},{6})
    """.format(user.nickName,phone,user.gender,user.location,user.createTime,user.intro,user.userRoles)
    return sql


def post_user(startTime, endTime):
    users = User.objects.filter(createTime__in=[startTime, endTime]).all()
    for user in users:
        telAuth = user.userTelUuid.first()
        if telAuth:
            checkSql = """select * from hbb_user where tel={}""".format(telAuth.tel)
            if cursor.execute(checkSql):
                break
        wechat = user.userWechatUuid.first()
        if wechat:
            checkSql1 = """select * from hbb_login where type_uid={0}""".format(wechat.unionid)
            if cursor.execute(checkSql1):
                break
        try:
            sql = post_user_sql(user)
            cursor.execute(sql)
        except Exception as e:
            logging.error(str(e))
            break
    return
