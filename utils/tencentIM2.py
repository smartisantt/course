import json
import random
import uuid

import requests

from parentscourse_server.config import IM_URL, IM_APPID, DEFAULT_AVATAR
from utils.errors import ParamError
from utils.msg import IM_ERROR, IM_NOT_FOUND_ERROR


class ServerAPI():
    def __init__(self, url=IM_URL, appId=IM_APPID, TIMEOUT=5):
        self.url = url
        self.appId = appId
        self.timeout = TIMEOUT

    def getHeader(self):
        headers = {
            'Content-Type': 'application/json',
            'appId': self.appId,
        }
        return headers

    def getuserSign(self, userName):
        url = self.url + "/api/yyapi/tx/sign"

        data = dict({
            'userName': userName
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader())
            # print(resp.text)
            # {"code":200,"msg":"OK","data":{"expire":8640000,"genSign":"eJw0zVHLgjAU***"}}
            if resp.status_code == 200:
                return resp.json()['data']
        except Exception:
            raise ParamError(IM_ERROR)

    def createUser(self, userName, nickName, faceUrl=DEFAULT_AVATAR):
        url = self.url + "/api/yyapi/tx/user"

        data = dict({
            'userName': userName,
            'nickName': nickName,
            'faceUrl': faceUrl
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader())
            # 200 创建成功   401 重复创建
            if resp.status_code == 200 or resp.status_code == 401:
                return True
            return False
        except Exception:
            raise ParamError(IM_ERROR)

    def createChatroom(self, name, introduction, users: list, groupId="01"):
        """
        创建聊天室
        :param name:
        :param description:
        :param users:            role：DOCTOR(专家)、DZ(主持人)、ASSISTANTS(嘉宾)
        :param groupId:
        :return:
        """
        url = "{}/api/yyapi/tx/chatroom".format(self.url)

        data = dict({
            'name': name,
            'groupId': groupId,
            'introduction': introduction,
            'users': users,
        })
        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            # print(resp.json())
            return resp.json()["data"]["id"]
        except Exception:
            raise ParamError(IM_ERROR)

    def modifyChatroom(self, chatRoomId, name, introduction, groupId="01"):
        url = "{}/api/yyapi/tx/chatroom/info/{}".format(self.url, chatRoomId)

        data = dict({
            'name': name,
            'groupId': groupId,
            'introduction': introduction,
        })
        try:
            resp = requests.put(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            if resp.status_code == 200:
                return True
            else:
                return False
        except Exception:
            raise ParamError(IM_ERROR)

    def modifyChatroomMembers(self, chatRoomId, users: list):
        url = "{}/api/yyapi/tx/chatroom/user/{}".format(self.url, chatRoomId)

        data = dict({
            'users': users,
        })
        try:
            resp = requests.put(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            if resp.json()["code"] == 200:
                return True
        except Exception:
            raise ParamError(IM_ERROR)

    def getChatroom(self, appid="", page="", size=""):
        url = "{}/api/yyapi/tx/chatroom?page={}&size={}&appid={}".format(self.url, page, size, appid)

        try:
            resp = requests.get(url, headers=self.getHeader(), timeout=self.timeout)
            if resp.json()["code"] == 200:
                return resp.json()['data']
        except Exception:
            raise ParamError(IM_ERROR)

    def sendMsg(self, chatRoomId, fromAccount, msgBody):
        url = "{}/api/yyapi/tx/msg".format(self.url)

        data = dict({
            'chatRoomId': chatRoomId,
            'fromAccount': fromAccount,
            'msgBody': msgBody,
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
        except Exception:
            raise ParamError(IM_ERROR)
        if resp.status_code == 200:
            return resp.json()['data']
        if resp.status_code == 404:
            return ParamError(IM_NOT_FOUND_ERROR)

    def mute(self, chatRoomId, userName, expire):
        url = "{}/api/yyapi/tx/chatroom/mute".format(self.url)

        data = dict({
            'chatRoomId': chatRoomId,
            'userName': userName,
            'expire': expire,
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
        except Exception:
            raise ParamError(IM_ERROR)
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            raise ParamError(IM_NOT_FOUND_ERROR)

    def recall(self, chatRoomId, msgSeq):
        url = "{}/api/yyapi/tx/msg/recall".format(self.url)

        data = dict({
            'chatRoomId': chatRoomId,
            'msgSeq': msgSeq
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
        except Exception:
            raise ParamError(IM_ERROR)
        if resp.status_code == 200:
            return True
        if resp.status_code == 400:
            raise ParamError(IM_ERROR)
        if resp.status_code == 401:
            raise ParamError("撤回失败，请检查消息是否存在")


if __name__ == '__main__':
    api = ServerAPI()
    # print(api.getuserSign("1004"))
    # print(api.createUser("1004", "aaa", "http://www.baidu.com"))
    users = [
        {
            "username": "1001",
            "nickname": "陈伦巨",
            "faceUrl": "faceUrl",
            "role": "DOCTOR"
        },
        {
            "username": "1002",
            "nickname": "陈泽春",
            "faceUrl": "faceUrl",
            "role": "DZ"
        },
        {
            "username": "1003",
            "nickname": "陈威",
            "faceUrl": "faceUrl",
            "role": "ASSISTANTS"
        }
    ]

    # print(api.createChatroom("aaa", "这个是聊天室的描述", users))
    # print(api.modifyChatroomMembers("5df98d11fc416b3ccc1adf2f", users))
    # print(api.getChatroom(page=1, appid="txbamaketang"))
    # print(api.sendMsg("5df98d11fc416b3ccc1adf2f", "1003", "ddd"))
    # print(api.mute("5df98d11fc416b3ccc1adf2f", "1003", 10))
    print(api.recall("5df98d11fc416b3ccc1adf2f", 1))
