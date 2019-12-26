from rest_framework.authentication import BaseAuthentication
import logging

from django.core.cache import caches
from rest_framework.exceptions import AuthenticationFailed


class ClientAuthentication(BaseAuthentication):

    def authenticate(self, request):
        # if request.method in ["POST","PUT","DELETE"]:
        #     # 如果请求是post,put,delete三种类型时
        #     # 获取随用户请求发来的token随机码
        #     token = request.data.get("token")
        #     # 然后去数据库查询有没有这个token
        #     token_obj = models.Token.objects.filter(token=token).first()
        #     if token_obj:
        #         # 如果存在，则说明验证通过,以元组形式返回用户对象和token
        #         return token_obj.user,token
        #     else:
        #         # 不存在就直接抛错
        #         raise AuthenticationFailed("无效的token")
        # else:
        # # 这一步的else 是为了当用户是get请求时也可获取数据，并不需要验证token.
        #     return None,None
        token = request.META.get('HTTP_TOKEN', None)
        if not token:
            raise AuthenticationFailed("请登录后继续访问")
        try:
            user = caches['client'].get(token)
        except Exception as e:
            logging.error(str(e))
            raise AuthenticationFailed("服务器缓存错误")
        if not user:
            raise AuthenticationFailed("登录失效，请重新登录")
        return user, token