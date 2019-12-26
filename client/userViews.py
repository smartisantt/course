import logging
import os

from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import caches
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.views import APIView
from rest_framework.response import Response

from client.clientCommon import random_string, match_tel, get_token, unix_time_to_datetime, is_valid_idcard
from client.insertQuery import set_user_session, save_login_log, wechat_bind_tel, tel_bind_wechat, save_access_token, \
    save_hbb_user
from client.models import Chats
from client.serializers import UserSerializer
from fileTools.fileTool import GetWechatFile
from fileTools.uploadFile import delete_file
from parentscourse_server.settings import BASE_DIR
from utils.clientGetHbbUser import get_user
from utils.clientJsSDK import JsSdk, get_res_data
from utils.clientPermission import ClientPermission
from client.ssoSMS.sms import send_sms
from common.models import User, TelAuth, WechatAuth
from parentscourse_server.config import IS_SEND, TEL_IDENTIFY_CODE, TOKEN_TIMEOUT, REALNAME_TIMEOUT, DEFAULT_AVATAR
from utils.clientAuths import ClientAuthentication
from utils.funcTools import http_return
from utils.hbbCheckLogin import HbbLogin
from utils.wechatLogin import WxLogin


def login_return(user, token):
    """登录成功返回模型"""
    data = {
        "token": token,
        "profile": UserSerializer(user, many=False).data
    }
    return data


class SendMsgCode(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_scope = "sms"

    def post(self, request):
        """
        发送验证码
        :param request:
        :return:
        """
        tel = request.data.get("tel", None)
        if not tel:
            return http_return(400, "请输入手机号")
        if not match_tel(tel):
            return http_return(400, "请输入正确的手机号")
        my_random = random_string(6)
        text = "您的短信验证码是{0}。若非本人发送，请忽略此短信。本条短信免费。".format(my_random)
        if IS_SEND:
            rv = send_sms(tel, text)
            try:
                result = eval(rv)
            except Exception as e:
                logging.error(str(e))
                result = {"code": 0, "msg": "", "smsid": "0"}
        else:
            my_random = '123456'
            result = {'code': 2}
        if result.get('code', '0') == 2:
            try:
                caches['client'].set(tel, my_random, TEL_IDENTIFY_CODE)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "服务器缓存错误")
            return http_return(200, '短信已发送')
        else:
            return http_return(400, '短信发送失败')


@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def register(request):
    """
    注册
    :param request:
    :return:
    """
    tel = request.data.get("tel", None)
    if not tel or not match_tel(tel):
        return http_return(400, "请输入正确的手机号")
    password = request.data.get("password", None)
    if not password:
        return http_return(400, "请输入密码")
    if len(password) < 6 or len(password) > 16:
        return http_return(400, "密码长度错误")
    code = request.data.get("code", None)
    if not code:
        return http_return(400, "请输入验证码")
    checkTel = TelAuth.objects.filter(tel=tel, status=1).first()
    if checkTel:
        return http_return(400, "该手机号已注册")
    sendCode = caches['client'].get(tel, None)
    if not sendCode:
        return http_return(400, "验证码已失效")
    if sendCode != code:
        return http_return(400, "验证码错误")
    try:
        caches['client'].delete(tel)
    except Exception as e:
        logging.error(str(e))
    try:
        user = User.objects.create(
            tel=tel,
            nickName=tel,
            registerPlatform=1,
            gender=3,
            avatar=DEFAULT_AVATAR,
        )
        TelAuth.objects.create(
            userUuid=user,
            tel=tel,
            passwd=make_password(password),
            userSource=2,
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "注册失败")
    token = get_token()
    if not set_user_session(token, user):
        return http_return(400, "服务器缓存错误")
    if not save_login_log(user, request, "PHONE"):
        return http_return(400, "存储登陆日志失败")
    return http_return(200, "注册成功", login_return(user, token))


@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def login(request):
    """
    登录
    :param request:
    :return:
    """
    loginType = request.data.get("type", None)
    tel = request.data.get("tel", None)
    if not tel:
        return http_return(400, "请输入手机号")
    if not match_tel(tel):
        return http_return(400, "手机号格式不正确")
    user = None
    if loginType == "pwd":
        password = request.data.get("password", None)
        if not password:
            return http_return(400, "请输入密码")
        if len(password) < 6 or len(password) > 16:
            return http_return(400, "密码长度错误")
        checkTel = TelAuth.objects.filter(tel=tel).first()
        if checkTel:
            passwd = checkTel.passwd
            if not passwd:
                return http_return(400, "账号未设置密码")
            if not check_password(password, passwd):
                return http_return(400, "手机号或密码错误")
            user = checkTel.userUuid
        else:
            hbb = HbbLogin()
            res = hbb.check_login(tel, password)
            try:
                resData = eval(res)
                status = resData.get("status")
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "登录错误")
            if status == 1:
                uid = resData.get("uid", None)
                hbbUserData = get_user(uid)
                if not hbbUserData:
                    return http_return(400, "获取用户信息失败")
                user = save_hbb_user(hbbUserData, tel, password)
                if not user:
                    return http_return(400, "数据迁移存储失败")
            elif status == 0:
                return http_return(400, "用户名或密码错误")
            else:
                return http_return(400, "登录失败")
    else:  # 手机验证码登录
        code = request.data.get("code", None)
        if not code:
            return http_return(400, "请输入验证码")
        sendCode = caches['client'].get(tel, None)
        if not sendCode:
            return http_return(400, "验证码已失效")
        if sendCode != code:
            return http_return(400, "验证码错误")
        try:
            caches['client'].delete(tel)
        except Exception as e:
            logging.error(str(e))
        checkTel = TelAuth.objects.filter(tel=tel).first()
        if checkTel:
            user = checkTel.userUuid
        else:
            hbbUserData = get_user(tel, "tel")
            if not hbbUserData:
                return http_return(400, "手机号未注册")
            user = save_hbb_user(hbbUserData, tel)
            if not user:
                return http_return(400, "数据迁移存储失败")
    token = get_token()
    if not set_user_session(token, user):
        return http_return(400, "服务器缓存错误")
    if not save_login_log(user, request, "PHONE"):
        return http_return(400, "存储登陆日志失败")
    return http_return(200, "登陆成功", login_return(user, token))


@api_view(["POST"])
@permission_classes([ClientPermission])
@authentication_classes([ClientAuthentication])
def logout(request):
    """
    退出登录
    :param request:
    :return:
    """
    try:
        caches['client'].delete(request.auth)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "退出登录失败")
    return http_return(200, "退出登录成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def wechat_login(request):
    """
    微信授权登录
    :param request:
    :return:
    """
    wxcode = request.data.get("wxcode", None)
    if not wxcode:
        return http_return(400, "请输入微信授权码")
    appType = request.data.get("appType", None)
    if not appType and appType not in ["web", "app"]:
        return http_return(400, "请选择登录平台")
    wxlogin = WxLogin(appType)
    baseInfo = wxlogin.get_access_token(wxcode)
    if not baseInfo:
        return http_return(400, "获取用户信息失败")
    access_token = baseInfo.get("access_token")
    openid = baseInfo.get("openid")
    unionid = baseInfo.get("unionid")
    if not all([access_token, openid, unionid]):
        return http_return(400, "微信获取信息缺失")
    wechat = WechatAuth.objects.filter(unionid=unionid, status=1).first()
    user = None
    if wechat:
        if not wechat.openid:
            try:
                wechat.openid = openid
                wechat.save()
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "存储openid失败")
        user = wechat.userUuid
    else:
        hbbUserData = get_user(unionid, "wechat")
        if hbbUserData:
            user = save_hbb_user(hbbUserData)
            if not user:
                return http_return(400, "数据迁移存储失败")
        else:
            check_res = wxlogin.check_token(access_token, openid)
            if not check_res:
                return http_return(400, "校验access_token失败")
            if check_res.get("errcode") != 0:
                refresh_res = wxlogin.refresh_token(baseInfo.get("refresh_token"))
                access_token = refresh_res.get("access_token")
            userInfo = wxlogin.get_user_info(access_token, openid)
            if not userInfo:
                return http_return(400, "获取用户信息失败")
            try:
                user = User.objects.create(
                    nickName=userInfo.get("nickname"),
                    registerPlatform=1,
                    gender=userInfo.get("sex"),
                    location=userInfo.get("province") + " " + userInfo.get("city"),
                    avatar=userInfo.get("headimgurl", DEFAULT_AVATAR),
                )
                WechatAuth.objects.create(
                    userUuid=user,
                    name=userInfo.get("nickname"),
                    sex=userInfo.get("sex"),
                    avatar=userInfo.get("headimgurl", DEFAULT_AVATAR),
                    province=userInfo.get("province"),
                    city=userInfo.get("city"),
                    openid=userInfo.get("openid"),
                    unionid=userInfo.get("unionid"),
                )
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "存储用户信息失败")
    if not save_access_token(openid, baseInfo):
        return http_return(400, "存储access_token失败")
    token = get_token()
    if not set_user_session(token, user, "WECHAT"):
        return http_return(400, "服务器缓存错误")
    if not save_login_log(user, request, "WECHAT"):
        return http_return(400, "存储登陆日志失败")
    return http_return(200, "登陆成功", login_return(user, token))


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def change_password(request):
    """
    修改密码
    :param request:
    :return:
    """
    tel = request.data.get("tel", None)
    if not tel:
        return http_return(400, "请输入手机号")
    password = request.data.get("password", None)
    if not password:
        return http_return(400, "请输入密码")
    if len(password) < 6 or len(password) > 16:
        return http_return(400, "密码长度错误")
    code = request.data.get("code", None)
    if not code:
        return http_return(400, "请输入验证码")
    checkTel = TelAuth.objects.filter(tel=tel, status=1).first()
    if not checkTel:
        return http_return(400, "该手机号未注册")
    if checkTel.userUuid.uuid != request.user.get("uuid"):
        return http_return(400, "手机号错误,请重新输入")
    sendCode = caches['client'].get(tel, None)
    if not sendCode:
        return http_return(400, "验证码已失效")
    if sendCode != code:
        return http_return(400, "验证码错误")
    try:
        caches['client'].delete(tel)
    except Exception as e:
        logging.error(str(e))
    try:
        checkTel.passwd = make_password(password)
        checkTel.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "修改失败")
    return http_return(200, "修改成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def change_tel(request):
    """
    修改手机号
    :param request:
    :return:
    """
    tel = request.data.get("tel", None)
    if not tel:
        return http_return(400, "请输入手机号")
    code = request.data.get("code", None)
    if not code:
        return http_return(400, "请输入验证码")
    selfUuid = request.user.get("uuid")
    user = User.objects.filter(uuid=selfUuid).first()
    if not user.userTelUuid:
        return http_return(400, "未绑定手机号")
    sendCode = caches['client'].get(tel, None)
    if not sendCode:
        return http_return(400, "验证码已失效")
    if sendCode != code:
        return http_return(400, "验证码错误")
    try:
        caches['client'].delete(tel)
    except Exception as e:
        logging.error(str(e))
    checkTel = TelAuth.objects.filter(tel=tel).exclude(userUuid__uuid=selfUuid).first()
    if checkTel:
        return http_return(400, "手机号已注册")
    try:
        userTel = user.userTelUuid.first()
        userTel.tel = tel
        userTel.save()
        user.tel = tel
        user.nickName = tel
        user.save()
        user_info = {
            "uuid": selfUuid,
            "tel": tel,
            "loginType": request.user.get("loginType"),
        }
        caches['client'].set(request.auth, user_info, TOKEN_TIMEOUT)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "更换失败")
    return http_return(200, "更换成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def change_info(request):
    """
    修改个人信息
    :param request:
    :return:
    """
    nickName = request.data.get("nickName", None)
    email = request.data.get("email", None)
    realName = request.data.get("realName", None)
    gender = request.data.get("gender", None)
    birthday = request.data.get("birthday", None)
    avatar = request.data.get("avatar", None)
    intro = request.data.get("intro", None)
    update_data = {}
    if nickName:
        checkName = User.objects.filter(nickName=nickName).first()
        if not checkName:
            return http_return(400, "用户名已存在")
        update_data["nickName"] = nickName
    if email:
        update_data["email"] = email
    if realName:
        update_data["realName"] = realName
    if gender:
        update_data["gender"] = gender
    if birthday:
        birthday = unix_time_to_datetime(int(birthday)).date()
        update_data["birthday"] = birthday
    if avatar:
        update_data["avatar"] = avatar
    if intro:
        update_data["intro"] = intro
    try:
        User.objects.filter(uuid=request.user.get("uuid")).update(**update_data)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "修改失败")
    return http_return(200, "修改成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def check_tel(request):
    """验证手机号"""
    code = request.data.get("code", None)
    if not code:
        return http_return(400, "请输入验证码")
    user = request.user.get("userObj")
    checkTel = user.userTelUuid.first() if user.userTelUuid else None
    if not checkTel:
        return http_return(400, "没有绑定手机号")
    sendCode = caches['client'].get(checkTel.tel, None)
    if not sendCode:
        return http_return(400, "验证码已失效")
    if sendCode != code:
        return http_return(400, "验证码错误")
    try:
        caches['client'].delete(checkTel.tel)
    except Exception as e:
        logging.error(str(e))
    try:
        caches['client'].set(checkTel.uuid, "OK", REALNAME_TIMEOUT)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "验证失败")
    return http_return(200, "验证成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def bind_real_info(request):
    """
    绑定身份证和设置交易密码
    :param request:
    :return:
    """
    user = request.user.get("userObj")
    checkTel = user.userTelUuid.first() if user.userTelUuid else None
    if not checkTel:
        return http_return(400, "没有绑定手机号")
    try:
        mark = caches['client'].get(checkTel.uuid, None)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "服务器缓存错误")
    if not mark or mark != "OK":
        return http_return(400, "手机号未验证")
    realName = request.data.get("realName", None)
    idCard = request.data.get("idCard", None)
    tradePwd = request.data.get("tradePwd", None)
    if not realName:
        return http_return(400, "请输入真实姓名")
    if not idCard:
        return http_return(400, "请输入身份证号")
    if not tradePwd:
        return http_return(400, "请输入交易密码")
    if len(tradePwd) != 6:
        return http_return(400, "交易密码长度必须为6位")
    if not is_valid_idcard(idCard):
        return http_return(400, '请填写正确身份证号码')
    try:
        User.objects.filter(uuid=request.user.get("uuid")).update(
            realName=realName,
            idCard=idCard,
            tradePwd=make_password(tradePwd),
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "设置失败")
    return http_return(200, "设置成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def query_tel(request):
    """
    查询手机号是否已存在
    :param request:
    :return:
    """
    tel = request.data.get("tel", None)
    if not tel:
        return http_return(400, "请输入手机号")
    checkTel = TelAuth.objects.filter(tel=tel, status=1).first()
    if checkTel:
        return http_return(200, "手机号已存在", {"exist": True})
    return http_return(200, "手机号不存在", {"exist": False})


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def bind_tel(request):
    """
    微信绑定手机号
    :param request:
    :return:
    """
    tel = request.data.get("tel", None)
    if not tel:
        return http_return(400, "请输入手机号")
    password = request.data.get("password", None)
    if not password:
        return http_return(400, "请输入密码")
    if len(password) < 6 or len(password) > 16:
        return http_return(400, "密码长度错误")
    code = request.data.get("code", None)
    if not code:
        return http_return(400, "请输入验证码")
    sendCode = caches['client'].get(tel, None)
    if not sendCode:
        return http_return(400, "验证码已失效")
    if sendCode != code:
        return http_return(400, "验证码错误")
    try:
        caches['client'].delete(tel)
    except Exception as e:
        logging.error(str(e))
    user = User.objects.filter(uuid=request.user.get("uuid")).first()
    if user.userTelUuid.first():
        return http_return(400, "你已绑定手机号，不能重复绑定")
    checkTel = TelAuth.objects.filter(tel=tel, status=1).first()
    if checkTel:
        # 账号合并逻辑实现
        if checkTel.userUuid.userWechatUuid.first():
            return http_return(400, "该手机号已绑定其他微信，不能绑定")
        if not wechat_bind_tel(checkTel, user):
            return http_return(400, "绑定失败")
    else:
        try:
            TelAuth.objects.create(
                userUuid=user,
                tel=tel,
                passwd=make_password(password),
                userSource=2,
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "绑定失败")
    return http_return(200, "绑定成功")


@api_view(["POST"])
@permission_classes([])
@authentication_classes([ClientAuthentication])
def bind_wechat(request):
    """
    绑定微信
    :param request:
    :return:
    """
    wxcode = request.data.get("wxcode", None)
    if not wxcode:
        return http_return(400, "请输入微信授权码")
    appType = request.data.get("appType", None)
    if not appType and appType not in ["web", "app"]:
        return http_return(400, "请选择登录平台")
    user = User.objects.filter(uuid=request.user.get("uuid")).first()
    if user.userWechatUuid.first() and user.userWechatUuid.first().status == 1:
        return http_return(400, "你已绑定过微信号")
    wxlogin = WxLogin(appType)
    baseInfo = wxlogin.get_access_token(wxcode)
    if not baseInfo:
        return http_return(400, "获取用户信息失败")
    access_token = baseInfo.get("access_token")
    openid = baseInfo.get("openid")
    unionid = baseInfo.get("unionid")
    if not all([access_token, openid, unionid]):
        return http_return(400, "微信获取信息缺失")
    wechat = WechatAuth.objects.filter(unionid=unionid, status=1).first()
    if wechat:
        # 执行手机号绑定微信逻辑
        if wechat.userUuid.userTelUuid.first():
            return http_return(400, "该微信号已绑定其他账号，不能绑定")
        if not tel_bind_wechat(wechat, user):
            return http_return(400, "绑定失败")
    else:
        check_res = wxlogin.check_token(access_token, openid)
        if not check_res:
            return http_return(400, "校验access_token失败")
        if check_res.get("errcode") != 0:
            refresh_res = wxlogin.refresh_token(baseInfo.get("refresh_token"))
            access_token = refresh_res.get("access_token")
        userInfo = wxlogin.get_user_info(access_token, openid)
        if not userInfo:
            return http_return(400, "获取用户信息失败")
        try:
            WechatAuth.objects.create(
                userUuid=user,
                name=userInfo.get("nickname"),
                sex=userInfo.get("sex"),
                avatar=userInfo.get("headimgurl"),
                province=userInfo.get("province"),
                city=userInfo.get("city"),
                openid=openid,
                unionid=unionid,
            )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "绑定失败")
    return http_return(200, "绑定成功")


class UserInfo(APIView):
    """用户详情"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        return Response(UserSerializer(user, many=False).data)


class ChangeTradePwd(APIView):
    """修改交易密码"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def post(self, request):
        user = User.objects.filter(uuid=request.user.get("uuid")).first()
        checkTel = user.userTelUuid.first() if user.userTelUuid else None
        if not checkTel:
            return http_return(400, "没有绑定手机号")
        try:
            mark = caches['client'].get(checkTel.uuid, None)
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "服务器缓存错误")
        if not mark or mark != "OK":
            return http_return(400, "手机号未验证")
        if not all([user.realName, user.idCard, user.tradePwd]):
            return http_return(400, "未设置交易密码")
        tradePwd = request.data.get("tradePwd", None)
        if not tradePwd or len(str(tradePwd)) != 6:
            return http_return(400, "密码长度错误")
        try:
            user.tradePwd = make_password(tradePwd)
            user.save()
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "重设失败")
        return http_return(200, "重设成功")


class GetJsSdk(APIView):
    """获取js sdk配置参数"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        url = request.query_params.get("url", None)
        if not url:
            return http_return(400, "请传入当前域名")
        js_data = caches['client'].get(url, None)
        if not js_data:
            js_ticket = caches['client'].get("jsapi_ticket", None)
            if not js_ticket:
                jsapi = JsSdk()
                js_token = caches['client'].get("js_token", None)
                if not js_token:
                    js_token = jsapi.get_access_token()
                    if not js_token:
                        return http_return(400, "获取js_token失败")
                    try:
                        caches['client'].set("js_token", js_token, 1 * 60 * 60)
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, "服务器缓存错误")
                js_ticket = jsapi.get_jsapi_ticket(js_token)
                if not js_ticket:
                    return http_return(400, "获取js_ticket失败")
                try:
                    caches['client'].set("js_ticket", js_ticket, 1 * 60 * 60)
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, "服务器缓存错误")
            js_data = get_res_data(js_ticket, url)
            try:
                caches['client'].set(url, js_data, 1 * 60 * 60)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "服务器缓存错误")
        return Response(js_data)


class GetFileInfo(APIView):
    """文件转码"""
    authentication_classes = [ClientAuthentication]
    permission_classes = [ClientPermission]

    def get(self, request):
        fileId = request.query_params.get("serverId", None)
        if not fileId:
            return http_return(400, "请选择要获取的文件")
        fileServer = GetWechatFile()
        js_token = caches['client'].get("js_token", None)
        if not js_token:
            js_token = fileServer.get_access_token()
            if not js_token:
                return http_return(400, "获取js_token失败")
            try:
                caches['client'].set("js_token", js_token, 2 * 60 * 60)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "服务器缓存错误")
        toolDir = os.path.join(BASE_DIR, 'fileTools')
        file_from = os.path.join(toolDir, get_token() + ".amr")
        file_target = os.path.join(toolDir, get_token() + ".mp3")
        try:
            if not fileServer.get_file(js_token, fileId, file_from):
                return http_return(400, "下载文件失败")
            if not fileServer.transformat_voice(file_from, file_target):
                return http_return(400, "文件转码失败")
            resInfo = fileServer.put_file(file_target)
            if resInfo["code"] != 200:
                return http_return(400, "文件上传失败")
            url = resInfo["data"]["url"]
        finally:
            delete_file([file_from, file_target])
        return http_return(200, "文件下载成功", {"url": url})

