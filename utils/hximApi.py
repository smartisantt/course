import json
import time

import requests
import threading

from parentscourse_server.config import IM_URL, IM_APPID
from utils.errors import ParamError
from utils.msg import IM_ERROR


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

    def createUser(self, userName, nickName):
        url = "{}/api/yyapi/im/user".format(self.url)

        data = dict({
            'userName': userName,
            'nickName': nickName,
        })

        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader())
            if resp.status_code == 200 or resp.status_code == 401:
                return True
        except Exception:
            raise ParamError(IM_ERROR)

    def createChatroom(self, name, description, users: list, groupId="01"):
        """
        创建聊天室
        :param name:
        :param description:
        :param users:            role：DOCTOR(专家)、DZ(主持人)、ASSISTANTS(嘉宾)
        :param groupId:
        :return:
        """
        url = "{}/api/yyapi/im/chatroom".format(self.url)

        data = dict({
            'name': name,
            'groupId': groupId,
            'description': description,
            'users': users,
        })
        try:
            resp = requests.post(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            return resp.json()["data"]["hxId"]
        except Exception:
            raise ParamError(IM_ERROR)

    def modifyChatroom(self, hxId, name, description, groupId="01"):
        url = "{}/api/yyapi/im/chatroom/info".format(self.url)

        data = dict({
            'hxId': hxId,
            'name': name,
            'description': description,
            'groupId': groupId,
        })
        try:
            resp = requests.put(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            return resp.json()
        except Exception:
            raise ParamError(IM_ERROR)

    def modifyChatroomMembers(self, hxId, users: list):
        url = "{}/api/yyapi/im/chatroom/user".format(self.url)

        data = dict({
            'hxId': hxId,
            'users': users,
        })
        try:
            resp = requests.put(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)
            if resp.json()["code"] == 200:
                return True
        except Exception:
            raise ParamError(IM_ERROR)

    def sendMsg(self, fromUser, msg, target, targetType="chatrooms"):
        url = "{}/api/yyapi/im/msg".format(self.url)

        data = dict({
            'target': target,
            'targetType': targetType,
            'users': users,
            'msg': {
                "msg": msg,
                "type": "txt",
            },
            'from': fromUser,           # 此用户是已经注册的环信用户id
        })

        try:
            resp = requests.put(url, json.dumps(data), headers=self.getHeader(), timeout=self.timeout)

            if resp.status_code == 200:
                return True
        except Exception:
            raise ParamError(IM_ERROR)


if __name__ == '__main__':
    api = ServerAPI()
    # print(api.createUser("11", "昵称1"))
    users = [
        {
            "username": "1000",
            "nickname": "尹鑫",
            "role": "OWNER"
        },
        {
            "username": "1001",
            "nickname": "陈伦巨",
            "role": "DOCTOR"
        },
        {
            "username": "1002",
            "nickname": "陈泽春",
            "role": "DZ"
        },
        {
            "username": "1003",
            "nickname": "陈威",
            "role": "ASSISTANTS"
        }
    ]


    print(api.createChatroom("aaa", "这个是聊天室的描述", users))

    # print(api.sendMsg())

    # for i in range(10000):
    #     print(api.createUser(str(i), "nicheng"+str(i)))
    # for i in range(10000):
    #     print(i)
    #     thread = threading.Thread(target=api.createChatroom, args=("陈伦巨建的聊天室"+str(i), "这个是聊天室的描述", users))
    #
    #     # print(api.modifyChatroom("101168583868
    #     #
    #     #
    #     # 417", "修改名字", "xiugai"))
    #     thread.start()
    #     time.sleep(0.2)
