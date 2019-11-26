import os, django



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()


import pymysql
from pymysql.cursors import DictCursor

from common.models import Experts, User, Courses, Chapters, CourseSource
from client.models import Discuss
DBHOST2 = '127.0.0.1'
DBUSER2 = 'root'
DBPWD2 = 'hbb123'
DATABASE2 = 'hbb_course'


def updateCourses2ChaptersUuid():
    """
    建立我们表的关联关系，course和chapter  1746
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE `tb_chapters` A, `tb_courses` B set A.courseUuid_id=B.uuid where B.o_room_id=A.o_room_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updateChapters2McUuid():
    """
    建立我们表的关联关系，Chapters和Mc  1744条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_chapters` A, `tb_mc` B set A.mcUuid_id=B.uuid where B.o_compere_id=A.o_compere_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updateChapters2ExpertUuid():
    """
    建立我们表的关联关系，Chapters和Expert  1746条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_chapters` A, `tb_experts` B set A.expertUuid_id=B.uuid where B.o_expert_id=A.o_expert_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updateChapters2CourseSourceUuid():
    """
    建立我们表的关联关系，Chapters和CourseSource 845条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_chapters` A, `tb_coursesource` B set A.courseSourceUuid_id=B.uuid where B.o_topic_id=A.o_topic_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updatePPT2CourseSourceUuid():
    """
    建立我们表的关联关系，PPT和CourseSource 4941条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_coursesource` A, `tb_course_ppt` B set B.sourceUuid_id=A.uuid where B.o_topic_id=A.o_topic_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updateChats2PPTUuid():
    """
    建立我们表的关联关系，Chats和PPT   9013条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_chats` A, `tb_course_ppt` B set A.currPPTUuid_id=B.uuid where B.o_ppt_id=A.o_ppt_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


def updateChats2UserUuid():
    """
    建立我们表的关联关系，Chats和User   9013条
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_chats` A, `tb_user` B set A.userUuid_id=B.uuid where B.o_user_id=A.o_user_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()


#  需要先导入用户表
def updateChats2UserUuid():
    """
    建立我们表的关联关系，Chats和User
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_user` A, `tb_chats` B set B.userUuid_id=A.uuid where B.o_user_id=A.o_user_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()

#  需要先导入用户表
def updateDiscuss2UserUuid():
    """
    建立我们表的关联关系，Discuss和User
    :return:
    """
    # db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    # cursor = db.cursor(DictCursor)
    # cursor.execute("SELECT VERSION()")
    # data = cursor.fetchone()
    #
    # print("Database version : %s " % data)
    # sql="UPDATE  `tb_user` A, `tb_discuss` B set B.userUuid_id=A.uuid where B.o_user_id=A.o_user_id"
    # cursor.execute(sql)
    # db.commit()
    # print(cursor.rowcount, " 条记录已更新")
    # db.close()
    discusses = Discuss.objects.all()
    for discuss in discusses:
        user = User.objects.filter(o_user_id=discuss.o_user_id).first()
        if user:
            discuss.userUuid=user
        course = CourseSource.objects.filter(o_topic_id=discuss.o_topic_id).first()
        if course:
            discuss.courseSourceUuid=course
        discuss.save()

#  需要先导入用户表
def updateMc2UserUuid():
    """
    建立我们表的关联关系，Mc和User
    :return:
    """
    db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    cursor = db.cursor(DictCursor)
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()

    print("Database version : %s " % data)
    sql="UPDATE  `tb_user` A, `tb_mc` B set B.userUuid_id=A.uuid where B.o_user_id=A.o_user_id"
    cursor.execute(sql)
    db.commit()
    print(cursor.rowcount, " 条记录已更新")
    db.close()

#  需要先导入用户表
def updateExpert2UserUuid():
    """
    建立我们表的关联关系，Expert和User
    :return:
    """
    # db = pymysql.connect(DBHOST2, DBUSER2, DBPWD2, DATABASE2, charset='utf8')
    # cursor = db.cursor(DictCursor)
    # cursor.execute("SELECT VERSION()")
    # data = cursor.fetchone()
    #
    # print("Database version : %s " % data)
    # sql="UPDATE  `tb_user` A, `tb_experts` B set B.userUuid_id=A.uuid where B.o_user_id=A.o_user_id"
    # cursor.execute(sql)
    # db.commit()
    # print(cursor.rowcount, " 条记录已更新")
    # db.close()
    experts = Experts.objects.all()
    for expert in experts:
        user = User.objects.filter(o_user_id=expert.o_user_id).first()
        if user:
            expert.userUuid = user
            expert.save()


if __name__ == '__main__':
    # updateChats2UserUuid()
    # updateExpert2UserUuid()
    updateDiscuss2UserUuid()