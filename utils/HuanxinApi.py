import json
import logging
import requests
from django.core.cache import caches

from parentscourse_server.config import *


class ServerAPI():
    def __init__(self, org_name, appname, client_id, client_secret, grant_type="client_credentials"):
        self.org_name = org_name
        self.appname = appname
        self.grant_type = grant_type
        self.client_id = client_id
        self.client_secret = client_secret

    def getTokenFromHuanxin(self):
        """
        获取管理员权限 http://docs-im.easemob.com/im/server/ready/user
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/token".format(self.org_name, self.appname)

        data = dict({
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def getToken(self):
        try:
            token = caches['default'].get("huanxintoken")
            if token:
                return token
            res = self.getTokenFromHuanxin()
            token = res.get("access_token", None)
            if token:
                caches['default'].set("huanxintoken", token, IM_TOKEN_TIMEOUT)
                return token
            return None
        except Exception as e:
            logging.error(str(e))
            return None

    def getTokenHeader(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.getToken(),
        }
        return headers

    def createUser(self, username, password, nickname):
        """
        注册单个用户(授权)
        :param username:
        :param password:
        :param nickname:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/users".format(self.org_name, self.appname)

        data = dict({
            'username': username,
            'password': password,
            'nickname': nickname,
        })

        r = requests.post(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()

    def createManyUsers(self, users):
        """
        批量注册用户
        :param users: [{"username":"user1", "password":"123","nickname":"testuser1"}, {"username":"user2", "password":"456","nickname":"testuser2"}]
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/users".format(self.org_name, self.appname)
        r = requests.post(url, json.dumps(users), headers=self.getTokenHeader())
        return r.json()


    def createChatroom(self, name, description, owner, members=[], maxusers=1000):
        """
        创建聊天室  http://docs-im.easemob.com/im/server/basics/chatroom
        :param name:
        :param description:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/chatrooms".format(self.org_name, self.appname)

        data = dict({
            'name': name,
            'owner': owner,
            'description': description,
            'maxusers': maxusers,
            'members': members,
        })

        r = requests.post(url, json.dumps(data),  headers=self.getTokenHeader())
        return r.json()

    def addChatroomMember(self, chatroomid, username):
        """
        添加单个聊天室成员 http://docs-im.easemob.com/im/server/basics/chatroom#%E6%B7%BB%E5%8A%A0%E5%8D%95%E4%B8%AA%E8%81%8A%E5%A4%A9%E5%AE%A4%E6%88%90%E5%91%98
        :param chatroomid:
        :param username:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}/users/{3}".\
            format(self.org_name, self.appname, chatroomid, username)

        r = requests.post(url, headers=self.getTokenHeader())
        return r.json()

    def sendTextMsgToChatroom(self, target, msg, msgFrom=None):
        """
        发送文本消息
        :param target:
        :param msg:
        :param msgFrom:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/messages". \
            format(self.org_name, self.appname)

        data = dict({
            'target': target,
            'msg':
                {
                    "msg": msg,
                    "type": "txt",
                },
            'from': msgFrom,
            'target_type': "chatrooms",
        })

        r = requests.post(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()

    def mute(self, group_id, mute_duration, usernames):
        """"""
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}/mute". \
            format(self.org_name, self.appname, group_id)

        data = dict({
            'mute_duration': mute_duration,
            'usernames': usernames,
        })

        r = requests.post(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()

    def modifyChatroom(self, chatroom_id, name, description, maxusers=1000):
        """"""
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}". \
            format(self.org_name, self.appname, chatroom_id)

        data = dict({
            'name': name,
            'description': description,
            'maxusers': maxusers,
        })

        r = requests.put(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()

    def delChatroomMembers(self, chatroom_id, usernames):
        """
        批量删除聊天室成员
        :param chatroom_id:
        :param usernames:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}/users/{3}". \
            format(self.org_name, self.appname, chatroom_id, ",".join(usernames))
        r = requests.delete(url, headers=self.getTokenHeader())
        return r.json()

    def addChatroomMembers(self, chatroom_id, usernames):
        """
        批量添加聊天室成员
        :param chatroom_id:
        :param usernames:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}/users". \
            format(self.org_name, self.appname, chatroom_id)

        data = dict({
            'usernames': usernames
        })

        r = requests.post(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()

    def addChatroomAdmin(self, chatroom_id, usernames):
        """
        批量添加聊天室成员
        :param chatroom_id:
        :param usernames:
        :return:
        """
        url = "https://a1.easemob.com/{0}/{1}/chatrooms/{2}/admin". \
            format(self.org_name, self.appname, chatroom_id)


        data = dict({
            'usernames': usernames
        })

        r = requests.post(url, json.dumps(data), headers=self.getTokenHeader())
        return r.json()


if __name__ == '__main__':
    api = ServerAPI(org_name, appname, client_id, client_secret)
    # res = api.getToken()
    # print(res)

    # token = "YWMtaCpIAhWfEeqJJmE5EaGBcwAAAAAAAAAAAAAAAAAAAAG3O4-GjfRMRqu21WiMd0ZVAgMAAAFuyq8EvABPGgCHUApMDwvL4U-KaWah4yOBxIoP_GtU1uNeRkyrp2Pplw"
    # print(api.createChatroom("测试聊天室3", "", "6"))
    # print(api.createUser("user3", "333", "testuser3"))
    # print(api.addChatroomMember(token, "100549682855937", "2"))
    # print(api.addChatroomMember(token, "100549682855937", "2"))
    # print(api.sendTextMsgToChatroom(token, ["100549682855937"], "xxaaaa XXX ", "2"))
    # print(api.mute(token, "100549682855937", 60, ["2"]))
    # print(api.modifyChatroom("100818257772545", "修改环信名", "zheshi jieshao"))
    # print(api.addChatroomMembers("100818257772545", ["3"]))
    print(api.delChatroomMembers("100711985643521", ["3b4a40713423450f87b09ee8f0bdfb10"]))
    # print(api.createManyUsers([{"username":"user3", "password":"333","nickname":"testuser3"}, {"username":"user2", "password":"456","nickname":"testuser2"}]))

