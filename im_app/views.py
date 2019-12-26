import json
import logging

from django.core.cache import caches
from django.views.decorators.cache import cache_page
from django_redis import get_redis_connection
from rest_framework.decorators import api_view, authentication_classes

from client.models import Chats
from common.models import ChatsRoom, User, Experts
from parentscourse_server.config import TOKEN_TIMEOUT, IM_TOKEN_TIMEOUT, IM_PREFIX, IM_PLATFORM, DEFAULT_AVATAR, \
    IM_SIGN_TIMEOUT
from utils.auths import IMAuthentication
from utils.errors import ParamError
from utils.funcTools import http_return
from rest_framework.response import Response

from utils.tencentIM2 import ServerAPI

api = ServerAPI()


def check_identify(func):
    def wrapper(request):
        token = request.META.get('HTTP_TOKEN')
        try:
            user_info = caches['client'].get(token) or caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '服务器连接redis失败')
        if not user_info:
            return http_return(403, '登录失效，请重新登录')
        return func(request)

    return wrapper


# @api_view(["POST"])
# @authentication_classes([IMAuthentication])
# def login(request):
#     # 注册环信 登录  返回登录的 用户名 昵称 角色
#     # uuid  和 直播间的id（校验用户是否有权限进入该直播间）
#     uuid = request.data.get("uuid", None)
#     if not uuid:
#         return http_return(400, "uuid不能为空")
#
#     room_id = request.data.get("room_id", None)
#     if not room_id:
#         return http_return(400, "room_id不能为空")
#     if not ChatsRoom.objects.filter(huanxingId=room_id).exists():
#         return http_return(400, "room_id无效")
#
#     # 从缓存中根据房间的id 和 当前用户的uuid 读取角色
#     try:
#         Conn = get_redis_connection("default")
#         if Conn.hget(room_id, 'DOCTOR') and Conn.hget(room_id, 'DOCTOR').decode() == uuid:
#             role = "expert"
#         elif Conn.hget(room_id, 'DZ') and Conn.hget(room_id, 'DZ').decode() == uuid:
#             role = "compere"
#         elif Conn.hget(room_id, 'ASSISTANTS') and uuid in Conn.hget(room_id, 'ASSISTANTS').decode().split(","):
#             role = "inviter"
#         else:
#             role = "normal"
#     except Exception:
#         raise ParamError("连接Redis失败!!")
#
#     data = {
#         "uuid": request.auth,
#         "pwd": request.auth+"hxpw",
#         "role": role,
#     }
#
#     api = ServerAPI()
#     res = api.createUser(request.auth, request.user.nickName or "没有昵称")
#     if res:
#         return Response(data)
#     raise ParamError("用户注册失败")

@api_view(["POST"])
@authentication_classes([IMAuthentication])
def login(request):
    uuid = request.data.get("uuid", None)
    if not uuid:
        return http_return(400, "uuid不能为空")

    user = User.objects.filter(status__in=[1, 4], uuid=uuid).first()
    if not user:
        return http_return(400, "无效用户uuid")

    # 缓存获取签名
    try:
        userSign = caches['default'].get(IM_PREFIX + uuid)
    except Exception:
        raise ParamError("获取redis中【{}】签名失败失败!!".format(uuid))

    if not userSign:

        res = api.createUser(uuid, user.nickName or "没有昵称", user.avatar or DEFAULT_AVATAR)
        if not res:
            raise ParamError("用户【{}】注册失败".format(uuid))

        res = api.getuserSign(uuid)
        if not res:
            raise ParamError("获取【{}】签名失败".format(uuid))

        userSign = res['genSign']
        caches['default'].set(IM_PREFIX + uuid, userSign, timeout=IM_SIGN_TIMEOUT)

    data = {
        "uuid": uuid,
        "userSign": userSign
    }

    return Response(data)


@api_view(["POST"])
@authentication_classes([IMAuthentication])
def getRole(request):
    uuid = request.data.get("uuid", None)
    if not uuid:
        return http_return(400, "uuid不能为空")

    user = User.objects.filter(status__in=[1, 4], uuid=uuid).first()
    if not user:
        return http_return(400, "无效用户uuid")

    room_id = request.data.get("room_id", None)
    if not room_id:
        return http_return(400, "room_id不能为空")

    if IM_PLATFORM == "TM":
        chatRoom = ChatsRoom.objects.filter(tmId=room_id).first()
        if not chatRoom:
            return http_return(400, "腾讯IM无效")
    else:
        chatRoom = ChatsRoom.objects.filter(huanxingId=room_id).first()
        if not chatRoom:
            return http_return(400, "环信IM无效")

    if ChatsRoom.objects.filter(mcUuid_id=uuid).exists():
        role = "compere"
    elif ChatsRoom.objects.filter(expertUuid__userUuid_id=uuid).exists():
        role = "expert"
    elif {'uuid': uuid} in list(chatRoom.inviterUuid.all().values("uuid")):
        role = "inviter"
    else:
        role = "normal"

    data = {
        "uuid": uuid,
        "role": role,
    }

    return Response(data)


@api_view(["POST"])
@authentication_classes([IMAuthentication])
def sendMsg(request):
    fromAccount = request.data.get("fromAccount", None)
    if not fromAccount:
        return http_return(400, "fromAccount不能为空")

    liveRoomId = request.data.get("liveRoomId", None)
    if not liveRoomId:
        return http_return(400, "liveRoomId不能为空")

    msgBody = request.data.get("msgBody", None)
    if not msgBody:
        return http_return(400, "msgBody不能为空")

    role = request.data.get("role", None)
    if not role in ["inviter", "expert", "compere", "normal"]:
        return http_return(400, "role参数不合法")

    if IM_PLATFORM == "TM":
        chatroom = ChatsRoom.objects.filter(roomChapterUuid__status=1, tmId=liveRoomId).first()
    else:
        chatroom = ChatsRoom.objects.filter(roomChapterUuid__status=1, huanxingId=liveRoomId).first()

    if not chatroom:
        return http_return(400, "未能找到对应的直播室，或者已下架删除")

    # 判断当前直播室状态是否可以发送消息
    # if chatroom.roomChapterUuid.first().updateStatus != 6:
    #     return http_return(400, "该直播室没有在直播状态")

    if role == "expert":
        user = Experts.objects.filter(enable=True, uuid=fromAccount).first()
        if not user:
            return http_return(400, "无效用户uuid")
        fromAccount = user.userUuid.uuid
    else:
        user = User.objects.filter(status__in=[1, 4], uuid=fromAccount).first()
        if not user:
            return http_return(400, "无效用户uuid")

    try:
        data = json.loads(msgBody)
        if not isinstance(data, dict):
            raise ParamError("序列化后消息不合法")

        isQuestion = data.get('isQuestion', None)
        userRole = data['role']
        displayPos = data['display']
        # 提问只能是 普通用户 或者 嘉宾
        if isQuestion and userRole in ["expert", "compere"]:
            raise ParamError("提问只能是 普通用户 或者 嘉宾")

        talkType = data['type']
        duration = data.get("duration", None)
        if talkType == "voice":
            if not duration:
                raise ParamError("音频请传时长")
            elif duration > 60:
                raise ParamError("音频时长需小于60s")

        # 普通用户和嘉宾只能发送文字
        if userRole in ["normal", "inviter"] and talkType != "txt":
            raise ParamError("普通用户和嘉宾只能发送文字")

    except Exception:
        raise ParamError("请传序列化后的消息")

    res = api.sendMsg(liveRoomId, fromAccount, msgBody)
    if res:
        # msgTime = res['MsgTime'] * 1000
        msgSeq = res['MsgSeq']
    else:
        raise ParamError("获取返回消息为空")

    try:
        Chats.objects.create(
            isQuestion=isQuestion,
            roomUuid=chatroom,
            talkType=talkType,
            userRole=userRole,
            content=msgBody,
            msgSeq=msgSeq,
            displayPos=displayPos,
            # msgTime=msgTime,      # 存储回调返回的时间，用户消息带的时间存储在消息体里面
            msgStatus=1,
            duration=duration,
            fromAccountUuid_id=fromAccount
        )
        return http_return(200, "发送成功", {"msgSeq": msgSeq})
    except Exception as e:
        print(e)
        logging.error(str(e))
        return http_return(400, "存储消息失败")


@api_view(["POST"])
@authentication_classes([IMAuthentication])
def mute(request):
    chatRoomId = request.data.get("chatRoomId", None)
    if not chatRoomId:
        return http_return(400, "chatRoomId不能为空")

    userName = request.data.get("userName", None)
    if not userName:
        return http_return(400, "userName不能为空")

    expire = request.data.get("expire", 0)
    if not isinstance(expire, int):
        return http_return(400, "expire需要时整数")
    if expire < 0:
        return http_return(400, "expire需要大于等于0")

    res = api.mute(chatRoomId, userName, expire)
    if res:
        if expire:
            return http_return(200, "禁言成功，禁言时间{}s".format(expire))
        else:
            return http_return(200, "取消禁言成功")
    else:
        return http_return(400, "操作失败")


@api_view(["POST"])
@authentication_classes([IMAuthentication])
def recall(request):
    chatRoomId = request.data.get("chatRoomId", None)
    if not chatRoomId:
        return http_return(400, "chatRoomId不能为空")

    msgSeq = request.data.get("msgSeq", None)
    if not msgSeq:
        return http_return(400, "userName不能为空")
    if not isinstance(msgSeq, int):
        return http_return(400, "msgSeq格式错误")

    if IM_PLATFORM == "TM":
        chat = Chats.objects.filter(roomUuid__tmId=chatRoomId, msgSeq=msgSeq).first()
    else:
        chat = Chats.objects.filter(roomUuid__huanxingId=chatRoomId, msgSeq=msgSeq).first()
    if not chat:
        return http_return(400, "该聊天室不存在")

    res = api.recall(chatRoomId, msgSeq)
    if res:
        if chat.msgSeq:
            chat.msgStatus = 2
            chat.save()
    return http_return(200, "撤回成功")
