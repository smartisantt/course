import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()
import pymysql
from pymysql.cursors import DictCursor
import time
import datetime
import json
import ast
from common.models import Orders, OrderDetail, User, Goods, Experts, Courses, Chapters, ChatsRoom
from client.models import Chats
from hashlib import md5, shake_256
from common.models import Payment

""" mysql 数据库配置 """
# DBHOST = 'rm-2ze7srd8bw76fyl52o.mysql.rds.aliyuncs.com'
# DBUSER = 'prod_hbb_ts1'
# DBPWD = 'Ts@HbbPr0d2018'
# DATABASE = 'prod_ts_comm'
# db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
# cursor = db.cursor(DictCursor)


#  导入订单
def insertOrderData():
    # 使用cursor()方法获取操作游标
    cursor = db.cursor(DictCursor)
    # cursor2 = db2.cursor()

    # 使用execute方法执行SQL语句
    # cursor.execute("SELECT VERSION()")
    # cursor2.execute("SELECT VERSION()")
    sqlStr = """
    SELECT
    	order_no,
    	channel,
    	trade_mode,
    	order_status,
    	pay_status,
    	order_amt,
    	order_org_amt,
    	act_payment,
    	buyer_id,
    	buyer_name,
    	buyer_phone,
    	order_date,
    	channel_cd ,
    	order_date
    FROM
    	ims_order;
    """
    cursor.execute(sqlStr)
    datas = cursor.fetchall()
    for data in datas:
        # print(data)
        order = Orders()
        order.orderNum = data["order_no"]
        order.channel = data["channel"]
        # order.goodsType = data["trade_mode"]
        order.orderStatus = (data["order_status"] + 2)
        order.payStatus = (data["pay_status"] + 1)
        order.orderPrice = int(data["order_amt"] * 100)
        order.orderOrgPrice = int(data["order_org_amt"] * 100)
        order.payAmount = int(data["act_payment"] * 100)
        order.o_user_id = data["buyer_id"]
        order.buyerName = data["buyer_name"]
        order.buyerTel = data["buyer_phone"]
        order.createTime = data["order_date"]
        order.channelNum = data["channel_cd"]
        order.save()
        order.createTime = data["order_date"]
        order.save()
    cursor.close()


##  插入订单详情
def insertOrderDetail():
    sqlStr = """
    SELECT
	order_no,
	product_id,
	product_type,
	product_name,
	product_qty,
	product_price,
	product_amt,
	product_org_price,
	product_act_payment 
FROM
	ims_order_detail
    """
    cursor.execute(sqlStr)
    datas = cursor.fetchall()
    for data in datas:
        # print(data)
        order = OrderDetail()
        order.orderUuid = Orders.objects.filter(orderNum=data["order_no"]).first()
        order.o_product_id = int(data.get("product_id", ""))
        order.goodsName = data["product_name"]
        order.goodsCount = data["product_qty"]
        if data["product_type"] == 9:
            order.goodsType = 6
        order.goodsType = data["product_type"]
        order.totalPrice = int(data["product_org_price"] * 100)
        order.payPrice = int(data["product_amt"] * 100)
        order.goodsPrice = int(data["product_act_payment"] * 100)
        order.originalPrice = int(data["product_price"] * 100)

        try:
            order.save()
        except:
            with open('test.txt', 'wt') as f:
                print(data, file=f)
            f.close()


# 导入支付信息
def insertPayment():
    # 打开数据库连接 HBB 数据库

    sqlStr = """
    SELECT
	ims_payment.payment_no,
	ims_payment.pay_ent_no,
	ims_payment.pay_ent_name,
	ims_payment.partner,
	ims_payment.pay_trans_no,
	ims_payment.pay_time,
	ims_payment.pay_status,
	ims_payment_detail.pay_type,
	ims_payment_detail.card_no,
	ims_payment_detail.used_points,
	ims_payment_detail.exp_price 
FROM
	ims_payment
	INNER JOIN ims_payment_detail ON ims_payment.payment_no = ims_payment_detail.payment_no;
    """
    cursor.execute(sqlStr)
    datas = cursor.fetchall()
    for data in datas:
        payment = Payment()
        payment.orderNum_id = data["payment_no"]
        payment.payWay = data["pay_ent_no"]
        payment.payWayName = data["pay_ent_name"]
        payment.partner = data["partner"]
        payment.payTransNo = data["pay_trans_no"]
        # 时间转换
        if data["pay_time"]:
            payment.payTime = int(time.mktime((data["pay_time"]).timetuple()))
        payment.payStatus = data["pay_status"]
        payment.payType = data["pay_type"]
        payment.cardNo = data["card_no"]
        payment.usedPoints = data["used_points"]
        if data["exp_price"]:
            payment.expPrice = int(data["exp_price"] * 100)
        payment.save()


# 导入订单详情


# data2 = cursor2.fetchone()


# print( data.get("pay_status",""))
# print("Database version : %s " % data2)

def unionGoods():
    orders = OrderDetail.objects.filter().all()
    for order in orders:
        goods = Goods.objects.filter(o_product_id=order.o_product_id).first()
        order.goodsUuid = goods
        order.save()


def orderUser():
    orders = Orders.objects.filter().all()
    for order in orders:
        user = User.objects.filter(o_user_id=order.o_user_id).first()
        if user:
            order.userUuid = user
            order.save()
        # print(user.nickName)


def userRole():
    sqlStr = """
    SELECT uid,user_group_id FROM hbb_user_group_link;
    """
    cursor.execute(sqlStr)
    datas = cursor.fetchall()
    for data in datas:
        if data["user_group_id"] != 3:
            user = User.objects.filter(hbbId=data["uid"]).update(userRoles=data["user_group_id"])


def Avatar():
    users = User.objects.filter().all()
    for user in users:
        origin_str = user.hbbId
        md5Str = md5(origin_str.encode('utf-8')).hexdigest()
        # print(md5Str,md5Str[0])
        avatar = "http://sns.hbbclub.com/data/upload/avatar/{0}/{1}/{2}/original_100_100.jpg".format(
            md5Str[0] + md5Str[1], md5Str[2] + md5Str[3], md5Str[4] + md5Str[4])
        user.avatar = avatar
        user.save()


def ChatsUpdate():
    chats = Chats.objects.all()
    for chat in chats:
        expert = Experts.objects.filter(o_user_id=chat.o_user_id).first()
        if expert:
            chat.expertUuid = expert
        if chat.talkType == "voice":
            try:
                aaa = json.loads(chat.content).encode('utf-8')
                bbb = json.loads(aaa)
                chat.duration = bbb["duration"]
            except:
                continue
        chat.save()


def CourseExpert():
    courses = Courses.objects.all()
    for course in courses:
        expert = Chapters.objects.filter(courseUuid=course).first()
        if expert:
            course.expertUuid = expert.expertUuid
        course.save()


def createChatsRoom():
    for i in range(10):
        chatroom = ChatsRoom()
        chatroom.name = "测试直播间%s"%i
        chatroom.studyNum = 100
        chatroom.save()

createChatsRoom()