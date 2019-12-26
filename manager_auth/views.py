import logging

from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import caches

# Create your views here.
from django.db import transaction
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle, AnonRateThrottle
from rest_framework.views import APIView

from client.clientCommon import match_tel, random_string, get_token
from client.models import LoginLog
from client.ssoSMS.sms import send_sms
from common.models import User, Role, TelAuth, Permissions, Tags
from manager_auth.init_data import init_permissions, init_roles, init_role_permission, init_tags
from parentscourse_server.config import IS_SEND, TEL_IDENTIFY_CODE, TEST_CODE, ADMIN_TOKEN_TIMEOUT, DEFAULT_AVATAR
from utils.errors import ParamError
from utils.funcTools import http_return


def checkToken(token):
    if caches['default'].get(token):
        return True
    return False


def save_login_log(user, request, loginType):
    """存储登陆日志"""
    IP = request.META.get("HTTP_X_FORWARDED_FOR")
    try:
        LoginLog.objects.create(
            userUuid=user,
            ipAddr=IP if IP else None,
            loginType=loginType,
        )
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def getAndCheckTel(request):
    tel = request.data.get("tel", None)
    if not tel:
        return False, "请输入手机号", ''
    if not match_tel(tel):
        return False, "手机号格式不正确", ''
    return True, "OK", tel


def getAndCheckPassword(request):
    password = request.data.get("password", None)
    if not password:
        return False, "请输入密码", ""
    if len(password) < 6 or len(password) > 16:
        return False, "密码长度错误", ""
    return True, "OK", password


def getAndCheckCode(request):
    code = request.data.get("code", None)
    if not code:
        return False, "请输入验证码", ""
    if len(code) != 6:
        return False, "验证码错误", ""
    return True, "OK", code


def set_admin_session(token, user):
    """缓存管理员token和用户信息"""
    try:
        user_info = {
            "uuid": user.uuid,
            "tel": user.tel
        }
        caches['default'].set(token, user_info, ADMIN_TOKEN_TIMEOUT)
    except Exception as e:
        logging.error(str(e))
        return False
    # 重新登录老token失效
    old_token = caches['default'].get(user.uuid)
    if old_token:
        caches['default'].delete(old_token)
    caches['default'].set(user.uuid, token, ADMIN_TOKEN_TIMEOUT)
    return True


@api_view(["POST"])
def sendCode(request):
    """发送验证码"""
    res, msg, tel = getAndCheckTel(request)
    if not res:
        return http_return(400, msg)

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
            caches['default'].set(tel, my_random, TEL_IDENTIFY_CODE)
        except Exception as e:
            logging.error(str(e))
            return http_return(400, "服务器redis连接失败")
        return http_return(200, '短信已发送')
    else:
        return http_return(400, '短信发送失败')


class SendSMS(APIView):
    throttle_scope = "sms"

    def post(self, request):
        res, msg, tel = getAndCheckTel(request)
        if not res:
            return http_return(400, msg)

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
                caches['default'].set(tel, my_random, TEL_IDENTIFY_CODE)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, "服务器redis连接失败")
            return http_return(200, '短信已发送')
        else:
            return http_return(400, '短信发送失败')


@api_view(["POST"])
def register(request):
    """ 初始化管理员 """
    # if User.objects.filter(managerStatus=1).exists():
    #     return http_return(400, "已经初始化管理员")
    # 初始化数据库基础数据


    res, msg, tel = getAndCheckTel(request)
    if not res:
        return http_return(400, msg)

    res, msg, code = getAndCheckCode(request)
    if not res:
        return http_return(400, msg)

    res, msg, password = getAndCheckPassword(request)
    if not res:
        return http_return(400, msg)

    if caches['default'].get(tel, TEST_CODE) != code:
        return http_return(400, "验证码错误")

    nickName = request.data.get("nickName", None)
    if not nickName:
        return http_return(400, "请输昵称")
    if not 1 < len(nickName) < 14:
        return http_return(400, "昵称长度错误")

    if User.objects.filter(nickName=nickName).exists():
        return http_return(400, "昵称已存在")

    # 登录过的新用户
    checkUser = User.objects.filter(tel=tel).first()
    if checkUser:
        checkUser.managerStatus = 1
        checkUser.userRoles = 1
        # checkUser.userSource = 3
        msg = "该用户在新客户端已存在，请使用的是客户端密码登录"
        # 如果要初始化老用户为管理员，则需要改变密码
        if not checkUser.passwd:
            msg = "添加管理员成功，原客户端密码已更新设置的密码"
            checkUser.passwd = make_password(password)
            TelAuth.objects.create(
                userUuid=checkUser,
                tel=tel,
                passwd=checkUser.passwd,
                userSource=4,
            )
        token = get_token()
        checkUser.save()
        # 给用户添加角色
        role = Role.objects.filter(name="管理员").first()
        checkUser.roles.add(role)
        if not set_admin_session(token, checkUser):
            return http_return(400, "服务器缓存错误")
        return http_return(200, msg, {"token": token})

    # 初始化基础数据
    if Role.objects.all().exists():
        raise ParamError("数据库role表有数据，请清空再试！")

    if Permissions.objects.all().exists():
        raise ParamError("数据库role表有数据，请清空再试！")

    if Tags.objects.all().exists():
        raise ParamError("数据库tag表有数据，请清空再试！")

    try:
        with transaction.atomic():
            init_permissions()
            init_roles()
            init_role_permission()
            init_tags()
            password = make_password(password)
            user = User.objects.create(
                tel=tel,
                nickName=nickName,
                managerStatus=1,
                userRoles=1,
                avatar=DEFAULT_AVATAR,
                registerPlatform=5,
                # userSource=4,
                passwd=password,
            )
            TelAuth.objects.create(
                userUuid=user,
                tel=tel,
                passwd=password,
                userSource=4,
            )
            role = Role.objects.filter(name="管理员").first()
            user.roles.add(role)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "注册失败")
    token = get_token()
    if not set_admin_session(token, user):
        return http_return(400, "服务器缓存错误")
    return http_return(200, "注册新管理员成功", {"token": token})


# 密码登录
def loginByPwd(tel, password, request):
    checkSource = User.objects.filter(tel=tel, managerStatus=1).first()
    if checkSource:
        if not check_password(password, checkSource.passwd):
            return False, "手机号或密码错误", None
        else:
            token = get_token()
            if not set_admin_session(token, checkSource):
                return False, "服务器缓存错误", None
            if not save_login_log(checkSource, request, "ADMINPWD"):
                return False, "存储登陆日志失败"
            return True, "登陆成功", token
    return False, "无此管理员", None


# 手机验证码登录
def loginByPhone(tel, code, request):
    checkUser = User.objects.filter(tel=tel, managerStatus=1).first()
    if not checkUser:
        return False, "无此管理员", None
    if caches['default'].get(tel, TEST_CODE) != code:
        return False, "验证码错误", None
    # 验证码使用后作废
    caches['default'].delete(tel)
    token = get_token()
    if not set_admin_session(token, checkUser):
        return False,  "服务器缓存错误", None
    if not save_login_log(checkUser, request, "ADMINPHONE"):
        return False, "存储登陆日志失败", None
    return True, "登陆成功", token


@api_view(["POST"])
def login(request):
    """登录"""
    loginType = request.data.get("loginType", None)
    if loginType not in ["pwd", "phone"]:
        return http_return(400, "请传登录方式")

    res, msg, tel = getAndCheckTel(request)
    if not res:
        return http_return(400, msg)

    checkUser = User.objects.filter(tel=tel, managerStatus=1).first()
    if not checkUser:
        return http_return(400, "无此管理员")
    data = {
        "nickName": checkUser.nickName,
        "avatar": checkUser.avatar or "https://hbb-ads.oss-cn-beijing.aliyuncs.com/file4142825175948.jpg",
        "uuid": checkUser.uuid,
        "tel": checkUser.tel,
        "managerStatus": checkUser.managerStatus
    }

    if loginType == "pwd":
        res, msg, password = getAndCheckPassword(request)
        if not res:
            return http_return(400, msg)

        res, msg, token = loginByPwd(tel, password, request)
        if not res:
            return http_return(400, msg)
        data['token'] = token
        return http_return(200, msg, data)

    if loginType == "phone":  # 手机验证码登录
        res, msg, code = getAndCheckCode(request)
        if not res:
            return http_return(400, msg)

        res, msg, token = loginByPhone(tel, code, request)
        if not res:
            return http_return(400, msg)
        data['token'] = token
        return http_return(200, msg, data)


@api_view(["POST"])
def logout(request):
    """退出登录"""
    try:
        caches['default'].delete(request.auth)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "退出登录失败")
    return http_return(200, "退出登录成功")


@api_view(["POST"])
def modifyPassword(request):
    """修改自己的密码"""
    password = request.data.get("password", None)
    newPassword = request.data.get("newPassword", None)
    if not all([password, newPassword]):
        return http_return(400, "不能为空")
    if not 6 <= len(newPassword) <= 16:
        return http_return(400, "密码长度错误")

    if not check_password(password,  request.user.passwd):
        return http_return(400, "原始密码错误")

    request.user.passwd = make_password(newPassword)
    request.user.save()
    telAuth = TelAuth.objects.filter(userUuid=request.user).first()
    if telAuth:
        telAuth.passwd = request.user.passwd
        telAuth.save()
    try:
        # 清除原来的缓冲
        caches['default'].delete(request.auth)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "修改密码失败")
    return http_return(200, "修改密码成功")


# 重设密码
@api_view(["POST"])
def resetPassword(request):
    """ 忘记密码"""
    # if User.objects.filter(managerStatus=1).exists():
    #     return http_return(400, "已经初始化管理")
    res, msg, tel = getAndCheckTel(request)
    if not res:
        return http_return(400, msg)

    res, msg, password = getAndCheckPassword(request)
    if not res:
        return http_return(400, msg)

    res, msg, code = getAndCheckCode(request)
    if not res:
        return http_return(400, msg)

    checkUser = User.objects.filter(tel=tel, managerStatus=1).first()
    if not checkUser:
        return http_return(400, "无此管理员信息")

    if caches['default'].get(tel, TEST_CODE) != code:
        return http_return(400, "验证码错误")

    # 验证码已使用，删除验证码
    caches['default'].delete(tel)
    checkUser.passwd=make_password(password)
    checkUser.save()

    telAuth = TelAuth.objects.filter(userUuid=checkUser).first()
    if telAuth:
        telAuth.passwd = checkUser.passwd
        telAuth.save()


    token = get_token()
    if not set_admin_session(token, checkUser):
        return http_return(400, "服务器缓存错误")
    try:
        # 清除原来的缓冲
        caches['default'].delete(request.auth)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, "重置密码失败")
    return http_return(200, "重置密码成功", {"token": token})


@api_view(["POST"])
def initAdmin(request):
    # initAdmin 1 不显示初始化页面  2 显示初始化页面
    if not caches['default'].get("initAdmin") == 1:
        if User.objects.filter(managerStatus=1, tel__isnull=False).exists():
            caches['default'].set("initAdmin", 1, 60*60*24)
            return http_return(200, "OK", {"initAdmin": 1})
        else:
            return http_return(200, "OK", {"initAdmin": 2})
    return http_return(200, "OK", {"initAdmin": 1})



