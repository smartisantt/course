import os, django



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()


import pymysql
from pymysql.cursors import DictCursor

from common.models import Experts, User, Courses, Chapters, CourseSource, Mc, CoursePPT, InviteCodes
from client.models import Discuss, Chats
from django.db.models import Q

def McUnion():
    Mcs = Mc.objects.all()
    for mc in Mcs:
        user =  User.objects.filter(o_user_id=mc.o_user_id).first()
        if user:
            mc.userUuid=user
            mc.save()


def uniconChapter():
    chapters = Chapters.objects.all()
    for chapter in chapters:
        courseSource = CourseSource.objects.filter(o_topic_id=chapter.o_topic_id).first()
        if courseSource:
            chapter.courseSourceUuid=courseSource
        course = Courses.objects.filter(o_room_id=chapter.o_room_id).first()
        if course:
            chapter.courseUuid = course
        expert = Experts.objects.filter(o_expert_id=chapter.o_expert_id).first()
        if expert:
            chapter.expertUuid = expert

        mc = Mc.objects.filter(o_compere_id=chapter.o_compere_id).first()
        if mc:
            chapter.mcUuid_id = mc.userUuid_id
        chapter.save()

def ChatsUnion():
    chats = Chats.objects.all()
    for chat in chats:
        user = User.objects.filter(o_user_id=chat.o_user_id).first()
        ppt = CoursePPT.objects.filter(o_ppt_id=chat.o_ppt_id).first()
        if user:
            chat.userUuid = user
        if ppt:
            chat.currPPTUuid = ppt
        chat.save()
#
def ExpertsUser():
    experts = Experts.objects.all()
    for expert in experts:
        user = User.objects.filter(uuid=expert.userUuid_id).first()
        if user:
            expert.tel = user.tel
            expert.save()

def coursePpt():
    ppts = CoursePPT.objects.all()
    for ppt in ppts:
        source = CourseSource.objects.filter(o_topic_id=ppt.o_topic_id).first()
        if source:
            ppt.sourceUuid = source.uuid
        ppt.save()

def inviteUnion():
    invites = InviteCodes.objects.exclude(o_user_id=None).all()
    for invite in invites:
        user = User.objects.filter(o_user_id=invite.o_user_id).first()
        if user:
            invite.userUuid=user
        invite.save()



# McUnion()
# uniconChapter()
# ChatsUnion()
# ExpertsUser()
inviteUnion()