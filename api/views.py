# 标准库
import uuid
import hashlib

# django
from api import models
from django.db import IntegrityError
from django.db.models import F
# drf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
# drf-spectacular
from drf_spectacular.utils import extend_schema

# 认证组件
from ext.auth import BlogAuthentication, ForceLoginAuthentication
# 序列化器
from api.serializers import (
    BlogSerializer,
    BlogDetailSerializer,
    CommentSerializer,
    RegisterSerializer,
    LoginSerializer,
    FavorSerializer,
)


# post接口装饰器
# 返回内容不是序列化器的字段，就要手写extend_schema()
def auto_schema(serializer_cls, desc=""):
    return extend_schema(
        request=serializer_cls,
        responses={200: None},
        description=desc
    )


# 统一响应函数
def api_response(code, data=None, msg=None, error=None, detail=None, errors=None):
    ret = {"code": code}
    if data is not None:
        ret["data"] = data
    if msg:
        ret["msg"] = msg
    if error:
        ret["error"] = error
    if detail:
        ret["detail"] = detail
    if errors:
        ret["errors"] = errors
    return Response(ret)


# 博客列表分页配置
class BlogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 50


# 博客列表视图
class BlogView(APIView):
    authentication_classes = (BlogAuthentication,)

    # BlogPagination赋值
    pagination_class = BlogPagination

    def get(self, request, *args, **kwargs):
        """博客列表"""
        # 读取数据库中的博客信息,根据id倒叙排
        queryset = models.Blog.objects.all().order_by('-id')

        # BlogPagination实例化
        paginator = self.pagination_class()

        # 调用paginate_queryset(数据,请求)方法 得到page对象
        page_obj = paginator.paginate_queryset(queryset, request)

        # 序列化
        ser = BlogSerializer(instance=page_obj, many=True)
        # 返回
        return api_response(200, data={
            "list": ser.data,
            "total": paginator.page.paginator.count,
            "page": paginator.page.number
        })

    @auto_schema(BlogSerializer, desc="新建博客")
    def post(self, request, *args, **kwargs):
        """新建博客"""
        if not request.user:
            return api_response(400, error="认证失败")
        ser = BlogSerializer(data=request.data)
        if not ser.is_valid():
            return api_response(400, error="校验失败", errors=ser.errors)
        ser.save(creator=request.user)
        return api_response(200, data=ser.data)


# 博客详情视图
class BlogDetailView(APIView):
    def get(self, request, *args, **kwargs):
        """博客详情"""
        # 获取id
        pk = kwargs.get('pk')

        # 根据pk读取数据库中的博客信息
        instance = models.Blog.objects.filter(id=pk).first()

        # 判断数据存不存在
        if not instance:
            # 返回
            return api_response(404, error="数据不存在")

        # 序列化
        ser = BlogDetailSerializer(instance=instance, many=False)

        # 返回
        return api_response(200, data=ser.data)


# 评论列表分页配置
class CommentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 50


# 评论列表视图
class CommentView(APIView):
    authentication_classes = (BlogAuthentication,)
    pagination_class = CommentPagination

    def get(self, request, blog_id):
        """评论列表"""
        # 获取id,按最新时间排序
        queryset = models.Comment.objects.filter(blog_id=blog_id).order_by("-create_datetime")
        paginator = self.pagination_class()
        page_obj = paginator.paginate_queryset(queryset, request)
        # 序列化
        ser = CommentSerializer(instance=page_obj, many=True)

        # 返回
        return api_response(200, data={
            "data": ser.data,
            "total": paginator.page.paginator.count,
            "page": paginator.page.number
        })

    @auto_schema(CommentSerializer, desc="发表评论")
    def post(self, request, blog_id):
        """发表评论"""
        # 登录验证
        if not request.user:
            return api_response(400, error="没登录")

        # 博客是否存在
        blog_object = models.Blog.objects.filter(id=blog_id).first()
        if not blog_object:
            return api_response(404, error="博客不存在")

        # 输入参数验证
        ser = CommentSerializer(data=request.data)
        if not ser.is_valid():
            return api_response(400, error="参数校验失败", detail=ser.errors)

        ser.save(blog=blog_object, user=request.user)
        return api_response(200, data=ser.data)


# 注册视图
class RegisterView(APIView):

    @auto_schema(RegisterSerializer, desc="用户注册接口")
    def post(self, request):
        # 校验
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            # 极端情况 并发同时注册同一个用户名
            try:
                ser.validated_data.pop('confirm_password')
                ser.save()
                return api_response(200, data=ser.data)
            except IntegrityError:
                return api_response(400, error="用户名已被占用")
        else:
            return api_response(400, error="注册失败", detail=ser.errors)


# 登录视图
class LoginView(APIView):
    @auto_schema(LoginSerializer, desc="用户登录，获取token")
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        # 数据格式校验
        if not ser.is_valid():
            # print(ser.errors)
            return api_response(400, error="校验失败")
        username = ser.validated_data['username']
        raw_pwd = ser.validated_data['password']
        md5_pwd = hashlib.md5(raw_pwd.encode('utf-8')).hexdigest()
        # 数据校验,数据库查看数据存在不存在
        instance = models.UserInfo.objects.filter(username=username, password=md5_pwd).first()
        if not instance:
            return api_response(400, error="用户名或密码错误")

        # 清空旧token
        instance.token = None
        instance.save()

        # 创建token存入userinfo数据库
        token = str(uuid.uuid4())
        instance.token = token
        instance.save()

        # 返回
        return api_response(200, data={"token": token})


# 点赞视图
class FavorView(APIView):
    authentication_classes = (BlogAuthentication, ForceLoginAuthentication)

    @auto_schema(FavorSerializer, desc="点赞/取消点赞，body传blog id")
    def post(self, request):
        ser = FavorSerializer(data=request.data)
        if not ser.is_valid():
            return api_response(400, error="校验失败", detail=ser.errors)
        # 判断点赞的博客是否存在
        blog_id = ser.validated_data['blog'].id
        blog_obj = models.Blog.objects.filter(id=blog_id).first()
        if not blog_obj:
            return api_response(404, error="博客不存在")
        # 判断是否已经点过赞了
        exists = models.Favor.objects.filter(user=request.user, **ser.validated_data).first()
        if exists:
            blog_object = exists.blog  # 先拿blog对象
            exists.delete()  # 再删除点赞记录
            # 点赞-1
            # F解决计数并发问题
            blog_object.favor_count = F("favor_count") - 1
            blog_object.save()
            blog_object.refresh_from_db()
            return api_response(200, msg="取消点赞成功")
        # 没有点过赞，进行点赞
        # 捕获并发冲突异常，如网络缓慢触发的快速点赞等
        try:
            # 返回这个序列化器对应的 Model 实例对象
            favor_obj = ser.save(user=request.user)
            blog_obj = favor_obj.blog
            blog_obj.favor_count = F("favor_count") + 1
            blog_obj.save()
            blog_obj.refresh_from_db()
        except IntegrityError:
            return api_response(400, error="请勿重复点赞")
        return api_response(200, msg="点赞成功")
