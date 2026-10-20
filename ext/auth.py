from rest_framework.authentication import BaseAuthentication
from api import models
from rest_framework import exceptions

# 允许匿名用户
class BlogAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # 验证token
        token = request.query_params.get('token')
        if not token:
            return
        # 去数据库查看是否有这个用户
        instance = models.UserInfo.objects.filter(token=token).first()
        if not instance:
            return
        return instance, token

    def authenticate_header(self, request):
        return 'API'

# 必须登录认证
class ForceLoginAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raise exceptions.AuthenticationFailed({'code': 400, 'msg': '没有登录'})

    def authenticate_header(self, request):
        return 'API'
