import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()

import pymysql
from pymysql.cursors import DictCursor

from client.models import Discuss, Chats
from common.models import Courses, Experts, Mc, Chapters, CourseSource, CoursePPT, Goods

""" mysql 数据库配置 """
DBHOST = 'rm-2ze7srd8bw76fyl52o.mysql.rds.aliyuncs.com'
DBUSER = 'prod_hbb_ts1'
DBPWD = 'Ts@HbbPr0d2018'
DATABASE = 'prod_ts_comm'


def insertCourse1():
    """
    导入 课程  1124条记录
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    mysql_query = """
SELECT							-- 非直播课课程
A.id as o_room_id,	
1 as o_room_type,		-- o_room_id 来自两张表， 1 代表 ims_chat_room（音频视频） 2 代表ims_rb_room（直播）

A.room_type+1 as courseType, -- 0：专题1：系列-> 1 单次课，2系列课
A.room_name as `name`,
A.sub_title as subhead,
A.room_desc as briefIntro,				-- 课程简介
A.plan_topic_count as preChapter,   -- 预计章节数
A.begin_time*1000 as startTime,  	-- 开始时间毫秒时间戳
A.end_time*1000 as endTime,				-- 结束时间毫秒时间戳
A.room_banner as courseBanner,		-- 课程封面
A.room_thumbnail as courseThumbnail,	-- 缩略图
A.room_mp_" as shareImg,	-- 小程序分享图
2 as infoType,		-- 课程说明存储类型 1富文本 2 逗号分隔图片
GROUP_CONCAT(B.img_url ORDER BY B.img_order) as info,
A.discount as discount,
A.line_through_price*100 as originalPrice,	-- 元 -》单位分
A.price*100 as realPrice,										-- 元 -》单位分
A.reward_status as rewardStatus,			-- 0-不开启,1-开启
A.reward_percent as rewardPercent,		-- 分成比例
A.x_look_numbers as vPopularity,
A.keywords as keywords,	
A.introduction as introduction,
A.update_status+1 as updateStatus		--  0：已完结 1：更新中  ->1：已完结 2：更新中

FROM
ims_chat_room AS A
INNER JOIN ims_chat_room_desc AS B ON A.id = B.room_id
WHERE B.enabled = 1  
GROUP BY B.room_id
        """

    cursor.execute(mysql_query)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not Courses.objects.filter(o_room_id=data['o_room_id']).exists() and data['o_room_id']:
            Courses.objects.create(
                o_room_id=data['o_room_id'],
                o_room_type=data['o_room_type'],
                courseType=data['courseType'],  # 课程类型 1为单次课，2为系列课
                name=data['name'],
                subhead=data['subhead'],
                briefIntro=data['briefIntro'],
                preChapter=data['preChapter'],
                startTime=data['startTime'],
                endTime=data['endTime'],
                courseBanner=data['courseBanner'],
                courseThumbnail=data['courseThumbnail'],
                shareImg=data['shareImg'],
                infoType=data['infoType'],
                info=data['info'],  # 富文本 长图
                discount=data['discount'],
                originalPrice=data['originalPrice'],
                realPrice=data['realPrice'],
                rewardStatus=data['rewardStatus'],
                rewardPercent=data['rewardPercent'],
                vPopularity=data['vPopularity'],
                keywords=data['keywords'],
                introduction=data['introduction'],
                updateStatus=data['updateStatus']
            )
        else:
            print("Courses.o_room_id: %d 已经存在" % data['o_room_id'])
    db.close()


def insertCourse2():
    """
    导入 课程 43条记录
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    mysql_query = """
SELECT							-- 代表ims_rb_room
A.id as o_room_id,	
2 as o_room_type,		-- o_room_id 来自两张表， 1 代表 ims_chat_room 2 代表ims_rb_room
A.room_type+1 as courseType, -- 0：专题1：系列-> 1 单次课，2系列课
A.room_name as `name`,
A.sub_title as subhead,
A.room_desc as briefIntro,				-- 课程简介
A.plan_topic_count as preChapter,   -- 预计章节数
A.begin_time*1000 as startTime,  	-- 开始时间毫秒时间戳
A.end_time*1000 as endTime,				-- 结束时间毫秒时间戳
A.room_banner as courseBanner,		-- 课程封面
A.room_thumbnail as courseThumbnail,	-- 缩略图
A.room_mp_share as shareImg,	-- 小程序分享图
2 as infoType,		-- 课程说明存储类型 1富文本 2 逗号分隔图片
GROUP_CONCAT(B.img_url ORDER BY B.img_order) as info,
A.discount as discount,
A.line_through_price*100 as originalPrice,	-- 元 -》单位分
A.price*100 as realPrice,										-- 元 -》单位分
A.reward_status as rewardStatus,			-- 0-不开启,1-开启
A.reward_percent as rewardPercent,		-- 分成比例
A.x_look_numbers as vPopularity,
A.keywords as keywords,	
A.introduction as introduction,
A.update_status+1 as updateStatus		--  0：已完结 1：更新中  ->1：已完结 2：更新中

FROM
ims_rb_room AS A
INNER JOIN ims_chat_room_desc AS B ON A.id = B.room_id
WHERE B.enabled = 1  
GROUP BY B.room_id
        """

    cursor.execute(mysql_query)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not Courses.objects.filter(o_room_id=data['o_room_id']).exists() and data['o_room_id']:
            Courses.objects.create(
                o_room_id=data['o_room_id'],
                o_room_type=data['o_room_type'],
                courseType=data['courseType'],  # 课程类型 1为单次课，2为系列课
                name=data['name'],
                subhead=data['subhead'],
                briefIntro=data['briefIntro'],
                preChapter=data['preChapter'],
                startTime=data['startTime'],
                endTime=data['endTime'],
                courseBanner=data['courseBanner'],
                courseThumbnail=data['courseThumbnail'],
                shareImg=data['shareImg'],
                infoType=data['infoType'],
                info=data['info'],  # 富文本 长图
                discount=data['discount'],
                originalPrice=data['originalPrice'],
                realPrice=data['realPrice'],
                rewardStatus=data['rewardStatus'],
                rewardPercent=data['rewardPercent'],
                vPopularity=data['vPopularity'],
                keywords=data['keywords'],
                introduction=data['introduction'],
                updateStatus=data['updateStatus']
            )
        else:
            print("Courses.o_room_id: %d 已经存在" % data['o_room_id'])
    db.close()


def insertChapters1():
    """
    导入 章节  1724条数据
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql2 = """
SELECT 							-- 章节表
A.id as o_room_id,		
B.id as o_topic_id,
A.compere_id as o_compere_id,
A.expert_id as o_expert_id,
A.enabled as `enable`,
	
B.topic_name as `name`,						-- 
B.topic_order as serialNumber,		-- 章节顺序
B.topic_type as chapterStyle, 	-- 主题类型 1:直播 2:音频 3:视频 --> 我们的表：1:直播 2:音频 3:视频
B.try_listen+1 as isTry,				-- 试听  0：否1：是  -->  我们的表 1 收费 2 试听
C.duration,											-- 音频 视频时长
B.begin_time*1000 as startTime,	-- 开始时间 毫秒单位时间戳
B.end_time*1000 as endTime,			-- 结束时间 毫秒单位时间戳
B.topic_banner as chapterBanner,-- 章节封面图
B.topic_desc as info						-- 章节介绍

FROM `ims_chat_room` A
LEFT JOIN  `ims_chat_topic` B ON A.id=B.room_id 
LEFT JOIN `ims_media` C ON C.topic_id=B.id
"""

    cursor.execute(sql2)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        if not Chapters.objects.filter(o_topic_id=data['o_topic_id']).exists() and data['o_topic_id']:
            Chapters.objects.create(
                o_topic_id=data['o_topic_id'],
                o_room_id=data['o_room_id'],
                o_compere_id=data['o_compere_id'],
                o_expert_id=data['o_expert_id'],
                enable=data['enable'],
                name=data['name'],
                serialNumber=data['serialNumber'],
                chapterStyle=data['chapterStyle'],
                isTry=data['isTry'],
                duration=data['duration'],
                startTime=data['startTime'],
                endTime=data['endTime'],
                chapterBanner=data['chapterBanner'],
                info=data['info'],
            )
    db.close()


def insertChapters2():
    """
    导入 章节 46条
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql2 = """
SELECT 							-- 章节表
A.id as o_room_id,		
B.id as o_topic_id,
A.compere_id as o_compere_id,
A.expert_id as o_expert_id,
A.enabled as `enable`,

B.topic_name as `name`,						-- 
B.topic_order as serialNumber,		-- 章节顺序
B.topic_type as chapterStyle, 	-- 主题类型 1:直播 2:音频 3:视频 --> 我们的表：1:直播 2:音频 3:视频
B.try_listen+1 as isTry,				-- 试听  0：否1：是  -->  我们的表 1 收费 2 试听
C.duration as duration,											-- 音频 视频时长
B.begin_time*1000 as startTime,	-- 开始时间 毫秒单位时间戳
B.end_time*1000 as endTime,			-- 结束时间 毫秒单位时间戳
B.topic_banner as chapterBanner,-- 章节封面图
B.topic_desc as info						-- 章节介绍

FROM `ims_rb_room` A
LEFT JOIN  `ims_rb_topic` B ON A.id=B.room_id 
LEFT JOIN `ims_media` C ON C.topic_id=B.id
"""

    cursor.execute(sql2)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        if not Chapters.objects.filter(o_topic_id=data['o_topic_id']).exists() and data['o_topic_id']:
            Chapters.objects.create(
                o_topic_id=data['o_topic_id'],
                o_room_id=data['o_room_id'],
                o_compere_id=data['o_compere_id'],
                o_expert_id=data['o_expert_id'],
                enable=data['enable'],
                name=data['name'],
                serialNumber=data['serialNumber'],
                chapterStyle=data['chapterStyle'],
                isTry=data['isTry'],
                duration=data['duration'],
                startTime=data['startTime'],
                endTime=data['endTime'],
                chapterBanner=data['chapterBanner'],
                info=data['info'],
            )
    db.close()


def insertExpert():
    """
    导入  专家表 299条
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql3 = """
SELECT
A.id as o_expert_id,
A.expert_uid as o_user_id,
A.expert_name as `name`,
A.avatar_img as avatar,
B.organization_name as hospital,
C.department_name as department,
D.title_name as jobTitle,
A.speciality as specialty,
A.is_star as isStar,
A.expert_desc as intro,
A.career_info as careerInfo,
A.enabled as `enable`
FROM `ims_expert` A
LEFT JOIN `ims_organization` B ON B.id=A.organization_id
LEFT JOIN `ims_department` C ON C.id=A.department_id
LEFT JOIN `ims_title` D ON D.id=A.title_id
"""

    cursor.execute(sql3)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        if not Experts.objects.filter(o_expert_id=data['o_expert_id']).exists() and data['o_expert_id']:
            Experts.objects.create(
                o_expert_id=data['o_expert_id'],
                o_user_id=data['o_user_id'],
                name=data['name'],
                avatar=data['avatar'],
                hospital=data['hospital'],
                department=data['department'],
                jobTitle=data['jobTitle'],
                specialty=data['specialty'],
                isStar=data['isStar'],
                intro=data['intro'],
                careerInfo=data['careerInfo'],
                enable=data['enable']
            )

    db.close()


def insertMc():
    """
    导入  主持人表 18条
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql3 = """
SELECT
A.id as o_compere_id,
A.compere_uid as o_user_id,
A.compere_name as `name`,
A.avatar_img as avatar,
B.organization_name as organization,
C.department_name as department,
A.speciality as specialty,
A.enabled as `enable`
FROM `ims_compere` A
LEFT JOIN `ims_organization` B ON B.id=A.organization_id
LEFT JOIN `ims_department` C ON C.id=A.department_id
LEFT JOIN `ims_title` D ON D.id=A.title_id
"""

    cursor.execute(sql3)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        if not Mc.objects.filter(o_compere_id=data['o_compere_id']).exists() and data['o_compere_id']:
            Mc.objects.create(
                o_compere_id=data['o_compere_id'],
                o_user_id=data['o_user_id'],
                name=data['name'],
                avatar=data['avatar'],
                organization=data['organization'],
                department=data['department'],
                specialty=data['specialty']
            )

    db.close()


def insertDiscuss():
    """
    导入  直播课的讨论表 13141条
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql3 = """
SELECT 					-- 讨论表

C.owner_uid as o_user_id,
C.topic_id as o_topic_id,
C.id as o_discuss_id,

C.dis_status as msgStatus, 	-- 对话状态(1-正常,2-撤回)
C.dis_content as content,
C.msg_seq as msgSeq, 

C.msg_time*1000 as msgTime,-- 前端创建消息时间 单位毫秒时间戳
C.dis_type as talkType,

C.ask_type as isQuestion,
C.ask_status as isAnswer		-- 0-未回复,1-已回复

FROM `ims_chat_topic` B 
INNER JOIN `ims_chat_discuss` C ON C.topic_id=B.id
        """

    cursor.execute(sql3)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        # ims_chat_disscuss 13136条  使用 sql3
        if not Discuss.objects.filter(o_discuss_id=data['o_discuss_id']).exists() and data['o_discuss_id']:
            Discuss.objects.create(
                o_discuss_id=data['o_discuss_id'],
                o_topic_id=data['o_topic_id'],
                o_user_id=data['o_user_id'],
                msgStatus=data['msgStatus'],
                content=data['content'],
                msgSeq=data['msgSeq'],
                msgTime=data['msgTime'],
                talkType=data['talkType'],
                isQuestion=data['isQuestion'],
                isAnswer=data['isAnswer']
            )

    db.close()


def insertChats():
    """
    导入 (老师上课直播) 20534条记录
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql4 = """
SELECT
A.id as o_subject_id,
A.curr_ppt_id as o_ppt_id,
A.curr_ppt_id as o_topic_id,
A.owner_uid as o_user_id,
A.sub_type as talkType,
A.sub_content as content,
A.msg_seq as msgSeq,
A.sub_status as msgStatus,
A.msg_time*1000 as msgTime
FROM `ims_chat_subjects` A;
"""

    cursor.execute(sql4)
    i = 0
    j = 0
    while 1:
        print("成功插入：{}/查询总记录：{}".format(j, i))
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not Chats.objects.filter(o_subject_id=data['o_subject_id']).exists() and data['o_subject_id']:
            j += 1
            Chats.objects.create(
                o_subject_id=data['o_subject_id'],
                o_ppt_id=data['o_ppt_id'],
                o_topic_id=data['o_topic_id'],
                o_user_id=data['o_user_id'],
                talkType=data['talkType'],
                content=data['content'],
                msgSeq=data['msgSeq'],
                msgStatus=data['msgStatus'],
                msgTime=data['msgTime'],
            )
    db.close()


def insertCourseSource1():
    """
    导入 课件库 音频和视频 641条
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql4 = """
SELECT
A.id as o_media_id,
A.topic_id as o_topic_id,
A.`name` as `name`,
A.media_path as sourceUrl,
A.size as fileSize,
A.type as sourceType,
A.duration as duration,
if(A.is_del=1, 0,1) as `enable`
From `ims_media` A
"""

    cursor.execute(sql4)
    i = 0
    j = 0
    while 1:
        print("成功插入：{}/查询总记录：{}".format(j, i))
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not CourseSource.objects.filter(o_media_id=data['o_media_id']).exists() and data['o_media_id']:
            j += 1
            CourseSource.objects.create(
                o_media_id=data['o_media_id'],
                o_topic_id=data['o_topic_id'],
                name=data['name'],
                sourceUrl=data['sourceUrl'],
                fileSize=data['fileSize'],
                sourceType=data['sourceType'],
                duration=data['duration'],
                enable=data['enable']
            )
    db.close()


def insertCourseSource2():
    """
    导入 课件库 PPT 226条= 204+22
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql4 = """
SELECT
A.id as o_topic_id,
A.topic_name as `name`,
3 as sourceType
From `ims_chat_topic` A
INNER JOIN `ims_chat_topic_ppt` B ON A.id=B.topic_id
GROUP BY A.id
union 
SELECT
A.id as o_topic_id,
A.topic_name as `name`,
3 as sourceType
From `ims_rb_topic` A
INNER JOIN `ims_chat_topic_ppt` B ON A.id=B.topic_id
GROUP BY A.id
"""

    cursor.execute(sql4)
    i = 0
    j = 0
    while 1:
        print("成功插入：{}/查询总记录：{}".format(j, i))
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not CourseSource.objects.filter(o_topic_id=data['o_topic_id']).exists() and data['o_topic_id']:
            j += 1
            CourseSource.objects.create(
                o_topic_id=data['o_topic_id'],
                name=data['name'],
                sourceType=data['sourceType']
            )
    db.close()


def insertPPT():
    """
    导入  PPT 4941
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql5 = """
SELECT
A.id as o_ppt_id,
A.topic_id as o_topic_id,
A.img_url as imgUrl,
A.img_order as sortNum,
A.enabled as `enable`
From `ims_chat_topic_ppt` A
"""

    cursor.execute(sql5)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1

        if not CoursePPT.objects.filter(o_ppt_id=data['o_ppt_id']).exists() and data['o_ppt_id']:
            CoursePPT.objects.create(
                o_ppt_id=data['o_ppt_id'],
                o_topic_id=data['o_topic_id'],
                imgUrl=data['imgUrl'],
                sortNum=data['sortNum'],
                enable=data['enable']
            )


    db.close()


def insertGoods():
    """
    导入  商品（课程商品）
    :return:
    """
    db = pymysql.connect(DBHOST, DBUSER, DBPWD, DATABASE, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql6 = """
SELECT  -- 1124条数据
id as o_product_id,
room_name as `name`,
line_through_price*100 as originalPrice,	-- 划线价
price*100 as realPrice,						-- 真实价
1 as goodsType  -- 1  "课程"
FROM `ims_chat_room`
union
SELECT 		-- 43条数据
id as o_product_id,
room_name as `name`,
line_through_price*100 as originalPrice,	-- 划线价
price*100 as realPrice,						-- 真实价
1 as goodsType  -- 1  "课程"
FROM `ims_rb_room`
"""

    cursor.execute(sql6)
    i = 0
    while 1:
        print(i)
        data = cursor.fetchone()
        print(data)
        if not data:
            print(i)
            break
        i += 1
        if not Goods.objects.filter(o_product_id=data['o_product_id']).exists() and data['o_product_id']:
            Goods.objects.create(
                o_product_id=data['o_product_id'],
                name=data['name'],
                originalPrice=data['originalPrice'],
                realPrice=data['realPrice'],
                goodsType=data['goodsType']
            )

    db.close()




if __name__ == '__main__':
    # insertCourse1()
    # insertCourse2()
    # insertChapters1()
    # insertChapters2()
    # insertExpert()
    # insertMc()
    # insertDiscuss()
    # insertChats()
    # insertCourseSource1()
    # insertCourseSource2()
    # insertPPT()
    insertGoods()