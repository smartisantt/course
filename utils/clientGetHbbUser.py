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


def get_user_sql(uid):
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
    where A.uid={0}
    """.format(str(uid))
    return sql


def get_user_by_tel_sql(tel):
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
    B.user_group_id as userRoles
    from
    hbb_user as A 
    left join hbb_user_group_link as B 
    on A.uid = B.uid 
    where A.phone='{0}'
    """.format(str(tel))
    return sql

def get_user_by_unionid_sql(unionid):
    sql = """
    select 
    A.uid as o_user_id,
    A.uname as nickName,
    A.phone as tel,
    A.email as email,
    A.sex as gender,
    A.location as location,
    A.ctime as createTime,
    A.intro as intro 
    from
    hbb_user as A 
    left join hbb_login as B 
    on A.uid = B.uid 
    where B.type_uid='{0}' and B.type='weixin'
    """.format(str(unionid))
    return sql


def get_user(value, ftype=None):
    """导入用户信息"""
    sql = get_user_sql(value)
    if ftype == "tel":
        sql = get_user_by_tel_sql(value)
    elif ftype == "wechat":
        sql = get_user_by_unionid_sql(value)
    cursor.execute(sql)
    data = cursor.fetchone()
    if not data:
        return None
    # 生成用户头像并存储
    md5Str = md5(str(data['o_user_id']).encode('utf-8')).hexdigest()
    avatar = "http://sns.hbbclub.com/data/upload/avatar/{0}/{1}/{2}/original_100_100.jpg".format(
        md5Str[0] + md5Str[1], md5Str[2] + md5Str[3], md5Str[4] + md5Str[4])
    data["avatar"] = avatar
    sql2 = """
    select 
    type_uid 
    from hbb_login 
    where 
    uid='{0}' and type="weixin"
    """.format(str(data["o_user_id"]))
    cursor.execute(sql2)
    openid_info = cursor.fetchone()
    if openid_info:
        data["unionid"] = openid_info["type_uid"]
    return data
