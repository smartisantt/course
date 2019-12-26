import json
import random
import uuid

import requests

from utils.TLSSigAPIv2 import TLSSigAPIv2


class ServerAPI():
    '''
     * 参数初始化
     * @param AppKey
     * @param AppSecret
    '''

    def __init__(self, sdkappid, key, identifier):
        self.sdkappid = sdkappid                            # 开发者平台分配的sdkappid
        self.key = key                                      # 开发者平台分配的key
        self.identifier = identifier                        # 开发者平台分配的identifier
        api = TLSSigAPIv2(sdkappid, key)
        self.usersig = api.gen_sig(identifier)
        self.url_param = "?sdkappid={}&identifier={}&usersig={}&random={}&contenttype=json".\
            format(sdkappid, identifier, self.usersig, random.randint(0, 4294967295))

    def createChatroom(self, Name, Introduction="", GroupId=None):
        """
        创建聊天室
        :param Name: 聊天室名字
        :param Introduction: 聊天室简介
        :param GroupId: 聊天室的id
        :return:
        """
        url = "https://console.tim.qq.com/v4/group_open_http_svc/create_group" + self.url_param

        data = dict({
            'Name': Name,
            'Type': "ChatRoom",
            'Introduction': Introduction,
            'GroupId': GroupId or uuid.uuid4().hex,
        })
        r =requests.post(url, json.dumps(data))
        return r.json()

    def destroyChatroom(self, GroupId):
        """
        删除直播室
        :param GroupId: 直播室的ID
        :return: {'ActionStatus': 'OK', 'ErrorCode': 0, 'ErrorInfo': ''}
        """
        url = "https://console.tim.qq.com/v4/group_open_http_svc/destroy_group" + self.url_param
        data = dict({
            'GroupId': GroupId
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def accountImport(self, Identifier, Nick, FaceUrl=None, Type=0):
        """
        导入单个账号
        :param Identifier: 账号
        :param Nick: 昵称
        :param FaceUrl: 头像
        :param Type: 值0表示普通帐号，1表示机器人帐号
        :return: {'ActionStatus': 'OK', 'ErrorInfo': '', 'ErrorCode': 0}
        """
        url = "https://console.tim.qq.com/v4/im_open_login_svc/account_import" + self.url_param
        data = dict({
            'Identifier': Identifier,
            'Nick': Nick,
            'FaceUrl': FaceUrl,
            'Type': Type,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def accountDelete(self, userIds):
        """
        帐号删除
        :param userIds: 请求删除的帐号对象数组，单次请求最多支持100个帐号
        :return:
        """
        url = "https://console.tim.qq.com/v4/im_open_login_svc/account_delete" + self.url_param
        data = dict({
            'DeleteItem': [{"UserID": item} for item in userIds]
        })
        r = requests.post(url, json.dumps(data))
        return r.json()


    def addGroupMember(self, GroupId, MemberList):
        """
        增加群组成员
        :param GroupId: 要操作的群组（必填）
        :param MemberList: 要添加的群成员ID {"Member_Account": "zhanghao"])
        :return:
        """
        url = "https://console.tim.qq.com/v4/group_open_http_svc/add_group_member" + self.url_param
        data = dict({
            'GroupId': GroupId,
            'MemberList': MemberList,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def deleteGroupMember(self, GroupId, MemberToDel_Account, Reason="扰乱秩序"):
        """
        删除群组成员
        :param GroupId: 要操作的群组（必填）
        :param MemberToDel_Account: 要删除的群成员列表，最多500个 用的账号
        :return:
        """
        url = "https://console.tim.qq.com/v4/group_open_http_svc/delete_group_member" + self.url_param
        data = dict({
            'GroupId': GroupId,
            'MemberToDel_Account': MemberToDel_Account,
            'Reason': Reason,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def setNoSpeaking(self, Set_Account):
        """
        设置用户全局禁言
        :param Set_Account:
        :return:
        """
        url = "https://console.tim.qq.com/v4/openconfigsvr/setnospeaking" + self.url_param
        data = dict({
            "Set_Account": Set_Account,
            "C2CmsgNospeakingTime": 7200,
            "GroupmsgNospeakingTime": 7200
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def sendGroupMsg(self, GroupId, From_Account, MsgBody):
        url = "https://console.tim.qq.com/v4/group_open_http_svc/send_group_msg" + self.url_param
        data = dict({
            "GroupId": GroupId,
            "From_Account": From_Account,
            "Random": random.randint(0, 10000),
            "MsgBody": MsgBody,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()

    def groupMsgGetSimple(self, GroupId, ReqMsgSeq, ReqMsgNumber):
        """
        拉取群漫游消息
        :param GroupId: 要拉取漫游消息的群组 ID
        :param ReqMsgSeq: 拉取的漫游消息的条数，目前一次请求最多返回20条漫游消息，所以这里最好小于等于20
        :param ReqMsgNumber: 拉取消息的最大 seq
        :return:
        """
        url = "https://console.tim.qq.com/v4/group_open_http_svc/group_msg_get_simple" + self.url_param
        data = dict({
            "GroupId": GroupId,
            "ReqMsgSeq": ReqMsgSeq,
            "ReqMsgNumber": ReqMsgNumber,
        })
        r = requests.post(url, json.dumps(data))
        return r.json()




if __name__ == '__main__':
    api = ServerAPI("1400291059", "48c2b4e0bd378502c9d3a638f6e967311f1d9426d75c118a3fb9c84c8df3caf6", "hbbclub")
    # print(api.createChatroom("wwww"))
    # print(api.destroyChatroom("2116e220c1664e5dae33651ad2b720d8"))
    # for i in range(10):
    #     print(api.accountImport("账号"+str(i), "昵称"+str(i), "http://b-ssl.duitang.com/uploads/item/201509/25/20150925110828_iMnGx.jpeg"))
    # for i in range(10):
    #     print(api.addGroupMember("02d75e1c32474f64ad9d7a8b93ca1573", [{"Member_Account":"账号"+str(i)}]))
    # print(api.deleteGroupMember("c1b828e44e5c406e8808d8178b4217c9", ["账号1"]))
    # for i in range(100):
    #     print(api.accountDelete(["账号"+str(i)]))
    print(api.sendGroupMsg("@TGS#3J2TYQCGF", "账号1",  [{"MsgType": "TIMTextElem", "MsgContent": {"Text": "Fuck the day"}}]))
    # print(api.groupMsgGetSimple("@TGS#3BSQBQCGE", 12, 15))