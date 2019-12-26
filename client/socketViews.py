"""
dewebsocket
author:York
datetime:2019-10-18
"""

import json
import logging
import threading

from django.core.cache import caches
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from dwebsocket.decorators import accept_websocket
from rest_framework.views import APIView
from rest_framework.response import Response

from client.insertQuery import get_user_role
from client.models import Chats, Discuss
from common.models import ChatsRoom, User

# 定义一个结构存储数据
from utils.clientAuths import ClientAuthentication
from utils.clientPermission import ClientPermission
from utils.tencentGetSign import TLSSigAPIv2

roomDict = {}


@api_view(["POST", "GET"])
@permission_classes([])
@authentication_classes([])
@accept_websocket
def websocketLink(request, token, uuid):
    """连接websocket"""
    if request.is_websocket:
        lock = threading.RLock()
        try:
            lock.acquire()
            try:
                userInfo = caches['common'].get(token)
            except Exception as e:
                logging.error(str(e))
                return_error(request, "服务器缓存错误")
            if not userInfo:
                return_error(request, "登录失效，请重新登录")
            if not uuid:
                return_error(request, "请选择要进入的聊天室")
            room = ChatsRoom.objects.filter(uuid=uuid).first()
            if not room:
                return_error(request, "聊天室不存在")
            if not roomDict.get(uuid):
                roomDict[uuid] = {}
            userUuid = userInfo.get("uuid")
            user = User.objects.filter(uuid=userUuid).first()
            if not user:
                return_error(request, "未获取到用户信息")
            expertUuid = room.expertUuid.userUuid.uuid if room.expertUuid else None
            mcUuid = room.mcUuid.uuid
            luckList = []
            for luck in room.inviterUUid:
                luckList.append(luck.uuid)
            role = "normal"
            nickName = user.nickName
            if userUuid == expertUuid:
                role = "expert"
                nickName = user.expertInfoUuid.name
            else:
                if userUuid == mcUuid:
                    role = "compere"
                else:
                    if userUuid in luckList:
                        role = "luck"
            clienInfo = {
                "request_client": request.websocket,
                "role": role,
                "avatar": user.avatar,
                "username": nickName,
            }
            if roomDict[uuid].get(userUuid):
                roomDict[uuid].update(clienInfo)
            else:
                roomDict[uuid][userUuid] = clienInfo
            # 监听消息
            for message in request.websocket:
                if message:
                    deMsgData = json.loads(message.decode("utf-8"))
                    targetData = dict(deMsgData, **clienInfo.pop("request_client"))
                    if role in ["expert", "compere", "luck"]:
                        roleDict = {
                            "expert": 2,
                            "compere": 3,
                            "luck": 4
                        }
                        try:
                            chat = Chats.objects.create(
                                expertUuid=room.expertUuid,
                                roomUuid=room,
                                userRole=roleDict[role],
                                talkType=targetData.get("type"),
                                content=str(targetData),
                                msgSeq=targetData.get("msgSeq"),
                                msgStatus=1,
                                msgTime=targetData.get("msgTime"),
                                duration=targetData.get("duration"),
                            )
                        except Exception as e:
                            logging.error(str(e))
                            return_error(request, "信息保存失败")
                        if chat.talkType == "qna":
                            question = targetData.get("question")
                            repUuid = question.get("from", None)
                            if repUuid:
                                try:
                                    Discuss.objects.filter(uuid=repUuid).update(isAnswer=True)
                                except Exception as e:
                                    logging.error(str(e))
                                    return_error(request, "更新回复状态失败")
                    else:
                        try:
                            Discuss.objects.create(
                                userUuid=user,
                                roomUuid=room,
                                msgStatus=1,
                                content=str(targetData),
                                msgTime=targetData.get("msgTime"),
                                isQuestion=targetData.get("isQuestion"),
                                isAnswer=False,
                                talkType="txt",
                            )
                        except Exception as e:
                            logging.error(str(e))
                            return_error(request, "信息保存失败")
                    # 分发消息
                    for req in roomDict[uuid].values():
                        req["request_client"].send(str(targetData).encode("utf-8"))
                else:
                    break
        except Exception as e:
            logging.error(str(e))
            return_error(request, "服务器连接错误")
        finally:
            roomDict[uuid].pop(userUuid)
            lock.release()


def return_error(request, msg):
    """返回错误信息"""
    data = {
        "code": 400,
        "msg": msg,
    }
    return request.websocket.send(json.dumps(data).encode('utf-8'))


def return_tencent(mark=0):
    data = {
        "ActionStatus": "OK",
        "ErrorInfo": "",
        "ErrorCode": mark
    }
    return data


class ImCallBackView(APIView):
    """
    流水列表
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def post(self, request):
        command = request.data.get("CallbackCommand")
        if command == "Group.CallbackBeforeSendMsg":
            userUuid = request.data.get("From_Account")
            user = User.objects.filter(uuid=userUuid).first()
            if not user:
                return return_tencent(1)
            roomUuid = request.data.get("GroupId")
            room = ChatsRoom.objects.filter(uuid=roomUuid).first()
            if not room:
                return return_tencent(1)
            msgInfo = request.data.get("MsgBody")
            msgType = msgInfo.get("msgInfo")
            if msgType == "TIMTextElem":  # 文本消息
                pass
            elif msgType == "TIMFaceElem":  # 表情
                pass
            elif msgType == "TIMCustomElem":  # 自定义消息
                pass
            elif msgType == "TIMSoundElem":  # 语音消息
                pass
            elif msgType == "TIMImageElem":  # 图像消息
                pass
            elif msgType == "TIMVideoFileElem":  # 视频消息
                pass
            else:
                return return_tencent(1)
            role = get_user_role(user, room)
            if role == "normal":
                pass
            elif role == "expert":
                pass
            elif role == "compere":
                pass
            elif role == "luck":
                pass
        return return_tencent()


class GetSignView(APIView):
    """
    获取会话标识
    """
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        api = TLSSigAPIv2()
        sig = api.gen_sig(request.user.get("uuid"))
        return Response(sig)
